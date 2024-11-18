import { mdsvex, escapeSvelte } from 'mdsvex';
import { createHighlighter } from 'shiki';
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

import { h } from 'hastscript';

export function addCopyButton(options = {}) {
	const toggleMs = options.toggle || 3000;

	return {
		name: 'shiki-transformer-copy-button',
		pre(node) {
			const button = h(
				'button',
				{
					class: 'copy',
					'data-code': this.source,
					onclick: `
          navigator.clipboard.writeText(this.dataset.code);
          this.classList.add('copied');
          setTimeout(() => this.classList.remove('copied'), ${toggleMs});
		  window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Copied to clipboard' } }));
        `
				},
				[h('span', { class: 'ready' }), h('span', { class: 'success' })]
			);

			node.children.push(button);
		}
	};
}

/** @type {import('mdsvex').MdsvexOptions} */
const mdsvexOptions = {
	extensions: ['.md'],
	highlight: {
		highlighter: async (code, lang = 'text') => {
			const highlighter = await createHighlighter({
				themes: ['poimandres'],
				langs: ['javascript', 'typescript']
			});
			await highlighter.loadLanguage('javascript', 'typescript');
			const html = escapeSvelte(
				highlighter.codeToHtml(code, {
					lang,
					theme: 'poimandres',
					transformers: [addCopyButton({ toggle: 1200 })]
				})
			);
			return `{@html \`${html}\` }`;
		}
	}
};

/** @type {import('@sveltejs/kit').Config} */
const config = {
	extensions: ['.svelte', '.md'],
	preprocess: [vitePreprocess(), mdsvex(mdsvexOptions)],

	kit: {
		adapter: adapter()
	}
};

export default config;
