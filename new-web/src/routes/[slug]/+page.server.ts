import { render } from "@/services";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import rehypeStringify from "rehype-stringify";
import { createHighlighter, type HighlighterGeneric, type BundledLanguage, type BundledTheme } from "shiki";
import { visit } from "unist-util-visit";
import { toHtml } from "hast-util-to-html";
import { h, s } from "hastscript";
import type { Element, Root } from "hast";
import type { PageServerLoad } from "./$types";
import type { ArticleErrorCode } from "$lib/types";
import { getIconData, iconToSVG } from "@iconify/utils";
import heroiconsData from "@iconify/json/json/heroicons.json";
import rehypeExternalLinks, { type Options as RehypeExternalLinksOptions } from "rehype-external-links";
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

const HIGHLIGHT_CONFIG = {
	themes: ["github-light", "github-dark"],
	langs: ["javascript", "typescript", "nginx", "bash", "ruby", "python"],
};

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

async function getHighlighter(): Promise<HighlighterGeneric<BundledLanguage, BundledTheme>> {
	if (!highlighterInstance) {
		highlighterInstance = await createHighlighter(HIGHLIGHT_CONFIG);
		await highlighterInstance.loadLanguage("javascript", "typescript", "nginx", "bash", "ruby", "python");
	}
	return highlighterInstance;
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
			class: `code-copy-btn absolute right-3 ${positionClass} size-8 p-1.5 flex items-center justify-center bg-black/50 text-white rounded-md transition-colors duration-200 cursor-pointer hover:bg-black/70`,
		},
		[
			h("span", { class: "ready block" }, clipboardIcon ? [clipboardIcon] : []),
			h("span", { class: "success hidden" }, clipboardCheckIcon ? [clipboardCheckIcon] : []),
		],
	);

	return toHtml(button, { allowDangerousHtml: true });
}

async function createHighlightedCode(code: string, lang: string | null = "text"): Promise<string> {
	const highlighter = await getHighlighter();
	const language = lang ?? "text";

	const lightHtml = highlighter.codeToHtml(code, {
		lang: language,
		theme: "github-light",
		transformers: [
			{
				code(node) {
					node.properties = { ...node.properties, ...CODE_ATTRIBUTES };
					return node;
				},
			},
		],
	});

	const darkHtml = highlighter.codeToHtml(code, {
		lang: language,
		theme: "github-dark",
		transformers: [
			{
				code(node) {
					node.properties = { ...node.properties, ...CODE_ATTRIBUTES };
					return node;
				},
			},
		],
	});

	const buttonHtml = createCodeCopyButton(code, 1200);

	return `
		<div class="relative">
			${buttonHtml}
			<div class="dark:hidden">${lightHtml}</div>
			<div class="hidden dark:block">${darkHtml}</div>
		</div>
	`;
}

// Rehype plugin for syntax highlighting
function rehypeHighlight() {
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
						} catch (e) {
							console.error('Failed to parse decorations:', e);
						}
					}


					// Generate highlighted HTML with decorations
					const lightHtml = highlighter.codeToHtml(codeText, {
						lang,
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

					const darkHtml = highlighter.codeToHtml(codeText, {
						lang,
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
					const wrappedHtml = `
						<div class="relative">
							${buttonHtml}
							<div class="dark:hidden">${lightHtml}</div>
							<div class="hidden dark:block">${darkHtml}</div>
						</div>
					`;

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

const ErrorCodes: Record<ArticleErrorCode, ArticleErrorCode> = {
	ARTICLE_NOT_FOUND: "ARTICLE_NOT_FOUND",
	RENDER_ERROR: "RENDER_ERROR",
	COMPILE_ERROR: "COMPILE_ERROR",
	INTERNAL_ERROR: "INTERNAL_ERROR",
};

export const load: PageServerLoad = async ({ params }) => {
	let renderResult = null;
	try {
		// Request with frontmatter to get metadata
		renderResult = await render(params.slug, true);
	} catch (err) {
		console.error("Failed to render article:", err);
		return {
			slug: params.slug,
			loading: false,
			content: null,
			markdown: null,
			article: null,
			error: {
				status: 500,
				message: "Failed to render article",
				code: ErrorCodes.RENDER_ERROR,
				details: import.meta.env.DEV ? (err as Error).message : undefined,
			},
		};
	}

	if (!renderResult) {
		return {
			slug: params.slug,
			loading: false,
			content: null,
			markdown: null,
			article: null,
			error: {
				status: 404,
				message: "Article not found",
				code: ErrorCodes.ARTICLE_NOT_FOUND,
			},
		};
	}

	// Parse frontmatter to extract metadata using front-matter library
	let article = null;
	let markdownContent = renderResult.markdown;

	try {
		const parsed = FrontMatter(renderResult.markdown);
		const metadata = parsed.attributes as Record<string, any>;
		markdownContent = parsed.body;

		// Use table_of_contents from frontmatter
		let tableOfContents: Array<{ id: string; title: string }> = [];

		if (metadata.table_of_contents && Array.isArray(metadata.table_of_contents)) {
			tableOfContents = metadata.table_of_contents;
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

		// Extract author information - handle both old string format and new object format
		let author = {
			name: "Unknown",
			avatar: `https://ui-avatars.com/api/?name=Unknown&background=random`,
			role: "Author",
		};

		if (metadata.author) {
			if (typeof metadata.author === "string") {
				// Old format: just author name string
				author.name = metadata.author;
				author.avatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(metadata.author)}&background=random`;
			} else if (typeof metadata.author === "object" && metadata.author.name) {
				// New format: author object with name and avatar
				author.name = metadata.author.name;
				if (metadata.author.avatar) {
					author.avatar = metadata.author.avatar;
				} else {
					author.avatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(metadata.author.name)}&background=random`;
				}
			}
		}

		// Add reading time as role if available
		if (metadata.reading_time) {
			author.role = `${metadata.reading_time} min read`;
		}

		article = {
			title: metadata.title || "Untitled",
			subtitle: metadata.subtitle || undefined,
			author,
			date: new Date().toISOString(),
			postImage,
			postImageZoom,
			postImageCaption: postImageCaption || undefined,
			url: metadata.url || null,
			tableOfContents,
		};
	} catch (error) {
		// No frontmatter found or parsing error - use markdown as-is
		console.warn("Failed to parse frontmatter:", error);
	}

	try {
		const processor = unified()
			.use(remarkParse)
			.use(remarkRehype, { allowDangerousHtml: true })
			.use(rehypeSlug)
			.use(rehypeExternalLinks, {
				target: "_blank",
				rel: ["nofollow"],
				content: externalLinkIcon,
			})
			.use(rehypeHighlight)
			.use(rehypeStringify, { allowDangerousHtml: true });

		const result = await processor.process(markdownContent);
		const htmlContent = String(result);

		return {
			slug: params.slug,
			loading: false,
			content: htmlContent,
			markdown: markdownContent,
			article,
			error: null,
		};
	} catch (compileError) {
		return {
			slug: params.slug,
			loading: false,
			content: null,
			markdown: null,
			article: null,
			error: {
				status: 500,
				message: "Failed to compile article content",
				code: ErrorCodes.COMPILE_ERROR,
				details: import.meta.env.DEV ? (compileError as Error).message : undefined,
			},
		};
	}
};
