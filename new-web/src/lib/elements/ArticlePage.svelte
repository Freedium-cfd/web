<script lang="ts">
	import Header from '$lib/elements/Header.svelte';
	import { formatDate } from '$lib/utils/dateFormatter';
	import { getErrorMessage } from '$lib/utils/errorFormatter';
	import ImageZoom from '$lib/elements/ImageZoom.svelte';
	import Skeleton from '$lib/components/ui/skeleton/skeleton.svelte';
	import Footer from '$lib/elements/Footer.svelte';
	import './ArticlePage.css';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import ArticleActions from '$lib/elements/ArticleActions.svelte';
	import HeroiconsDocumentArrowDown20Solid from '~icons/heroicons/document-arrow-down-20-solid';
	import HeroiconsDocumentText20Solid from '~icons/heroicons/document-text-20-solid';
	import HeroiconsChevronDown20Solid from '~icons/heroicons/chevron-down-20-solid';
	import { onMount } from 'svelte';
	import { mode } from 'mode-watcher';
	import { initializeCodeCopyButtons } from '$lib/codeCopy';
	import { initializeLazyIframes } from '$lib/lazyIframe';
	import { initializeImageZoom } from '$lib/imageZoom';
	import { applyTheme } from '$lib/iframeTheme';
	import { articleDownloadUrl } from '@/services';
	import type { ArticlePageData } from '$lib/types';

	interface Props {
		data: ArticlePageData;
	}

	let { data }: Props = $props();

	let article = $derived(data.article);
	let authors = $derived(article?.authors ?? []);
	let content = $derived(data.content);
	let loading = $derived(data.loading);
	let error = $derived(data.error);
	let contentLoaded = $derived(!loading && !!content);
	let showSkeleton = $derived(!error && !contentLoaded);
	let toc = $derived(article?.tableOfContents ?? []);

	// Contents accordion: collapsed by default, showing only the first few
	// sections; clicking the header (or "show all") reveals the rest.
	const TOC_COLLAPSED_COUNT = 5;
	let tocExpanded = $state(false);
	let tocVisible = $derived(tocExpanded ? toc : toc.slice(0, TOC_COLLAPSED_COUNT));
	// Normalize indentation to the shallowest heading the article actually
	// uses: an all-H3 article (Medium often flattens to one level) renders
	// flat, while a mixed H2/H3/H4 article shows real nesting.
	let tocMinLevel = $derived(toc.length ? Math.min(...toc.map((t) => t.level)) : 2);

	function downloadMarkdown() {
		if (!data.slug) return;
		const link = document.createElement('a');
		link.href = articleDownloadUrl(data.slug);
		// /api/download is a +server.ts API route, not a +page. Without these,
		// SvelteKit's client router hijacks the click and tries to fetch
		// /api/download/__data.json (which 404s) instead of downloading.
		// The download attribute + reload opt-out force a real browser
		// navigation so the Content-Disposition response downloads.
		link.download = '';
		link.setAttribute('data-sveltekit-reload', '');
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	}

	let pdfState = $state<'idle' | 'generating'>('idle');

	async function downloadPdf() {
		if (!data.slug || pdfState === 'generating') return;
		pdfState = 'generating';
		try {
			const res = await fetch('/api/pdf', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ slug: data.slug }),
			});
			if (!res.ok) {
				throw new Error(`PDF generation failed: ${res.status}`);
			}
			const blob = await res.blob();
			const filename = res.headers.get('content-disposition')
				?.match(/filename="([^"]+)"/)?.[1] || 'article.pdf';
			const url = URL.createObjectURL(blob);
			const a = Object.assign(document.createElement('a'), {
				href: url,
				download: filename
			});
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		} catch (err) {
			console.error('PDF download failed:', err);
			alert('PDF download failed. Please try again.');
		} finally {
			pdfState = 'idle';
		}
	}

	onMount(() => {
		if (contentLoaded) {
			initializeCodeCopyButtons();
			initializeLazyIframes();
			initializeImageZoom();
		}
	});

	// Keep iframe srcdoc in sync with the page theme: every time mode.current
	// changes, refetch each iframe's HTML with the new theme and swap srcdoc.
	// Initial run also catches dark-mode users on first load (iframes are
	// always SSRed with the light variant since the server can't read the
	// client's theme preference). State/scroll inside the iframe resets
	// on each swap — that's the known cost of approach D.
		$effect(() => {
			if (!contentLoaded) return;
			const theme: "light" | "dark" = mode.current === "dark" ? "dark" : "light";
			// Retry-loop: srcdoc iframes may not have documentElement ready
			// when first queried (asynchronous srcdoc parsing). Retry every
			// 100ms until all iframes are themed or 10 attempts exhausted.
			let attempts = 0;
			const MAX = 10;
			function retry() {
				if (++attempts > MAX) return;
				let pending = false;
				for (const iframe of document.querySelectorAll<HTMLIFrameElement>("iframe[data-iframe-id]")) {
					if (!applyTheme(iframe, theme)) pending = true;
				}
				if (pending) setTimeout(retry, 100);
			}
			retry();
		});
</script>

<svelte:head>
	<title>{error ? 'Freedium' : data?.article?.title || 'Freedium'} - Freedium</title>
	{#if article?.subtitle}
		<meta name="description" content={article.subtitle} />
	{/if}
</svelte:head>

<Header />
<div class="flex flex-col min-h-screen">
	<main class="flex-1 w-full h-full max-w-5xl px-4 py-8 mx-auto">
		<div>
			{#if error}
				<div class="error-card">
					<div class="error-status">{error.status}</div>
					<div class="error-eyebrow">— {error.code.replace(/_/g, ' ')}</div>
					<h1 class="error-title">
						{#if error.code === 'UNSUPPORTED_SITE'}
							Site not supported.
						{:else if error.status === 404}
							Article not found.
						{:else}
							Something went wrong.
						{/if}
					</h1>
					<p class="error-message">{getErrorMessage(error)}</p>

					{#if error.details && import.meta.env.DEV}
						<pre class="error-details">{error.details}</pre>
					{/if}

					<div class="error-actions">
						<a href="/" class="error-btn primary">Return home</a>
						<button
							type="button"
							class="error-btn ghost"
							onclick={() => window.location.reload()}
						>
							Try again
						</button>
					</div>
				</div>
			{:else if showSkeleton}
				<article class="w-full overflow-hidden bg-white rounded-lg shadow-lg dark:bg-zinc-900">
					<Skeleton class="w-full h-96" />
					<div class="p-6 bg-gray-50 dark:bg-zinc-800">
						<Skeleton class="w-32 h-4 mb-2" />
						<Skeleton class="w-full h-10 mb-4" />
						<div class="flex items-center">
							<Skeleton class="w-12 h-12 mr-4 rounded-full" />
							<div class="space-y-2">
								<Skeleton class="w-40 h-4" />
								<Skeleton class="w-32 h-4" />
							</div>
						</div>
					</div>
					<div class="p-6">
						<div class="space-y-4">
							<Skeleton class="w-full h-4" />
							<Skeleton class="w-full h-4" />
							<Skeleton class="w-3/4 h-4" />
						</div>
					</div>
				</article>
			{:else if article}
				<article class="overflow-hidden bg-white rounded-lg shadow-lg dark:bg-zinc-900">
					<div data-nosnippet style="display: contents">
						<ArticleActions originalUrl={article.url} title={article.title} />
					</div>
					{#if article.postImage}
						<ImageZoom
							src={article.postImage}
							zoomSrc={article.postImageZoom}
							caption={article.postImageCaption}
							alt="Post cover image"
							class="object-cover w-full h-auto min-h-96"
						/>
					{/if}
					<header class="p-6 bg-gray-50 dark:bg-zinc-800">
						<p class="mb-2 text-gray-600 dark:text-gray-400">{formatDate(article.date)}</p>
						<h1 class="mb-4 text-4xl font-bold text-gray-900 dark:text-white">{article.title}</h1>
						{#if article.subtitle}
							<p class="mb-4 text-xl text-gray-700 dark:text-gray-300">{article.subtitle}</p>
						{/if}
						<div class="flex items-start">
							<!-- avatars: overlapping stack for multiple authors -->
							<div class="flex mr-4 shrink-0">
								{#each authors as a, i (a.name + i)}
									<img
										src={a.avatar}
										alt=""
										class="w-12 h-12 rounded-full object-cover bg-gray-200 dark:bg-zinc-700 border-2 border-gray-50 dark:border-zinc-800 {i > 0 ? '-ml-4' : ''}"
									/>
								{/each}
							</div>
							<div>
								<p class="font-semibold text-gray-900 dark:text-white">
									By {authors.map((a) => a.name).join(' and ')}
								</p>
								{#if article.readingTime}
								<p class="text-gray-600 dark:text-gray-400">{article.readingTime}</p>
							{/if}
								{#if article.bylineBio}
									<div class="author-bio mt-1 text-sm text-gray-500 dark:text-gray-400">
										{@html article.bylineBio}
									</div>
								{/if}
							</div>
						</div>
					</header>

					<section
						class="px-6 py-5 border-b border-gray-200 dark:border-zinc-700"
						aria-labelledby={toc.length > 0 ? 'toc-heading' : undefined}
					>
						<!-- Row 1: download action, right-aligned on its own line -->
						<div class="flex justify-end">
							<DropdownMenu.Root>
								<DropdownMenu.Trigger>
									{#snippet child({ props })}
										<button
											{...props}
											class="flex items-center justify-between gap-2 px-4 py-2 text-sm text-primary bg-gray-50 rounded-lg cursor-pointer select-none dark:bg-zinc-800 hover:bg-gray-100 dark:hover:bg-zinc-700"
										>
											<span>Download article</span>
											<HeroiconsChevronDown20Solid class="size-4" />
										</button>
									{/snippet}
								</DropdownMenu.Trigger>
								<DropdownMenu.Content class="w-56" side="bottom" align="end">
									<DropdownMenu.Item onclick={downloadPdf} disabled={pdfState === 'generating'}>
										<HeroiconsDocumentArrowDown20Solid class="size-4 text-red-500" />
										{pdfState === 'generating' ? 'Generating PDF…' : 'Download as PDF'}
									</DropdownMenu.Item>
									<DropdownMenu.Item onclick={downloadMarkdown}>
										<HeroiconsDocumentText20Solid class="size-4 text-blue-500" />
										Download as Markdown
									</DropdownMenu.Item>
								</DropdownMenu.Content>
							</DropdownMenu.Root>
						</div>

						<!-- Row 2: Contents accordion (own row, collapsed by default) -->
						{#if toc.length > 0}
							<div
								data-nosnippet
								class="mt-4 overflow-hidden border rounded-lg border-gray-200 dark:border-zinc-700"
							>
								<button
									type="button"
									aria-expanded={tocExpanded}
									aria-controls="toc-list"
									onclick={() => (tocExpanded = !tocExpanded)}
									class="flex items-center justify-between w-full gap-2 px-4 py-3 cursor-pointer select-none bg-gray-50 dark:bg-zinc-800 hover:bg-gray-100 dark:hover:bg-zinc-700"
								>
									<span class="flex items-center gap-2">
										<h2 id="toc-heading" class="text-lg font-semibold text-primary">Contents</h2>
										<span
											class="px-2 py-0.5 text-xs font-medium rounded-full text-zinc-600 bg-gray-200 dark:bg-zinc-700 dark:text-zinc-300"
										>
											{toc.length}
										</span>
									</span>
									<HeroiconsChevronDown20Solid
										class="size-5 text-zinc-500 transition-transform duration-200 {tocExpanded
											? 'rotate-180'
											: ''}"
									/>
								</button>
								<ul id="toc-list" class="divide-y divide-gray-200 dark:divide-zinc-700">
									{#each tocVisible as item, i}
										<li>
											<a
												href={`#${item.id}`}
												class="flex items-start gap-3 py-3 pr-4 text-sm transition-colors text-zinc-700 hover:text-zinc-900 dark:text-gray-200 dark:hover:text-white hover:bg-accent/60"
												class:toc-sub={item.level > tocMinLevel}
												style="padding-left: {0.75 + (item.level - tocMinLevel) * 1}rem"
											>
												<span
													class="shrink-0 w-6 pt-0.5 font-mono text-xs text-right text-zinc-400 dark:text-zinc-500"
												>
													{#if item.level > tocMinLevel}
														&ndash;
													{:else}
														{i + 1}
													{/if}
												</span>
												<span class="break-words">{item.title}</span>
											</a>
										</li>
									{/each}
								</ul>
								{#if !tocExpanded && toc.length > TOC_COLLAPSED_COUNT}
									<button
										type="button"
										onclick={() => (tocExpanded = true)}
										class="block w-full px-4 py-2.5 text-sm font-medium text-center cursor-pointer text-primary border-t border-gray-200 dark:border-zinc-700 bg-gray-50/50 dark:bg-zinc-800/50 hover:bg-gray-100 dark:hover:bg-zinc-700"
									>
										Show all {toc.length} sections
									</button>
								{/if}
							</div>
						{/if}
					</section>

					<div class="p-6 dark:text-gray-300">
						<div class="prose max-w-none prose-external-links">
							{#if content}
								{@html content}
							{:else}
								<p>Error loading content</p>
							{/if}
						</div>
					</div>
					<div data-nosnippet class="border-t border-gray-200 dark:border-zinc-700">
						<ArticleActions originalUrl={article.url} title={article.title} />
					</div>
				</article>
			{/if}
		</div>
	</main>
	<Footer />
</div>

<style>
	/* De-emphasize nested (h3/h4) table-of-contents entries. */
	.toc-sub {
		font-size: 0.8125rem;
		color: var(--color-zinc-500, #71717a);
	}

	.error-card {
		max-width: 540px;
		margin: 80px auto;
		padding: 56px 36px 44px;
		background: var(--bg-2);
		border: 1px solid var(--line);
		border-radius: 12px;
		text-align: center;
	}

	.error-status {
		font-family: var(--font-serif);
		font-size: 96px;
		line-height: 1;
		letter-spacing: -0.04em;
		color: var(--accent);
		font-style: italic;
		margin-bottom: 14px;
	}

	.error-eyebrow {
		font-family: var(--font-mono);
		font-size: 11px;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--ink-3);
		margin-bottom: 18px;
	}

	.error-title {
		font-family: var(--font-serif);
		font-weight: 400;
		font-size: 36px;
		line-height: 1.1;
		letter-spacing: -0.02em;
		margin: 0 0 14px;
		color: var(--ink);
		text-wrap: balance;
	}

	.error-message {
		font-size: 14.5px;
		color: var(--ink-2);
		line-height: 1.55;
		max-width: 420px;
		margin: 0 auto 28px;
	}

	.error-details {
		font-family: var(--font-mono);
		font-size: 11.5px;
		text-align: left;
		color: var(--ink-3);
		background: var(--bg);
		border: 1px dashed var(--line-2);
		border-radius: 6px;
		padding: 12px 14px;
		overflow: auto;
		max-height: 220px;
		margin: 0 0 24px;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.error-actions {
		display: flex;
		justify-content: center;
		gap: 10px;
		flex-wrap: wrap;
	}

	.error-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 10px 20px;
		border-radius: 8px;
		font-family: var(--font-sans);
		font-size: 13px;
		text-decoration: none;
		cursor: pointer;
		transition: filter 0.15s, color 0.15s, border-color 0.15s, background 0.15s;
	}
	.error-btn.primary {
		background: var(--accent);
		color: oklch(0.18 0.02 145);
		border: 1px solid var(--accent);
		font-weight: 600;
	}
	.error-btn.primary:hover { filter: brightness(1.08); }

	.error-btn.ghost {
		background: transparent;
		color: var(--ink-2);
		border: 1px solid var(--line-2);
		font-weight: 500;
	}
	.error-btn.ghost:hover {
		color: var(--ink);
		border-color: var(--ink-3);
		background: var(--bg-3);
	}

	@media (max-width: 540px) {
		.error-card {
			padding: 40px 24px 32px;
			margin: 40px auto;
		}
		.error-status { font-size: 72px; }
		.error-title { font-size: 28px; }
	}
</style>
