import { mdsvex, escapeSvelte } from "mdsvex";
import { createHighlighter } from "shiki";
import adapter from "@sveltejs/adapter-auto";
import { toHtml } from "hast-util-to-html";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { h, s } from "hastscript";
import remarkMixtapeEmbed from "./src/lib/utils/remark/mixtape-embed.ts";
import rehypeExternalLinks from "rehype-external-links";
import rehypeShiki from "@shikijs/rehype";
import { getIconData, iconToSVG } from "@iconify/utils";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const heroiconsData = require("@iconify/json/json/heroicons.json");

// Helper to create HAST SVG node from iconify
function createIconHast(iconName, customAttrs = {}) {
	const iconData = getIconData(heroiconsData, iconName);
	if (!iconData) return null;
	const renderData = iconToSVG(iconData, { height: "1em", width: "1em" });
	return s("svg", {
		...renderData.attributes,
		...customAttrs,
		xmlns: "http://www.w3.org/2000/svg",
	}, [{ type: "raw", value: renderData.body }]);
}

// Create external link icon for rehype-external-links
const externalLinkIcon = createIconHast("arrow-top-right-on-square", {
	class: "inline ml-0.5 size-3 align-baseline relative -top-px",
	stroke: "currentColor",
	fill: "none",
	"stroke-width": "2",
	"aria-hidden": "true",
});

// Create clipboard icons for code copy button
const readyIcon = createIconHast("clipboard-document", {
	width: "100%",
	height: "100%",
	stroke: "white",
	fill: "none",
	"stroke-width": "1.5",
});

const successIcon = createIconHast("clipboard-document-check-solid", {
	width: "100%",
	height: "100%",
	fill: "white",
});

export function renderCodeCopyButton(code, options = {}) {
	const toggleMs = options.toggle || 3000;
	const button = h(
		"button",
		{
			"data-code": code,
			style: `
				position: absolute;
				right: 0.75rem;
				top: 0.75rem;
				height: 2rem;
				width: 2rem;
				padding: 0.375rem;
				display: flex;
				align-items: center;
				justify-content: center;
				background-color: rgba(0, 0, 0, 0.5);
				border-radius: 6px;
				transition: background-color 0.2s ease;
				cursor: pointer;
			`,
			onmouseover: `
				this.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
			`,
			onmouseout: `
				this.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
			`,
			onclick: `
				if (this.classList.contains('copied')) return;
				navigator.clipboard.writeText(this.dataset.code);
				this.classList.add('copied');
				const ready = this.querySelector('.ready');
				const success = this.querySelector('.success');
				ready.style.display = 'none';
				success.style.display = 'flex';
				setTimeout(() => {
					this.classList.remove('copied');
					ready.style.display = 'flex';
					success.style.display = 'none';
				}, ${toggleMs});
				window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Copied to clipboard' } }));
			`,
		},
		[
			h("span", {
				class: "ready",
				style: "display: flex; width: 100%; height: 100%;",
			}, readyIcon ? [readyIcon] : []),
			h("span", {
				class: "success",
				style: "display: none; width: 100%; height: 100%;",
			}, successIcon ? [successIcon] : []),
		],
	);

	return toHtml(button, { allowDangerousHtml: true });
}

/** @type {import('mdsvex').MdsvexOptions} */
const mdsvexOptions = {
	extensions: [".md"],
	remarkPlugins: [remarkMixtapeEmbed],
	rehypePlugins: [
		[rehypeExternalLinks, {
			target: "_blank",
			rel: ["nofollow"],
			content: externalLinkIcon,
		}],
		[rehypeShiki, { theme: "poimandres" }],
	],
	highlight: {
		highlighter: async (code, lang = "text") => {
			const highlighter = await createHighlighter({
				themes: ["poimandres"],
				langs: ["javascript", "typescript"],
			});
			await highlighter.loadLanguage("javascript", "typescript");
			const result = highlighter.codeToHast(code, {
				lang,
				theme: "poimandres",
				transformers: [
					{
						code(node) {
							node.properties = {
								...node.properties,
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
							return node;
						},
					},
				],
			});
			const resultHtml = toHtml(result);
			const buttonHtml = renderCodeCopyButton(code, { toggle: 1200 });
			const html = `<div class="relative">${buttonHtml}${resultHtml}</div>`;
			return html;
		},
	},
};

/** @type {import('@sveltejs/kit').Config} */
const config = {
	extensions: [".svelte", ".md"],
	preprocess: [vitePreprocess(), mdsvex(mdsvexOptions)],

	kit: {
		adapter: adapter(),
		alias: {
			'$lib': './src/lib',
			'$lib/*': './src/lib/*',
			'@': './src',
			'@/*': './src/*'
		}
	},
};

export default config;
