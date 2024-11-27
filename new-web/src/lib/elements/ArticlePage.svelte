<script>
	import Header from '$lib/elements/Header.svelte';
	import { formatDate } from '$lib/utils/dateFormatter';
	import { onMount } from 'svelte';
	import ImageZoom from '$lib/elements/ImageZoom.svelte';
	import Skeleton from '$lib/components/ui/skeleton/skeleton.svelte';
	import Footer from '$lib/elements/Footer.svelte';

	let data = {
		title: 'UploadThing is 5x Faster',
		date: '2024-09-13T12:00:00Z',
		author: {
			name: 'Theo Browne',
			role: 'CEO @ Ping Labs',
			avatar: 'https://picsum.photos/seed/post1/400/300'
		},
		postImage: 'https://picsum.photos/seed/postimage/1200/600', // This can now be undefined or null,
		tableOfContents: [
			{ id: 'v7-is-here', title: 'V7 Is Here!' },
			{ id: 'benchmarks', title: 'Benchmarks' },
			{ id: 'the-road-to-v7', title: 'The Road To V7' },
			{ id: 'uploadthing-has-served', title: 'UploadThing Has Served...' },
			{ id: 'and-were-just-getting-started', title: "...and we're just getting started" }
		]
	};
	let contentLoaded = false;
	let compiledContent = '';

	onMount(async () => {
		try {
			const transformed = await import('../test/blog01.md');
			compiledContent = transformed.default;
			contentLoaded = true;
		} catch (error) {
			console.error('Error compiling markdown:', error);
			contentLoaded = true;
		}
	});
</script>

<svelte:head>
	<title>{data.title} - Freedium</title>
	<meta name="description" content="Read about the latest updates to UploadThing" />
</svelte:head>

<Header />

<main class="max-w-5xl px-4 py-8 mx-auto">
	<nav class="flex items-center justify-between gap-2 mb-4 text-center">
		<a
			href="/"
			class="flex items-center justify-center transition bg-white rounded-full shadow-md text-primary hover:text-primary/90 group size-8 shadow-zinc-800/5 ring-1 ring-zinc-900/5 dark:border dark:border-zinc-700/50 dark:bg-zinc-800 dark:ring-0 dark:ring-white/10 dark:hover:border-zinc-700 dark:hover:ring-white/20"
		>
			<span class="icon-[heroicons--arrow-left-20-solid] size-6" />
		</a>
		<a href="/" class="font-bold text-primary hover:text-primary/90"> Original article</a>
	</nav>

	<div class="lg:flex lg:space-x-8">
		<article class="flex-grow overflow-hidden bg-white rounded-lg shadow-lg dark:bg-zinc-900">
			{#if !contentLoaded}
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
			{:else}
				{#if data.postImage}
					<ImageZoom
						src={data.postImage}
						alt="Post cover image"
						class="object-cover w-full h-auto max-h-96"
					/>
				{/if}
				<header class="p-6 bg-gray-50 dark:bg-zinc-800">
					<p class="mb-2 text-gray-600 dark:text-gray-400">{formatDate(data.date)}</p>
					<h1 class="mb-4 text-4xl font-bold text-gray-900 dark:text-white">{data.title}</h1>
					<div class="flex items-center">
						<img src={data.author.avatar} alt="" class="w-12 h-12 mr-4 rounded-full" />
						<div>
							<p class="font-semibold text-gray-900 dark:text-white">{data.author.name}</p>
							<p class="text-gray-600 dark:text-gray-400">{data.author.role}</p>
						</div>
					</div>
				</header>

				<div class="p-6 {data.postImage ? '' : 'pt-0'} dark:text-gray-300">
					<div class="prose max-w-none">
						{#if contentLoaded}
							{#if compiledContent}
								<svelte:component this={compiledContent} />
							{:else}
								<p>Error loading content</p>
							{/if}
						{:else}
							<p>Loading content...</p>
						{/if}
					</div>
				</div>
			{/if}
		</article>

		<aside class="order-first mt-7 lg:mt-0 lg:min-w-80 lg:order-none">
			{#if !contentLoaded}
				<div class="w-full p-4 bg-white rounded-lg shadow-lg dark:bg-zinc-900">
					<Skeleton class="w-32 h-6 mb-4" />
					<div class="space-y-2">
						<Skeleton class="w-full h-4" />
						<Skeleton class="w-full h-4" />
						<Skeleton class="w-3/4 h-4" />
					</div>
				</div>
			{:else}
				<nav
					aria-labelledby="toc-heading"
					class="w-full p-4 bg-white rounded-lg shadow-lg dark:bg-zinc-900 lg:sticky lg:top-36"
				>
					<h2 id="toc-heading" class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
						Contents
					</h2>
					{#if data.tableOfContents && data.tableOfContents.length > 0}
						<ul class="space-y-2">
							{#each data.tableOfContents as item}
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
			{/if}
		</aside>
	</div>
</main>

<Footer />

<style lang="postcss">
	/* Headings */
	:global(.prose h1) {
		@apply text-4xl font-bold text-gray-900 dark:text-gray-100 mt-12 mb-6;
	}

	:global(.prose h2) {
		@apply text-3xl font-bold text-gray-900 dark:text-gray-100 mt-12 mb-4;
	}

	:global(.prose h3) {
		@apply text-2xl font-bold text-gray-900 dark:text-gray-100 mt-8 mb-3;
	}

	:global(.prose h4) {
		@apply text-xl font-bold text-gray-900 dark:text-gray-100 mt-6 mb-2;
	}

	:global(.prose h5) {
		@apply text-lg font-bold text-gray-900 dark:text-gray-100 mt-4 mb-2;
	}

	:global(.prose h6) {
		@apply text-base font-bold text-gray-900 dark:text-gray-100 mt-4 mb-2;
	}

	/* Paragraphs and spacing */
	:global(.prose p) {
		@apply text-gray-700 dark:text-gray-300 leading-7 mt-4;
	}

	:global(.prose > *:first-child) {
		@apply mt-0;
	}

	/* Lists */
	:global(.prose ul) {
		@apply list-disc list-outside ml-6 mt-4 space-y-2;
	}

	:global(.prose ol) {
		@apply list-decimal list-outside ml-6 mt-4 space-y-2;
	}

	:global(.prose li) {
		@apply text-gray-700 dark:text-gray-300 leading-7;
	}

	/* Blockquotes */
	:global(.prose blockquote) {
		@apply border-l-4 border-gray-300 dark:border-gray-700 pl-4 italic my-6;
	}

	/* Code blocks */
	:global(.prose pre) {
		@apply rounded-lg p-4 my-6 overflow-x-auto;
	}

	:global(.prose code:not(.shiki code)) {
		@apply px-1.5 py-0.5 rounded text-sm font-mono bg-gray-200 dark:bg-zinc-700;
	}

	:global(.prose pre code) {
		@apply bg-transparent p-0 text-sm leading-relaxed;
	}

	/* Tables */
	:global(.prose table) {
		@apply w-full border-collapse my-6;
	}

	:global(.prose th) {
		@apply border border-gray-300 dark:border-gray-700 px-4 py-2 bg-gray-100 dark:bg-zinc-800 text-left;
	}

	:global(.prose td) {
		@apply border border-gray-300 dark:border-gray-700 px-4 py-2;
	}

	/* Links */
	:global(.prose a) {
		@apply text-primary hover:text-primary/90 underline decoration-primary/30 hover:decoration-primary/50;
	}

	:global(.prose a::after) {
		content: '';
		@apply icon-[heroicons-outline--external-link] inline-block ml-1 w-3.5 h-3.5 align-text-bottom;
	}

	/* Horizontal rule */
	:global(.prose hr) {
		@apply border-gray-200 dark:border-gray-700 my-8;
	}

	/* Images */
	:global(.prose img) {
		@apply rounded-lg my-6 mx-auto;
	}

	/* Inline elements */
	:global(.prose strong) {
		@apply font-bold text-gray-900 dark:text-gray-100;
	}

	:global(.prose em) {
		@apply italic;
	}

	:global(.prose del) {
		@apply line-through;
	}

	/* Definition lists */
	:global(.prose dl) {
		@apply mt-4;
	}

	:global(.prose dt) {
		@apply font-bold text-gray-900 dark:text-gray-100;
	}

	:global(.prose dd) {
		@apply ml-4 mt-2;
	}

	/* Nested lists spacing */
	:global(.prose li > ul),
	:global(.prose li > ol) {
		@apply mt-2 mb-2;
	}

	/* Code block filename */
	:global(.prose .filename) {
		@apply text-sm text-gray-500 dark:text-gray-400 -mb-2 mt-6;
	}

	/* Summary blocks */
	:global(.prose summary) {
		@apply text-gray-700 dark:text-gray-300 leading-7 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 select-none;
	}

	:global(.prose details) {
		@apply my-4 p-4 rounded-lg bg-gray-50 dark:bg-zinc-800;
	}

	:global(.prose details[open] summary) {
		@apply mb-3;
	}

	/* Aside blocks */
	:global(.prose aside) {
		@apply my-6 p-4 rounded-lg border-l-4 border-primary bg-primary/5;
	}

	:global(.prose aside p) {
		@apply m-0;
	}

	/* Mark blocks */
	:global(.prose mark) {
		@apply bg-primary/20 text-primary px-1.5 py-0.5 rounded;
	}

	/* Keyboard blocks */
	:global(.prose kbd) {
		@apply px-2 py-1.5 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded-lg dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500;
	}

	/* Mixtape embeds */
	:global(.prose .mixtape-embed) {
		@apply items-center p-2 overflow-hidden border border-gray-300 mt-7;
	}

	:global(.prose .mixtape-content) {
		@apply flex flex-row justify-between p-2 overflow-hidden;
	}

	:global(.prose .mixtape-text) {
		@apply flex flex-col justify-center p-2;
	}

	:global(.prose .mixtape-text h2) {
		@apply text-base font-bold text-black dark:text-gray-100;
	}

	:global(.prose .mixtape-description) {
		@apply block mt-2;
	}

	:global(.prose .mixtape-description h3) {
		@apply text-sm text-gray-700;
	}

	:global(.prose .mixtape-site) {
		@apply mt-5;
	}

	:global(.prose .mixtape-site p) {
		@apply text-xs text-gray-700;
	}

	:global(.prose .mixtape-image) {
		@apply relative flex h-40 flex-row w-60;
	}

	:global(.prose .mixtape-image-inner) {
		@apply absolute inset-0 bg-center bg-cover;
	}
</style>
