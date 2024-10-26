<script>
	import Header from '$lib/elements/Header.svelte';
	import SvelteMarkdown from 'svelte-markdown';
	import { formatDate } from '$lib/utils/dateFormatter';
	import { onMount } from 'svelte';
	import Icon from '@iconify/svelte';
	import ImageZoom from '$lib/elements/ImageZoom.svelte';

	let data = {
		title: 'UploadThing is 5x Faster',
		date: '2024-09-13T12:00:00Z',
		author: {
			name: 'Theo Browne',
			role: 'CEO @ Ping Labs',
			avatar: 'https://picsum.photos/seed/post1/400/300'
		},
		postImage: 'https://picsum.photos/seed/postimage/1200/600', // This can now be undefined or null
		content: `
## V7 Is Here!

This release has been an absurd amount of work. So proud of the team and what we've built. Huge thanks to [Julius](#) and [Mark](#) for making this happen.

It is so, so hard to not go straight into the nerdy details, but the whole point of UploadThing is that you don't need to know ANY of those details. With that in mind, here's what's relevant for most of y'all:

- UploadThing is now *way* faster
- Uploads can be paused and resumed seamlessly (huge for users on bad internet connections)
- More details...

## Revolutionary Features

We've completely overhauled our backend infrastructure to bring you unparalleled performance. Our new distributed processing system can handle millions of concurrent uploads without breaking a sweat.

### AI-Powered Optimization

UploadThing now leverages cutting-edge machine learning algorithms to optimize your uploads in real-time. Whether you're uploading images, videos, or documents, our AI will automatically adjust compression and encoding settings to give you the best possible quality at the smallest file size.

## Security Enhancements

We've implemented state-of-the-art encryption protocols to ensure your data remains safe and secure throughout the entire upload process. Our new zero-knowledge architecture means that even we can't access your files without your explicit permission.

### Compliance and Regulations

UploadThing is now fully compliant with GDPR, CCPA, and other major data protection regulations worldwide. We've also obtained ISO 27001 certification, demonstrating our commitment to information security management.

## Future Roadmap

We're not stopping here. Our team is already hard at work on the next big update. Here's a sneak peek of what's coming:

- Quantum-resistant encryption for future-proof security
- Integration with major cloud storage providers for seamless file management
- Advanced analytics dashboard for enterprise users
- Support for emerging file formats and codecs

Stay tuned for more exciting updates as we continue to revolutionize the world of file uploads!
    `,
		tableOfContents: [
			{ id: 'v7-is-here', title: 'V7 Is Here!' },
			{ id: 'benchmarks', title: 'Benchmarks' },
			{ id: 'the-road-to-v7', title: 'The Road To V7' },
			{ id: 'uploadthing-has-served', title: 'UploadThing Has Served...' },
			{ id: 'and-were-just-getting-started', title: "...and we're just getting started" }
		]
	};
	let contentLoaded = false;

	onMount(() => {
		setTimeout(() => {
			contentLoaded = true;
		}, 500);
	});

	async function saveAsPDF() {
		const response = await fetch(`/generate-pdf?path=${encodeURIComponent(window.location.pathname)}`);
		const blob = await response.blob();
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${data.title}.pdf`;
		document.body.appendChild(a);
		a.click();
		a.remove();
		window.URL.revokeObjectURL(url);
	}
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
			<Icon icon="heroicons:arrow-left-20-solid" class="size-6" />
		</a>
		<a href="/" class="font-bold text-primary hover:text-primary/90"> Original article</a>
	</nav>

	<div class="lg:flex lg:space-x-8">
		<article class="flex-grow overflow-hidden bg-white rounded-lg shadow-lg">
			{#if data.postImage}
				<ImageZoom
					src={data.postImage}
					alt="Post cover image"
					class="object-cover w-full h-auto max-h-96"
				/>
			{/if}
			<header class="p-6 bg-gray-50">
				<p class="mb-2 text-gray-600">{formatDate(data.date)}</p>
				<h1 class="mb-4 text-4xl font-bold text-gray-900">{data.title}</h1>
				<div class="flex items-center">
					<img src={data.author.avatar} alt="" class="w-12 h-12 mr-4 rounded-full" />
					<div>
						<p class="font-semibold text-gray-900">{data.author.name}</p>
						<p class="text-gray-600">{data.author.role}</p>
					</div>
				</div>
			</header>

			<div class="p-6 {data.postImage ? '' : 'pt-0'}">
				<div class="prose max-w-none">
					{#if contentLoaded}
						<SvelteMarkdown source={data.content} />
					{:else}
						<p>Loading content...</p>
					{/if}
				</div>
			</div>
			<div class="p-6">
				<button on:click={saveAsPDF} class="px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600">
					Save as PDF
				</button>
			</div>
		</article>

		<aside class="order-first mt-7 lg:mt-0 lg:min-w-80 lg:order-none">
			<nav
				aria-labelledby="toc-heading"
				class="w-full p-4 bg-white rounded-lg shadow-lg lg:sticky lg:top-36"
			>
				<h2 id="toc-heading" class="mb-4 text-xl font-semibold text-gray-900">Contents</h2>
				{#if data.tableOfContents && data.tableOfContents.length > 0}
					<ul class="space-y-2">
						{#each data.tableOfContents as item}
							<li>
								<a href={`#${item.id}`} class="transition-colors text-zinc-800 hover:text-zinc-900">
									{item.title}
								</a>
							</li>
						{/each}
					</ul>
				{:else}
					<p>No table of contents available</p>
				{/if}
			</nav>
		</aside>
	</div>
</main>

<style lang="postcss">
	:global(h2) {
		@apply font-bold font-sans break-normal text-gray-900 dark:text-gray-100 md:text-2xl;
	}

	:global(*:not(:first-child) + h2) {
		@apply pt-12;
	}

	:global(.prose p) {
		@apply leading-8 mt-7;
	}

	:global(.prose h3 + p),
	:global(.prose h4 + p) {
		@apply mt-3;
	}
</style>
