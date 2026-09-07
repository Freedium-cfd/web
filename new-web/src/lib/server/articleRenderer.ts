import { render } from "@/services";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import rehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import rehypeStringify from "rehype-stringify";
import { createHighlighter, type HighlighterGeneric, type BundledLanguage, type BundledTheme } from "shiki";
import { visit } from "unist-util-visit";
import { toHtml } from "hast-util-to-html";
import { h, s } from "hastscript";
import type { Element, Root } from "hast";
import { getIconData, iconToSVG } from "@iconify/utils";
import heroiconsData from "@iconify/json/json/heroicons.json";
import rehypeExternalLinks from "rehype-external-links";
import rehypeSlug from "rehype-slug";
import FrontMatter from "front-matter";

// Helper to get icon as HAST SVG node
function getIconHast(iconName: string, customAttrs: Record<string, string> = {}): Element | null {
	const iconData = getIconData(heroiconsData, iconName);
	if (!iconData) {
		console.warn(`Icon "${iconName}" not found in heroicons`);
		return null;
	}
	const renderData = iconToSVG(iconData, { height: "1em", width: "1em" });
	const attrs = {
		...renderData.attributes,
		...customAttrs,
		xmlns: "http://www.w3.org/2000/svg",
	};

	const svgElement = s("svg", attrs) as Element;
	// Inject raw SVG body content
	(svgElement.children as unknown[]).push({ type: "raw", value: renderData.body });
	return svgElement;
}

// Create external link icon
const externalLinkIcon = getIconHast("arrow-top-right-on-square", {
	class: "inline-block ml-0.5 size-3 align-baseline relative -top-px",
	stroke: "currentColor",
	fill: "none",
	"stroke-width": "2",
	"aria-hidden": "true",
});

// Load every bundled shiki language so Medium code blocks in ANY
// language (kotlin, markdown, java, css, etc.) don't crash the SSR.
import { bundledLanguages } from "shiki";

const HIGHLIGHT_CONFIG = {
	themes: ["github-light", "github-dark"],
	langs: Object.keys(bundledLanguages),
};

// Sanitize schema for the article body. Extends rehype-sanitize's default
// (GitHub) schema — which already strips <script>, on* event handlers, and
// dangerous URL protocols — to additionally permit the structural HTML
// Freedium legitimately emits in the markdown body (embed iframes, image
// data-attributes, ids/classes/styles). Attribute names use hast's camelCase
// property form (srcDoc, frameBorder, dataIframeId, …), not raw HTML names.
const FREEDIUM_SANITIZE_SCHEMA: typeof defaultSchema = (() => {
	const s = structuredClone(defaultSchema);
	// "mark" = Medium highlights (<mark class="bg-emerald-...">); not in the
	// default schema, so without this the highlight wrapper is stripped.
	// figure/figcaption: NYT image blocks + grids/diptychs wrap images in
	// <figure class="image-grid">…<figcaption>. Not in the default allowlist,
	// so without this sanitize unwraps them → images spill out loose + the
	// grid layout breaks.
	// audio/source: Bloomberg and other podcast/audio episode embeds.
	s.tagNames = [...new Set([...(s.tagNames ?? []), "iframe", "mark", "figure", "figcaption", "audio", "source"])];
	s.attributes = {
		...s.attributes,
		// Note: id/style intentionally NOT wildcard-allowed (DOM-clobbering /
		// CSS-exfil surface). Heading ids are added by rehypeSlug *after*
		// sanitize; shiki inline styles are injected after sanitize too.
		"*": [
			...(s.attributes?.["*"] ?? []),
			"className",
			"dataIframeId",
			"dataZoomSrc",
			"dataCaption",
			"dataNosnippet",
		],
		audio: [
			"src",
			"controls",
			"preload",
			"className",
		],
		source: [
			"src",
			"type",
		],
		iframe: [
			"src",
			"srcDoc",
			"sandbox",
			"width",
			"height",
			"style",
			"loading",
			"title",
			"allow",
			"frameBorder",
			"dataIframeId",
		],
		img: [
			...(s.attributes?.img ?? []),
			"dataZoomSrc",
			"dataCaption",
			"loading",
			"className",
		],
	};
	return s;
})();

const CODE_ATTRIBUTES: Record<string, string> = {
	contenteditable: "true",
	"aria-label": "code",
	"aria-readonly": "true",
	inputmode: "none",
	tabindex: "0",
	"aria-multiline": "true",
	"aria-haspopup": "false",
	"data-gramm": "false",
	"data-gramm_editor": "false",
	"data-enable-grammarly": "false",
	spellcheck: "false",
	autocorrect: "off",
	autocapitalize: "none",
	autocomplete: "off",
	"data-ms-editor": "false",
};

let highlighterInstance: HighlighterGeneric<BundledLanguage, BundledTheme> | null = null;

// TODO: are we optimizing shiki loading by making it a singleton?
// (Process-wide singleton currently holds every bundled language's grammar
//  in memory. Revisit whether that's the right trade-off vs. lazy per-lang
//  loading or a smaller curated language set.)
async function getHighlighter(): Promise<HighlighterGeneric<BundledLanguage, BundledTheme>> {
	if (!highlighterInstance) {
		highlighterInstance = await createHighlighter(HIGHLIGHT_CONFIG);
		await highlighterInstance.loadLanguage(...Object.keys(bundledLanguages));
	}
	return highlighterInstance;
}

/** codeToHtml wrapper that falls back to "text" for unsupported languages.
 * Medium articles can contain code blocks in any language — kotlin, java,
 * markdown, css, etc. — but we only pre-load a handful. This keeps the
 * render pipeline from crashing on unknown languages. */
function safeCodeToHtml(
	highlighter: HighlighterGeneric<BundledLanguage, BundledTheme>,
	code: string,
	lang: string,
	options: Record<string, unknown>,
): string {
	try {
		return highlighter.codeToHtml(code, { ...options, lang } as Parameters<typeof highlighter.codeToHtml>[1]);
	} catch (e) {
		if (e instanceof Error && (e.name === "ShikiError" || e.message?.includes("Language"))) {
			// Degrade gracefully rather than crashing the whole article render.
			// Two known ShikiError causes: an unsupported language, and
			// "Decorations … intersect" (Medium markup with overlapping
			// bold/italic ranges in a code block). Drop the decorations first
			// (keeps language highlighting), then fall back to plain "text".
			const { decorations: _dropped, ...noDecorations } = options;
			try {
				return highlighter.codeToHtml(code, { ...noDecorations, lang } as Parameters<typeof highlighter.codeToHtml>[1]);
			} catch {
				return highlighter.codeToHtml(code, { ...noDecorations, lang: "text" } as Parameters<typeof highlighter.codeToHtml>[1]);
			}
		}
		throw e;
	}
}

function createCodeCopyButton(code: string, toggleMs: number = 3000): string {
	const lineCount = code.split("\n").length;
	const positionClass = lineCount <= 3 ? "top-1/2 -translate-y-1/2" : "top-3";

	const clipboardIcon = getIconHast("clipboard-document", {
		class: "size-5",
		stroke: "currentColor",
		fill: "none",
		"stroke-width": "1.5"
	});

	const clipboardCheckIcon = getIconHast("clipboard-document-check-solid", {
		class: "size-5",
		fill: "currentColor"
	});

	const button = h(
		"button",
		{
			"data-code": code,
			"data-toggle-ms": toggleMs,
			"aria-label": "Copy code",
			// data-nosnippet: keep this control out of page-saver / reader-mode
			// extraction so it doesn't pollute the saved article text.
			"data-nosnippet": "",
			class: `code-copy-btn absolute right-3 ${positionClass} size-8 p-1.5 flex items-center justify-center bg-black/50 text-white rounded-md transition-colors duration-200 cursor-pointer hover:bg-black/70`,
		},
		[
			h("span", { class: "ready block", "aria-hidden": "true" }, clipboardIcon ? [clipboardIcon] : []),
			h("span", { class: "success hidden", "aria-hidden": "true" }, clipboardCheckIcon ? [clipboardCheckIcon] : []),
		],
	);

	return toHtml(button, { allowDangerousHtml: true });
}

// Rehype plugin for syntax highlighting
function rehypeHighlight(opts: { mode: RenderMode } = { mode: "web" }) {
	return async (tree: Root) => {
		const highlighter = await getHighlighter();
		const nodesToReplace: Array<{ node: any; parent: any; index: number; replacement: any }> = [];

		visit(tree, 'element', (node: any, index: number | null | undefined, parent: any) => {
			if (node.tagName === 'pre') {
				const codeNode = node.children?.[0];
				if (codeNode && codeNode.tagName === 'code') {
					const className = codeNode.properties?.className;
					const lang = className?.[0]?.replace('language-', '') || 'text';
					// Remove trailing newline that remark-parse adds to all code blocks
					const originalText = codeNode.children?.[0]?.value || '';
					const codeText = originalText.replace(/\n$/, '');


					// Check for decorations in code fence meta (e.g., ```lang decorations="[...]")
					const meta = codeNode.data?.meta || '';
					let decorations: Array<{ start: number; end: number; properties: any }> = [];

					// Match decorations with escaped quotes - need to find the closing quote
					const decorationsMatch = meta.match(/decorations="(.+)"$/);
					if (decorationsMatch) {
						try {
							// Unescape the JSON
							const jsonStr = decorationsMatch[1].replace(/\\"/g, '"');
							const decoData = JSON.parse(jsonStr);
							decorations = decoData.map((d: any) => ({
								// Clamp positions to code length to handle Medium's invalid markup positions
								start: Math.min(d.start, codeText.length),
								end: Math.min(d.end, codeText.length),
								properties: { class: d.type === 'strong' ? 'font-bold' : 'italic' }
							}))
							// Filter out invalid decorations where start >= end
							.filter((d: any) => d.start < d.end);

							// Shiki throws "Decorations … intersect" on overlapping
							// ranges — Medium's markup sometimes nests/overlaps
							// bold+italic. Keep them sorted and drop any that overlap
							// a previously-kept one so the render never crashes.
							decorations.sort((a, b) => a.start - b.start);
							const deconflicted: typeof decorations = [];
							let lastEnd = -1;
							for (const d of decorations) {
								if (d.start >= lastEnd) {
									deconflicted.push(d);
									lastEnd = d.end;
								}
							}
							decorations = deconflicted;
						} catch (e) {
							console.error('Failed to parse decorations:', e);
						}
					}


					// Generate highlighted HTML with decorations
					const lightHtml = safeCodeToHtml(highlighter, codeText, lang, {

						theme: "github-light",
						decorations,
						transformers: [
							{
								code(transformNode) {
									transformNode.properties = { ...transformNode.properties, ...CODE_ATTRIBUTES };
									return transformNode;
								},
							},
						],
					});

					let wrappedHtml: string;
					if (opts.mode === "print") {
						// Print: single theme, no dark variant, no copy button.
						wrappedHtml = lightHtml;
					} else {
						// Web: dual theme + copy button (existing behavior).
						const darkHtml = safeCodeToHtml(highlighter, codeText, lang, {
	
							theme: "github-dark",
							decorations,
							transformers: [
								{
									code(transformNode) {
										transformNode.properties = { ...transformNode.properties, ...CODE_ATTRIBUTES };
										return transformNode;
									},
								},
							],
						});

						const buttonHtml = createCodeCopyButton(codeText, 1200);

						// Create replacement HTML
						wrappedHtml = `
						<div class="relative">
							${buttonHtml}
							<div class="dark:hidden">${lightHtml}</div>
							<div class="hidden dark:block">${darkHtml}</div>
						</div>
					`;
					}

					// Create a raw HTML node
					const replacement = {
						type: 'raw',
						value: wrappedHtml
					};

					if (parent && typeof index === 'number') {
						nodesToReplace.push({ node, parent, index, replacement });
					}
				}
			}
		});

		// Replace nodes
		for (const { parent, index, replacement } of nodesToReplace) {
			parent.children[index] = replacement;
		}
	};
}

const YOUTUBE_PATTERNS = [
	/youtube\.com\/embed\/([A-Za-z0-9_-]{6,15})/,
	/youtube\.com\/watch\?v=([A-Za-z0-9_-]{6,15})/,
	/youtu\.be\/([A-Za-z0-9_-]{6,15})/,
];

function extractYouTubeId(src: string): string | null {
	for (const re of YOUTUBE_PATTERNS) {
		const m = src.match(re);
		if (m) return m[1];
	}
	return null;
}

function escapeHtml(s: string): string {
	return s
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

function buildIframeFallbackLink(src: string): string {
	try {
		const u = new URL(src);
		if (u.protocol !== "http:" && u.protocol !== "https:") {
			return `<a href="#">[Embed]</a>`;
		}
		return `<a href="${escapeHtml(src)}">[Embed: ${escapeHtml(u.hostname)}]</a>`;
	} catch {
		return `<a href="#">[Embed]</a>`;
	}
}

function transformIframeHtml(iframeHtml: string): string {
	const srcMatch = iframeHtml.match(/\bsrc\s*=\s*["']([^"']+)["']/i);
	if (!srcMatch) return iframeHtml;
	const src = srcMatch[1];

	const ytId = extractYouTubeId(src);
	if (ytId) {
		return (
			`<a class="yt-link" href="https://www.youtube.com/watch?v=${ytId}">` +
			`<img class="yt-thumb" src="https://img.youtube.com/vi/${ytId}/maxresdefault.jpg" alt="YouTube video"/>` +
			`<span class="yt-play">▶</span>` +
			`</a>`
		);
	}

	return buildIframeFallbackLink(src);
}

/** Force sandbox="allow-same-origin" on every iframe (runs AFTER sanitize so
 * it's authoritative — an attacker can't pre-set allow-scripts in markdown).
 * allow-same-origin (NOT allow-scripts) lets the parent inject dark-theme CSS
 * into the srcdoc document (iframeTheme.ts) while preventing any <script>
 * inside a malicious srcdoc from executing. Closes the srcdoc XSS vector that
 * allowlisting srcDoc would otherwise open. */
function rehypeSandboxIframes() {
	return (tree: Root) => {
		visit(tree, "element", (node: Element) => {
			if (node.tagName === "iframe") {
				node.properties = { ...node.properties, sandbox: "allow-same-origin" };
			}
		});
	};
}

function rehypeIframeToThumbnail() {
	return (tree: Root) => {
		// Iframes appear as either:
		// 1. element nodes (when remark parses them as inline HTML inside paragraphs and rehype-raw runs), or
		// 2. raw nodes (when remark-rehype { allowDangerousHtml: true } passes block-level HTML through).
		// We handle both.

		visit(tree, "element", (node: any, index: number | null | undefined, parent: any) => {
			if (node.tagName !== "iframe") return;
			if (!parent || typeof index !== "number") return;

			const src = node.properties?.src;
			if (typeof src !== "string") return;

			const ytId = extractYouTubeId(src);
			const replacement = ytId
				? {
						type: "raw" as const,
						value:
							`<a class="yt-link" href="https://www.youtube.com/watch?v=${ytId}">` +
							`<img class="yt-thumb" src="https://img.youtube.com/vi/${ytId}/maxresdefault.jpg" alt="YouTube video"/>` +
							`<span class="yt-play">▶</span>` +
							`</a>`,
					}
				: {
						type: "raw" as const,
						value: buildIframeFallbackLink(src),
					};

			parent.children[index] = replacement;
		});

		// Transform raw HTML nodes whose value contains an <iframe>.
		visit(tree, "raw" as any, (node: any) => {
			if (typeof node.value !== "string") return;
			if (!/<iframe\b/i.test(node.value)) return;
			// Lazy [\s\S]*? matches iframes with body content (e.g., fallback text)
			// without gobbling across two adjacent iframes.
			node.value = node.value.replace(/<iframe\b[^>]*>[\s\S]*?<\/iframe>/gi, (match: string) =>
				transformIframeHtml(match),
			);
			// Also handle self-closing or void-style iframes just in case.
			node.value = node.value.replace(/<iframe\b[^>]*\/>/gi, (match: string) =>
				transformIframeHtml(match),
			);
		});
	};
}

export type RenderMode = "web" | "print";

export interface ArticleMetadata {
	title: string;
	subtitle?: string;
	authors: { name: string; avatar: string; bio?: string }[];
	readingTime: string;
	bylineBio?: string;
	date: string;
	publishedAt: string | null;
	updatedAt: string | null;
	isFree: boolean | null;
	postImage: string | null;
	postImageZoom: string | null;
	postImageCaption?: string;
	url: string | null;
	tableOfContents: Array<{ id: string; title: string; level: number }>;
}

/** Recursively concatenate the text content of a HAST node. */
function hastText(node: any): string {
	if (!node) return "";
	if (node.type === "text") return node.value ?? "";
	if (Array.isArray(node.children)) {
		return node.children.map(hastText).join("");
	}
	return "";
}

/**
 * Rehype plugin that collects every h2/h3/h4 heading (with an id) into the
 * provided accumulator, capturing its id, heading level and text content.
 * Must run AFTER rehypeSlug so heading ids are populated.
 */
function rehypeCollectToc(acc: Array<{ id: string; title: string; level: number }>) {
	return (tree: Root) => {
		visit(tree, "element", (n: Element) => {
			if (["h2", "h3", "h4"].includes(n.tagName) && n.properties?.id) {
				const title = hastText(n).trim();
				if (!title) return;
				acc.push({
					id: String(n.properties.id),
					level: Number(n.tagName[1]),
					title,
				});
			}
		});
	};
}

export interface RenderResult {
	html: string;
	markdown: string;
	article: ArticleMetadata | null;
	cacheStatus: string;
}

export async function renderArticle(
	slug: string,
	options: { mode?: RenderMode; clientUa?: string } = {},
): Promise<RenderResult> {
	const mode = options.mode ?? "web";

	const renderResult = await render(slug, true, options.clientUa);
	if (!renderResult) throw new Error("ARTICLE_NOT_FOUND");

	let article: ArticleMetadata | null = null;
	let markdownContent = renderResult.markdown;
	// Headings collected from the actual rendered HTML (correct rehype-slug ids
	// + real h2/h3/h4 levels). Falls back to the frontmatter list only if empty.
	const tocAcc: Array<{ id: string; title: string; level: number }> = [];

	try {
		const parsed = FrontMatter(renderResult.markdown);
		const metadata = parsed.attributes as Record<string, any>;
		markdownContent = parsed.body;

		// Frontmatter table_of_contents is flat ({id,title}) and its slugs may not
		// match the rendered ids. Use it only as a fallback (level 2) when the
		// heading collector finds nothing.
		let tableOfContents: Array<{ id: string; title: string; level: number }> = [];

		if (metadata.table_of_contents && Array.isArray(metadata.table_of_contents)) {
			tableOfContents = metadata.table_of_contents.map((item: { id: string; title: string }) => ({
				id: item.id,
				title: item.title,
				level: 2,
			}));
		}

		// Extract preview image - handle both responsive object and simple string formats
		let postImage: string | null = null;
		let postImageZoom: string | null = null;
		let postImageCaption: string | null = null;
		if (metadata.preview_image) {
			if (typeof metadata.preview_image === "string") {
				// Simple string format (backward compatibility or base64 data URI)
				postImage = metadata.preview_image;
			} else if (typeof metadata.preview_image === "object" && metadata.preview_image.medium) {
				// Responsive object format - use medium for display, zoom for HD
				postImage = metadata.preview_image.medium;
				postImageZoom = metadata.preview_image.zoom || null;
				postImageCaption = metadata.preview_image.caption || null;
			}
		}

		// Canonical author model: a list. `authors` (NYT etc.) is preferred;
		// a single `author` (Medium, string or object) is normalized into a
		// one-element list. Reading time is a separate article field.
		const avatarFor = (name: string, avatar?: string) =>
			avatar ||
			`https://ui-avatars.com/api/?name=${encodeURIComponent(name || "Unknown")}&background=random`;

		const readingTime = metadata.reading_time ? `${metadata.reading_time} min read` : "";

		let authors: { name: string; avatar: string; bio?: string }[];
		if (Array.isArray(metadata.authors) && metadata.authors.length > 0) {
			authors = metadata.authors.map((a: { name?: string; avatar?: string; bio?: string }) => ({
				name: a.name || "Unknown",
				avatar: avatarFor(a.name || "Unknown", a.avatar),
				bio: a.bio || undefined,
			}));
		} else if (metadata.author) {
			const name =
				typeof metadata.author === "string"
					? metadata.author
					: metadata.author.name || "Unknown";
			const av = typeof metadata.author === "object" ? metadata.author.avatar : undefined;
			authors = [{ name, avatar: avatarFor(name, av) }];
		} else {
			authors = [{ name: "Unknown", avatar: avatarFor("Unknown") }];
		}

		article = {
			title: metadata.title || "Untitled",
			subtitle: metadata.subtitle || undefined,
			authors,
			readingTime,
			bylineBio: metadata.byline_bio || undefined,
			date: metadata.first_published_at
				? new Date(metadata.first_published_at).toISOString()
				: new Date().toISOString(),
			publishedAt: metadata.first_published_at
				? new Date(metadata.first_published_at).toISOString()
				: null,
			updatedAt: metadata.updated_at
				? new Date(metadata.updated_at).toISOString()
				: null,
			isFree:
				typeof metadata.is_locked === "boolean" ? !metadata.is_locked : null,
			postImage,
			postImageZoom,
			postImageCaption: postImageCaption || undefined,
			url: metadata.url || null,
			tableOfContents,
		};
	} catch (error) {
		console.warn("Failed to parse frontmatter:", error);
	}

	const baseProcessor = unified()
		.use(remarkParse)
		.use(remarkRehype, { allowDangerousHtml: true })
		// SECURITY: article body is attacker-controlled (any Medium author can
		// embed raw <script>/<img onerror>/javascript: in their post text).
		// rehypeRaw parses the raw HTML into HAST; rehypeSanitize then strips
		// scripts, event handlers, and dangerous URL protocols. MUST run before
		// the trusted injectors below (link icons, shiki, copy buttons) so their
		// output isn't stripped. Without this, the {@html content} sink is a
		// stored-XSS hole (cache-poisoned per article).
		.use(rehypeRaw)
		.use(rehypeSanitize, FREEDIUM_SANITIZE_SCHEMA)
		.use(rehypeSandboxIframes)
		.use(rehypeSlug)
		.use(rehypeCollectToc, tocAcc)
		.use(rehypeExternalLinks, {
			target: "_blank",
			rel: ["nofollow"],
			content: mode === "print" ? undefined : externalLinkIcon,
		});

	const withIframeTransform =
		mode === "print" ? baseProcessor.use(rehypeIframeToThumbnail) : baseProcessor;

	const processor = withIframeTransform
		.use(rehypeHighlight, { mode })
		.use(rehypeStringify, { allowDangerousHtml: true });

	const result = await processor.process(markdownContent);

	// Prefer the headings collected from the actual rendered HTML (correct ids +
	// real levels) over the flat frontmatter fallback.
	if (article && tocAcc.length) {
		// Drop leading "orphan" headings deeper than the shallowest level that
		// appear before the first top-level heading — e.g. a caption/attribution
		// the author rendered as an H4 above the first real section. Genuinely
		// nested deeper headings elsewhere are kept.
		const minLevel = Math.min(...tocAcc.map((t) => t.level));
		let start = 0;
		while (start < tocAcc.length && tocAcc[start].level > minLevel) start++;
		article.tableOfContents = tocAcc.slice(start);
	}

	// Render the cover-image caption through the SAME pipeline so markdown spans
	// (links, emphasis, code) become HTML — body figcaptions get rendered because
	// medium-parser drops them into the body markdown stream; this caption lives
	// in YAML frontmatter and would otherwise reach the client as raw markdown.
	if (article && article.postImageCaption) {
		const captionHtml = String(await processor.process(article.postImageCaption));
		// Strip the wrapping <p>…</p> remark-rehype adds; <figcaption> is an
		// inline-content context, so a block paragraph is wrong here.
		article.postImageCaption = captionHtml
			.trim()
			.replace(/^<p>([\s\S]*)<\/p>$/, "$1")
			.trim();
	}

	// Byline bio is raw HTML (NYT #enhanced-byline: short per-article author bios
	// + datelines). Sanitize through the same pipeline; client renders it {@html}.
	if (article?.bylineBio) {
		article.bylineBio = String(await processor.process(article.bylineBio))
			.trim()
			.replace(/^<p>([\s\S]*)<\/p>$/, "$1")
			.trim();
	}

	// Render body-image caption markdown → HTML server-side (same pipeline as
	// the cover caption above) so the client lightbox just displays it — no
	// client-side markdown parsing. Captions arrive as data-caption="<md>" on
	// the raw <picture> the backend emits.
	let html = String(result);
	const decodeEntities = (s: string): string =>
		s
			.replace(/&lt;/g, "<")
			.replace(/&gt;/g, ">")
			.replace(/&quot;/g, '"')
			.replace(/&#39;/g, "'")
			.replace(/&amp;/g, "&"); // &amp; last to avoid double-decoding
	const attrEscape = (s: string): string =>
		s
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	const captionAttrs = new Set<string>();
	for (const mm of html.matchAll(/data-caption="([^"]*)"/g)) captionAttrs.add(mm[1]);
	const renderedByAttr = new Map<string, string>();
	for (const escaped of captionAttrs) {
		if (!escaped) continue;
		const renderedCaption = String(await processor.process(decodeEntities(escaped)))
			.trim()
			.replace(/^<p>([\s\S]*)<\/p>$/, "$1")
			.trim();
		renderedByAttr.set(escaped, attrEscape(renderedCaption));
	}
	if (renderedByAttr.size) {
		html = html.replace(
			/data-caption="([^"]*)"/g,
			(full, escaped) =>
				renderedByAttr.has(escaped) ? `data-caption="${renderedByAttr.get(escaped)}"` : full,
		);
	}

	return {
		html,
		markdown: markdownContent,
		article,
		cacheStatus: renderResult.cache_status ?? "miss",
	};
}
