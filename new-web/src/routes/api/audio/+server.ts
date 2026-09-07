import { error } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";

/**
 * Audio proxy for podcast episodes and audio embeds.
 *
 * Why this is needed:
 * Major podcast providers (e.g. Bloomberg Odd Lots on Omny/Triton/Podtrac) route
 * through multiple cross-origin analytics/tracking redirects (podtrac.com,
 * tracking.swap.fm, traffic.omny.fm).
 *
 * Privacy blockers (Brave Shields, Firefox Enhanced Tracking Protection, uBlock)
 * block these third-party tracker domains by default, causing NS_BINDING_ABORTED
 * errors and preventing the audio player from loading.
 *
 * This endpoint serves the audio as a same-origin resource on Freedium, following
 * the redirects server-side while supporting HTTP Range requests for seamless
 * seeking and scrubbing in native browser <audio> players.
 */

const ALLOWED_AUDIO_HOSTS =
	/(^|\.)(podtrac\.com|omny\.fm|tritondigital\.com|swap\.fm|bloomberg\.com|bwbx\.io|nyt\.com|nytimes\.com|arcpublishing\.com|washingtonpost\.com|reuters\.com)$/i;

const MAX_REDIRECTS = 6;

function assertAllowedAudioUrl(u: string): URL {
	let parsed: URL;
	try {
		parsed = new URL(u);
	} catch {
		throw error(400, "Invalid audio URL");
	}
	if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
		throw error(400, "Invalid audio protocol");
	}
	if (!ALLOWED_AUDIO_HOSTS.test(parsed.hostname)) {
		throw error(400, "Audio host not permitted");
	}
	return parsed;
}

export const GET: RequestHandler = async ({ url, request }) => {
	const targetUrl = url.searchParams.get("url");
	if (!targetUrl) {
		throw error(400, "Missing audio url parameter");
	}

	const range = request.headers.get("range");
	const headers: Record<string, string> = {
		"user-agent": "Freedium Audio Proxy/1.0",
	};
	if (range) {
		headers["range"] = range;
	}

	let currentUrl = targetUrl;
	let upstream: Response | null = null;

	for (let hop = 0; hop <= MAX_REDIRECTS; hop++) {
		assertAllowedAudioUrl(currentUrl);
		let res: Response;
		try {
			res = await fetch(currentUrl, {
				headers,
				redirect: "manual",
				signal: AbortSignal.timeout(60_000),
			});
		} catch (err: unknown) {
			throw error(502, `Failed to reach audio stream: ${(err as Error).message}`);
		}

		if (res.status >= 300 && res.status < 400) {
			const loc = res.headers.get("location");
			if (!loc) throw error(502, "Audio redirect without Location header");
			currentUrl = new URL(loc, currentUrl).toString();
			continue;
		}

		upstream = res;
		break;
	}

	if (!upstream) {
		throw error(502, "Too many audio redirects");
	}

	if (!upstream.ok && upstream.status !== 206) {
		throw error(upstream.status, `Upstream audio error ${upstream.status}`);
	}

	const responseHeaders = new Headers();
	for (const key of ["content-type", "content-length", "content-range", "accept-ranges"]) {
		const val = upstream.headers.get(key);
		if (val) responseHeaders.set(key, val);
	}
	responseHeaders.set("cache-control", "public, max-age=86400");

	return new Response(upstream.body, {
		status: upstream.status,
		headers: responseHeaders,
	});
};
