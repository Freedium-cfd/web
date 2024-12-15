<script>
	import { page } from '$app/stores';
	import Header from '$lib/elements/Header.svelte';
	import { formatDate } from '$lib/utils/dateFormatter';
	import ImageZoom from '$lib/elements/ImageZoom.svelte';
	import Skeleton from '$lib/components/ui/skeleton/skeleton.svelte';
	import Footer from '$lib/elements/Footer.svelte';
	import './ArticlePage.css';

	export let data;

	$: ({ article, content, loading } = data);
	$: contentLoaded = !loading && !!content;
	$: error = data.error;
	$: showSkeleton = !error && !contentLoaded;

	function getErrorMessage(error) {
		if (!error) return '';

		switch (error.code) {
			case 'ARTICLE_NOT_FOUND':
				return "We couldn't find the article you're looking for.";
			case 'RENDER_ERROR':
				return 'There was a problem preparing this article.';
			case 'COMPILE_ERROR':
				return 'There was a problem processing the article content.';
			default:
				return error.message || 'An unexpected error occurred.';
		}
	}
</script>

<svelte:head>
	<title>{error ? 'Freedium' : data?.article?.title || 'Freedium'} - Freedium</title>
	<meta name="description" content="Read about the latest updates to UploadThing" />
</svelte:head>

<Header />
<div class="flex flex-col min-h-screen">
	<main class="flex-1 w-full h-full max-w-5xl px-4 py-8">
		<nav class="flex items-center justify-between gap-2 mb-4 text-center">
			<a
				href="/"
				class="flex items-center justify-center transition bg-white rounded-full shadow-md text-primary hover:text-primary/90 group size-8 shadow-zinc-800/5 ring-1 ring-zinc-900/5 dark:border dark:border-zinc-700/50 dark:bg-zinc-800 dark:ring-0 dark:ring-white/10 dark:hover:border-zinc-700 dark:hover:ring-white/20"
			>
				<span class="icon-[heroicons--arrow-left-20-solid] size-6" />
			</a>
			{#if article?.url}
				<a href={article.url} class="font-bold text-primary hover:text-primary/90">
					Original article
				</a>
			{/if}
		</nav>

		{#if error}
			<div class="p-6 text-center bg-white rounded-lg shadow-lg dark:bg-zinc-900">
				<h1
					class="mb-4 text-2xl font-bold {error.status === 404 ? 'text-amber-600' : 'text-red-600'}"
				>
					{error.status === 404 ? 'Article Not Found' : 'Error Loading Article'}
				</h1>
				<p class="text-gray-600 dark:text-gray-400">
					{getErrorMessage(error)}
				</p>
				{#if error.details && process.env.NODE_ENV === 'development'}
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
						on:click={() => window.location.reload()}
					>
						Try Again
					</button>
				</div>
			</div>
		{:else if showSkeleton}
			<div class="lg:flex lg:space-x-8">
				<article class="flex-grow overflow-hidden bg-white rounded-lg shadow-lg dark:bg-zinc-900">
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

				<aside class="order-first mt-7 lg:mt-0 lg:min-w-80 lg:order-none">
					<div class="w-full p-4 bg-white rounded-lg shadow-lg dark:bg-zinc-900">
						<Skeleton class="w-32 h-6 mb-4" />
						<div class="space-y-2">
							<Skeleton class="w-full h-4" />
							<Skeleton class="w-full h-4" />
							<Skeleton class="w-3/4 h-4" />
						</div>
					</div>
				</aside>
			</div>
		{:else}
			<div class="lg:flex lg:space-x-8">
				<article class="flex-grow overflow-hidden bg-white rounded-lg shadow-lg dark:bg-zinc-900">
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
						<div class="prose max-w-none">
							{#if content}
								{@html content}
							{:else}
								<p>Error loading content</p>
							{/if}
						</div>
					</div>
				</article>

				<aside class="order-first mt-7 lg:mt-0 lg:min-w-80 lg:order-none">
					<nav
						aria-labelledby="toc-heading"
						class="w-full p-4 bg-white rounded-lg shadow-lg dark:bg-zinc-900 lg:sticky lg:top-36"
					>
						<h2 id="toc-heading" class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
							Contents
						</h2>
						{#if article.tableOfContents && article.tableOfContents.length > 0}
							<ul class="space-y-2">
								{#each article.tableOfContents as item}
									<li>
										<a
											href={`#${item.id}`}
											class="transition-colors text-zinc-800 hover:text-zinc-900 dark:text-gray-300 dark:hover:text-white"
										>
											{item.title}
										</a>
									</li>
								{/each}
							</ul>
						{:else}
							<p class="dark:text-gray-300">No table of contents available</p>
						{/if}
					</nav>
				</aside>
			</div>
		{/if}
	</main>

	<Footer />
</div>
