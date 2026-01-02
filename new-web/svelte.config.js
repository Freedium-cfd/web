import { mdsvex, escapeSvelte } from "mdsvex";
import { createHighlighter } from "shiki";
import adapter from "@sveltejs/adapter-auto";
import { toHtml } from "hast-util-to-html";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { h } from "hastscript";
import remarkMixtapeEmbed from "./src/lib/utils/remark/mixtape-embed.js";
import rehypeExternalLinks from "rehype-external-links";
import rehypeShiki from "@shikijs/rehype";

const readySvg =
	"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1em' height='1em' viewBox='0 0 24 24'><path fill='none' stroke='white' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192q.56-.045 1.124-.08M15.75 18H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48 48 0 0 0-1.123-.08M15.75 18.75v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5A3.375 3.375 0 0 0 6.375 7.5H5.25m11.9-3.664A2.25 2.25 0 0 0 15 2.25h-1.5a2.25 2.25 0 0 0-2.15 1.586m5.8 0q.099.316.1.664v.75h-6V4.5q.001-.348.1-.664M6.75 7.5H4.875c-.621 0-1.125.504-1.125 1.125v12c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V16.5a9 9 0 0 0-9-9'/></svg>";

const successSvg =
	"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1em' height='1em' viewBox='0 0 16 16'><g fill='white' fill-rule='evenodd' clip-rule='evenodd'><path d='M11.986 3H12a2 2 0 0 1 2 2v6a2 2 0 0 1-1.5 1.937V7A2.5 2.5 0 0 0 10 4.5H4.063A2 2 0 0 1 6 3h.014A2.25 2.25 0 0 1 8.25 1h1.5a2.25 2.25 0 0 1 2.236 2M10.5 4v-.75a.75.75 0 0 0-.75-.75h-1.5a.75.75 0 0 0-.75.75V4z'/><path d='M2 7a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1zm6.585 1.08a.75.75 0 0 1 .336 1.005l-1.75 3.5a.75.75 0 0 1-1.16.234l-1.75-1.5a.75.75 0 0 1 .977-1.139l1.02.875l1.321-2.64a.75.75 0 0 1 1.006-.336'/></g></svg>";

export function renderCodeCopyButton(code, options = {}) {
	const toggleMs = options.toggle || 3000;
	const button = h(
		"button",
		{
			"data-code": code,
			style: `
				position: absolute;
				right: 1rem;
				top: 0.8rem;
				height: 2rem;
				width: 2rem;
				padding: 0.4rem;
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
				success.style.display = 'block';
				setTimeout(() => {
					this.classList.remove('copied');
					ready.style.display = 'block';
					success.style.display = 'none';
				}, ${toggleMs});
				window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Copied to clipboard' } }));
			`,
		},
		[
			h("span", {
				class: "ready",
				style: `
					width: 100%;
					aspect-ratio: 1 / 1;
					background-repeat: no-repeat;
					background-position: center;
					background-size: cover;
					background-image: url("${readySvg}");
					z-index: 99;
					display: block;
				`,
			}),
			h("span", {
				class: "success",
				style: `
					width: 100%;
					aspect-ratio: 1 / 1;
					background-repeat: no-repeat;
					background-position: center;
					background-size: cover;
					background-image: url("${successSvg}");
					z-index: 99;
					display: none;
				`,
			}),
		],
	);

	return toHtml(button);
}

/** @type {import('mdsvex').MdsvexOptions} */
const mdsvexOptions = {
	extensions: [".md"],
	remarkPlugins: [remarkMixtapeEmbed],
	rehypePlugins: [
		[rehypeExternalLinks, { target: "_blank", rel: ["nofollow"] }],
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
			'$lib/*': './src/lib/*'
		}
	},
};

export default config;
