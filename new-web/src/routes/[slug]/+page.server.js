import { render } from "@/services";
import { compile } from "mdsvex";
import { createHighlighter } from "shiki";
import { toHtml } from "hast-util-to-html";
import { h } from "hastscript";

const HIGHLIGHT_CONFIG = {
	themes: ["github-light", "github-dark"],
	langs: ["javascript", "typescript"],
};

const CODE_ATTRIBUTES = {
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

let highlighterInstance = null;

async function getHighlighter() {
	if (!highlighterInstance) {
		highlighterInstance = await createHighlighter(HIGHLIGHT_CONFIG);
		await highlighterInstance.loadLanguage("javascript", "typescript");
	}
	return highlighterInstance;
}

const MOCK_ARTICLE = {
	title: "UploadThing is 5x Faster",
	date: "2024-09-13T12:00:00Z",
	author: {
		name: "Theo Browne",
		role: "CEO @ Ping Labs",
		avatar: "https://picsum.photos/seed/post1/400/300",
	},
	postImage: "https://picsum.photos/seed/postimage/1200/600",
	tableOfContents: [
		{ id: "v7-is-here", title: "V7 Is Here!" },
		{ id: "benchmarks", title: "Benchmarks" },
		{ id: "the-road-to-v7", title: "The Road To V7" },
		{ id: "uploadthing-has-served", title: "UploadThing Has Served..." },
		{
			id: "and-were-just-getting-started",
			title: "...and we're just getting started",
		},
	],
};

function createCodeCopyButton(code, toggleMs = 3000) {
	const lineCount = code.split("\n").length;
	const positionClass = lineCount <= 3 ? "top-1/2 -translate-y-1/2" : "top-3";

	const button = h(
		"button",
		{
			"data-code": code,
			"data-toggle-ms": toggleMs,
			class: `code-copy-btn absolute right-4 ${positionClass} h-8 w-8 p-1.5 flex items-center justify-center bg-black/50 rounded-md transition-colors duration-200 cursor-pointer hover:bg-black/70`,
		},
		[
			h("span", {
				class:
					"ready text-white w-full aspect-square bg-no-repeat bg-center bg-cover z-50 block icon-[heroicons--clipboard-document]",
			}),
			h("span", {
				class:
					"success w-full text-white aspect-square bg-no-repeat bg-center bg-cover z-50 hidden icon-[heroicons--clipboard-document-check-16-solid]",
			}),
		],
	);

	return toHtml(button);
}

async function createHighlightedCode(code, lang = "text") {
	const highlighter = await getHighlighter();

	const lightHtml = highlighter.codeToHtml(code, {
		lang,
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
		lang,
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

const ErrorCodes = {
	ARTICLE_NOT_FOUND: "ARTICLE_NOT_FOUND",
	RENDER_ERROR: "RENDER_ERROR",
	COMPILE_ERROR: "COMPILE_ERROR",
	INTERNAL_ERROR: "INTERNAL_ERROR",
};

export async function load({ params }) {
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
				details:
					process.env.NODE_ENV === "development" ? err.message : undefined,
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
		const { code } = await compile(transformed.text, {
			highlight: {
				highlighter: createHighlightedCode,
			},
		});

		return {
			slug: params.slug,
			loading: false,
			content: code,
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
				details:
					process.env.NODE_ENV === "development"
						? compileError.message
						: undefined,
			},
		};
	}
}
