<script lang="ts">
	import Header from '$lib/elements/Header.svelte';
	import { formatDate } from '$lib/utils/dateFormatter';
	import { getErrorMessage } from '$lib/utils/errorFormatter';
	import ImageZoom from '$lib/elements/ImageZoom.svelte';
	import Skeleton from '$lib/components/ui/skeleton/skeleton.svelte';
	import Footer from '$lib/elements/Footer.svelte';
	import './ArticlePage.css';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Drawer from '$lib/components/ui/drawer';
	import { mediaQuery } from '$lib/hooks/media-query';
	import HeroiconsArrowLeft20Solid from '~icons/heroicons/arrow-left-20-solid';
	import HeroiconsDocumentArrowDown20Solid from '~icons/heroicons/document-arrow-down-20-solid';
	import HeroiconsDocumentText20Solid from '~icons/heroicons/document-text-20-solid';
	import HeroiconsChevronDown20Solid from '~icons/heroicons/chevron-down-20-solid';
	import HeroiconsBars320Solid from '~icons/heroicons/bars-3-20-solid';
	import { onMount } from 'svelte';
	import { initializeCodeCopyButtons } from '$lib/codeCopy';
	import { initializeLazyIframes } from '$lib/lazyIframe';
	import { initializeImageZoom } from '$lib/imageZoom';
	import type { ArticlePageData } from '$lib/types';

	interface Props {
		data: ArticlePageData;
	}

	let { data }: Props = $props();

	let article = $derived(data.article);
	let content = $derived(data.content);
	let markdown = $derived(data.markdown);
	let loading = $derived(data.loading);
	let error = $derived(data.error);
	let contentLoaded = $derived(!loading && !!content);
	let showSkeleton = $derived(!error && !contentLoaded);

	const isDesktop = mediaQuery('(min-width: 1024px)');
	let drawerOpen = $state(false);

	function downloadMarkdown() {
		if (!markdown || !article) return;

		const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = `${article.title.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.md`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	}

	onMount(() => {
		if (contentLoaded) {
			initializeCodeCopyButtons();
			initializeLazyIframes();
			initializeImageZoom();
		}
	});
</script>

<svelte:head>
	<title>{error ? 'Freedium' : data?.article?.title || 'Freedium'} - Freedium</title>
	<meta name="description" content="Read about the latest updates to UploadThing" />
</svelte:head>

<Header />
<div class="flex flex-col min-h-screen">
	<main class="flex-1 w-full h-full max-w-6xl px-4 py-8 mx-auto">
		<div class="lg:flex lg:space-x-6 lg:justify-center">
			{#if error}
				<div class="p-6 text-center bg-white rounded-lg shadow-lg dark:bg-zinc-900">
					<h1
						class="mb-4 text-2xl font-bold {error.status === 404
							? 'text-amber-600'
							: 'text-red-600'}"
					>
						{error.status === 404 ? 'Article Not Found' : 'Error Loading Article'}
					</h1>
					<p class="text-gray-600 dark:text-gray-400">
						{getErrorMessage(error)}
					</p>
					{#if error.details && import.meta.env.DEV}
						<pre class="p-4 mt-4 overflow-auto text-sm bg-gray-100 dark:bg-zinc-800">
					{error.details}
				</pre>
					{/if}
					<div class="mt-6 space-x-4">
						<a
							href="/"
							class="inline-block px-4 py-2 text-white rounded-md bg-primary hover:bg-primary/90"
						>
							Return Home
						</a>
						<button
							class="inline-block px-4 py-2 border rounded-md border-primary text-primary hover:bg-primary/10"
							onclick={() => window.location.reload()}
						>
							Try Again
						</button>
					</div>
				</div>
			{:else if showSkeleton}
				<div class="grow max-w-[calc(100%-10rem)]">
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
				</div>

				<aside class="mt-7 lg:mt-0 max-w-72 lg:shrink-0">
					<div class="w-full p-4 bg-white rounded-lg shadow-lg dark:bg-zinc-900">
						<Skeleton class="w-32 h-6 mb-4" />
						<div class="space-y-2">
							<Skeleton class="w-full h-4" />
							<Skeleton class="w-full h-4" />
							<Skeleton class="w-3/4 h-4" />
						</div>
					</div>
				</aside>
			{:else}
				{#if article}
				<div class="w-full lg:grow lg:max-w-[calc(100%-18rem)]">
					<article class="overflow-hidden bg-white rounded-lg shadow-lg dark:bg-zinc-900">
						<nav class="flex items-center gap-2 p-4">
							<button
								class="flex items-center justify-center transition bg-white rounded-full shadow-md text-primary hover:text-primary/90 group size-8 shadow-zinc-800/5 ring-1 ring-zinc-900/5 dark:border dark:border-zinc-700/50 dark:bg-zinc-800 dark:ring-0 dark:ring-white/10 dark:hover:border-zinc-700 dark:hover:ring-white/20"
								onclick={() => window.history.back()}
							>
								<HeroiconsArrowLeft20Solid class="size-6" />
							</button>
							{#if article.url}
								<a href={article.url} class="ml-auto font-bold text-primary hover:text-primary/90">
									Original article
								</a>
							{/if}
						</nav>
						{#if article.postImage}
							<ImageZoom
								src={article.postImage}
								alt="Post cover image"
								class="object-cover w-full h-auto min-h-96"
							/>
						{/if}
						<header class="p-6 bg-gray-50 dark:bg-zinc-800">
							<p class="mb-2 text-gray-600 dark:text-gray-400">{formatDate(article.date)}</p>
							<h1 class="mb-4 text-4xl font-bold text-gray-900 dark:text-white">{article.title}</h1>
							<div class="flex items-center">
								<img src={article.author.avatar} alt="" class="w-12 h-12 mr-4 rounded-full" />
								<div>
									<p class="font-semibold text-gray-900 dark:text-white">{article.author.name}</p>
									<p class="text-gray-600 dark:text-gray-400">{article.author.role}</p>
								</div>
							</div>
						</header>

						<div class="p-6 {article.postImage ? '' : 'pt-0'} dark:text-gray-300">
							<div class="prose max-w-none prose-external-links">
								{#if content}
									{@html content}
								{:else}
									<p>Error loading content</p>
								{/if}
							</div>
						</div>
					</article>
				</div>

				{#if $isDesktop}
					<aside class="w-full mt-7 lg:mt-0 max-w-64" aria-labelledby="toc-heading">
						<div class="sticky top-12">
							<nav class="w-full p-4 bg-white rounded-lg shadow-lg dark:bg-zinc-900">
								<h2 id="toc-heading" class="mb-4 text-xl font-semibold text-primary">Contents</h2>
								{#if article.tableOfContents && article.tableOfContents.length > 0}
									<ul class="space-y-1">
										{#each article.tableOfContents as item}
											<li>
												<a
													href={`#${item.id}`}
													class="block px-2 py-1.5 text-sm text-zinc-600 hover:text-zinc-900 dark:text-gray-100 dark:hover:text-white hover:bg-accent rounded-md text-wrap break-words"
												>
													{item.title}
												</a>
											</li>
										{/each}
									</ul>
								{:else}
									<p class="italic text-zinc-600 dark:text-gray-400">
										No table of contents available
									</p>
								{/if}
							</nav>
							<div class="mt-4">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger>
										{#snippet child({ props })}
											<button
												{...props}
												class="flex items-center justify-between w-full px-4 py-2 text-sm text-primary bg-gray-50 rounded-lg cursor-pointer select-none dark:bg-zinc-800 hover:bg-gray-100 dark:hover:bg-zinc-700"
											>
												<span>Download article</span>
												<HeroiconsChevronDown20Solid class="size-4" />
											</button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content class="w-56" side="bottom" align="start">
										<DropdownMenu.Item>
											<HeroiconsDocumentArrowDown20Solid class="size-4 text-red-500" />
											Download as PDF
										</DropdownMenu.Item>
										<DropdownMenu.Item onclick={downloadMarkdown}>
											<HeroiconsDocumentText20Solid class="size-4 text-blue-500" />
											Download as Markdown
										</DropdownMenu.Item>
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</div>
						</div>
					</aside>
				{:else}
					{#if article.tableOfContents && article.tableOfContents.length > 0}
						<Drawer.Root bind:open={drawerOpen}>
							<Drawer.Trigger
								class="fixed z-50 flex items-center justify-center transition shadow-lg bottom-6 right-6 bg-primary text-white rounded-full size-14 hover:bg-primary/90 shadow-zinc-800/20 ring-1 ring-primary/20"
							>
								<HeroiconsBars320Solid class="size-6" />
							</Drawer.Trigger>
						<Drawer.Content class="max-h-[85dvh] flex flex-col">
							<Drawer.Header class="text-left">
								<Drawer.Title class="text-xl font-semibold text-primary">Contents</Drawer.Title>
							</Drawer.Header>
							<div class="flex-1 px-4 pb-4 overflow-y-auto">
								{#if article.tableOfContents && article.tableOfContents.length > 0}
									<ul class="space-y-1">
										{#each article.tableOfContents as item}
											<li>
												<a
													href={`#${item.id}`}
													onclick={() => drawerOpen = false}
													class="block px-3 py-2.5 text-base text-zinc-600 hover:text-zinc-900 dark:text-gray-100 dark:hover:text-white hover:bg-accent rounded-md text-wrap break-words"
												>
													{item.title}
												</a>
											</li>
										{/each}
									</ul>
								{:else}
									<p class="italic text-zinc-600 dark:text-gray-400">
										No table of contents available
									</p>
								{/if}
								<div class="mt-6">
									<DropdownMenu.Root>
										<DropdownMenu.Trigger>
											{#snippet child({ props })}
												<button
													{...props}
													class="flex items-center justify-between w-full px-4 py-3 text-base text-primary bg-gray-50 rounded-lg cursor-pointer select-none dark:bg-zinc-800 hover:bg-gray-100 dark:hover:bg-zinc-700"
												>
													<span>Download article</span>
													<HeroiconsChevronDown20Solid class="size-5" />
												</button>
											{/snippet}
										</DropdownMenu.Trigger>
										<DropdownMenu.Content class="w-56" side="bottom" align="start">
											<DropdownMenu.Item>
												<HeroiconsDocumentArrowDown20Solid class="size-4 text-red-500" />
												Download as PDF
											</DropdownMenu.Item>
											<DropdownMenu.Item onclick={downloadMarkdown}>
												<HeroiconsDocumentText20Solid class="size-4 text-blue-500" />
												Download as Markdown
											</DropdownMenu.Item>
										</DropdownMenu.Content>
									</DropdownMenu.Root>
								</div>
							</div>
						</Drawer.Content>
					</Drawer.Root>
					{/if}
				{/if}
				{/if}
			{/if}
		</div>
	</main>
	<Footer />
</div>
