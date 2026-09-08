import { renderArticle } from "$lib/server/articleRenderer";
import { recordArticleFetch } from "$lib/server/metrics";
import type { PageServerLoad } from "./$types";

/**
 * Render-race: we start the render, then wait up to EAGER_BUDGET_MS for it.
 *
 *  - If it resolves in time (the common case — L2 cache hits are sub-second),
 *    we return the FULL result eagerly, so the initial HTML contains the
 *    article body. External "save it" / reader apps and crawlers that grab
 *    the first response therefore get real content, not a skeleton.
 *  - If it doesn't (a genuinely cold render, 10–90 s through WARP), we fall
 *    back to streaming: the skeleton arrives instantly and the body streams
 *    in later. Humans never stare at a blank page.
 *
 * Popular articles (the ones people save) are almost always cached, so they
 * win the race → full HTML. Content-based, no bot-UA guessing.
 */
const EAGER_BUDGET_MS = 2500;

function getUnsupportedSiteInfo(urlStr: string): { message: string } | null {
	const normalized = urlStr.replace(/^(https?):\/+(?!\/)/i, "$1://");
	const withScheme = normalized.includes("://") ? normalized : `https://${normalized}`;
	try {
		const host = new URL(withScheme).hostname.toLowerCase().replace(/^www\./, "");
		if (host === "wsj.com" || host.endsWith(".wsj.com")) {
			return { message: "The Wall Street Journal is not supported by Freedium." };
		}
		if (host === "substack.com" || host.endsWith(".substack.com")) {
			return { message: "Substack is not supported by Freedium." };
		}
		if (host === "wired.com" || host.endsWith(".wired.com")) {
			return { message: "Wired is not supported by Freedium." };
		}
	} catch {
		return null;
	}
	return null;
}

export const load: PageServerLoad = async ({ params, request }) => {
	const unsupported = getUnsupportedSiteInfo(params.slug);
	if (unsupported) {
		recordArticleFetch("unsupported");
		return {
			slug: params.slug,
			eager: {
				html: null,
				markdown: null,
				article: null,
				cacheStatus: "miss",
				renderTimeMs: 0,
				error: {
					status: 400,
					message: unsupported.message,
					code: "UNSUPPORTED_SITE",
				},
			},
			streamed: null,
		};
	}

	const start = performance.now();
	const clientUa = request.headers.get("User-Agent") ?? "";

	// This promise never rejects — the .catch below maps every failure to a
	// uniform result shape (with an `error` field).
	const renderPromise = renderArticle(params.slug, { clientUa }).then((result) => {
		const renderTimeMs = Math.round(performance.now() - start);
		recordArticleFetch("success");
		return {
			html: result.html,
			markdown: result.markdown,
			article: result.article,
			cacheStatus: result.cacheStatus,
			renderTimeMs,
			error: null as { status: number; message: string; code?: string; details?: string } | null,
		};
	}).catch((err: unknown) => {
		const message = (err as Error)?.message ?? "";
		// A backend 404 (post not found, OR a transient WARP soft-block that
		// exhausted retries) should surface as 404 with the branded
		// not-found card — not a scary 500.
		if (message === "ARTICLE_NOT_FOUND" || message === "UPSTREAM_404") {
			recordArticleFetch("not_found");
			return {
				html: null as string | null,
				markdown: null as string | null,
				article: null as import("$lib/types").ArticlePageData["article"] | null,
				cacheStatus: "miss" as string,
				renderTimeMs: Math.round(performance.now() - start),
				error: {
					status: 404,
					message: "Article not found",
					code: "ARTICLE_NOT_FOUND",
				},
			};
		}
		if (message === "UPSTREAM_422") {
			recordArticleFetch("unsupported");
			const detail = (err as Error & { detail?: string })?.detail;
			const unsupportedInfo = getUnsupportedSiteInfo(params.slug);
			let customMsg =
				"This site isn’t supported. Freedium unlocks article paywalls — video, social, search, and shopping links aren’t articles.";
			if (detail && detail !== "unsupported_site") {
				customMsg = detail;
			} else if (unsupportedInfo) {
				customMsg = unsupportedInfo.message;
			}
			return {
				html: null as string | null,
				markdown: null as string | null,
				article: null as import("$lib/types").ArticlePageData["article"] | null,
				cacheStatus: "miss" as string,
				renderTimeMs: Math.round(performance.now() - start),
				error: {
					status: 400,
					message: customMsg,
					code: "UNSUPPORTED_SITE",
				},
			};
		}
		console.error("Failed to render article:", err);
		recordArticleFetch(
			message.startsWith("UPSTREAM_") ? "upstream_error" : "network_fail",
		);
		return {
			html: null,
			markdown: null,
			article: null,
			cacheStatus: "miss",
			renderTimeMs: Math.round(performance.now() - start),
			error: {
				status: 500,
				message: "Failed to render article",
				code: "RENDER_ERROR",
				details: import.meta.env.DEV ? (err as Error).message : undefined,
			},
		};
	});

	// Race the render against the eager budget.
	const TIMED_OUT = Symbol("timed-out");
	const winner = await Promise.race([
		renderPromise,
		new Promise<typeof TIMED_OUT>((resolve) =>
			setTimeout(() => resolve(TIMED_OUT), EAGER_BUDGET_MS).unref?.(),
		),
	]);

	if (winner !== TIMED_OUT) {
		// Fast (cache hit / quick render) → full HTML in the initial response.
		return { slug: params.slug, eager: winner, streamed: null };
	}
	// Cold → stream the skeleton, body arrives when renderPromise resolves.
	return { slug: params.slug, eager: null, streamed: renderPromise };
};
