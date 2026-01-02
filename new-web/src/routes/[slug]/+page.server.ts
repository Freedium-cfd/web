import { render } from "@/services";
import { compile } from "mdsvex";
import { createHighlighter, type HighlighterGeneric, type BundledLanguage, type BundledTheme } from "shiki";
import { toHtml } from "hast-util-to-html";
import { h, s } from "hastscript";
import type { Element } from "hast";
import type { PageServerLoad } from "./$types";
import type { ArticleErrorCode } from "$lib/types";
import { getIconData, iconToSVG } from "@iconify/utils";
import heroiconsData from "@iconify/json/json/heroicons.json";
import rehypeExternalLinks, { type Options as RehypeExternalLinksOptions } from "rehype-external-links";

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
	langs: ["javascript", "typescript"],
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
		await highlighterInstance.loadLanguage("javascript", "typescript");
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

const ErrorCodes: Record<ArticleErrorCode, ArticleErrorCode> = {
	ARTICLE_NOT_FOUND: "ARTICLE_NOT_FOUND",
	RENDER_ERROR: "RENDER_ERROR",
	COMPILE_ERROR: "COMPILE_ERROR",
	INTERNAL_ERROR: "INTERNAL_ERROR",
};

export const load: PageServerLoad = async ({ params }) => {
	let transformed = null;
	try {
		transformed = await render("medium");
	} catch (err) {
		console.error("Failed to render article:", err);
		return {
			slug: params.slug,
			loading: false,
			content: null,
			article: null,
			error: {
				status: 500,
				message: "Failed to render article",
				code: ErrorCodes.RENDER_ERROR,
				details: import.meta.env.DEV ? (err as Error).message : undefined,
			},
		};
	}

	if (!transformed) {
		return {
			slug: params.slug,
			loading: false,
			content: null,
			article: null,
			error: {
				status: 404,
				message: "Article not found",
				code: ErrorCodes.ARTICLE_NOT_FOUND,
			},
		};
	}

	try {
		const result = await compile(transformed.text, {
			rehypePlugins: [
				[rehypeExternalLinks as unknown as import("unified").Plugin, {
					target: "_blank",
					rel: ["nofollow"],
					content: externalLinkIcon,
				} as import("unified").Settings],
			],
			highlight: {
				highlighter: createHighlightedCode,
			},
		});

		return {
			slug: params.slug,
			loading: false,
			content: result?.code ?? null,
			article: transformed.article,
			error: null,
		};
	} catch (compileError) {
		return {
			slug: params.slug,
			loading: false,
			content: null,
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
