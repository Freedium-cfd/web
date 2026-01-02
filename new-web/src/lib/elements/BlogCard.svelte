<script lang="ts">
	import MageMedium from '~icons/mage/medium';
	import LazyImage from '$lib/components/LazyImage.svelte';
	import type { BlogPost, BlogPostSize } from '$lib/types';

	const sizes: BlogPostSize[] = ['small', 'medium', 'large'];

	function randomSize(): BlogPostSize {
		return sizes[Math.floor(Math.random() * sizes.length)];
	}

	type Props = BlogPost;

	let {
		id,
		title,
		excerpt,
		imageUrl = '',
		bottomImageUrl = null,
		size = randomSize(),
		readingTime,
		publishedAt,
		collection = null,
		creator,
		slug
	}: Props = $props();

	const sizeClasses: Record<string, string> = {
		small: 'w-full',
		medium: 'w-full',
		large: 'w-full',
		null: 'w-full'
	};

	const imageHeights: Record<string, string> = {
		small: '128px',
		medium: '192px',
		large: '256px',
		null: '128px'
	};
</script>

<a href={`/${slug}`} class="block no-underline">
	<div
		class={`border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg shadow-md overflow-hidden ${sizeClasses[size ?? 'null']} transition-transform duration-300 ease-in-out hover:scale-105 mb-4`}
	>
		{#if imageUrl}
			<LazyImage
				src={imageUrl}
				alt={title}
				class="w-full"
				width="100%"
				height={imageHeights[size ?? 'null']}
				rootMargin="100px"
			/>
		{/if}
		<div class="p-4">
			<h2 class="mb-2 text-xl font-bold text-zinc-900 dark:text-zinc-100">{title}</h2>
			<p class="text-gray-600 dark:text-gray-300">{excerpt}</p>
		</div>
		{#if bottomImageUrl}
			<LazyImage
				src={bottomImageUrl}
				alt={title}
				class="w-full"
				width="100%"
				height={imageHeights[size ?? 'null']}
				rootMargin="100px"
			/>
		{/if}
		<div
			class="flex flex-wrap items-center p-4 mt-2 space-x-2 text-sm text-gray-500 dark:text-white"
		>
			<MageMedium class="size-4 mr-1" />
			{#if collection}
				<div class="flex items-center">
					<img
						src="https://miro.medium.com/v2/resize:fill:48:48/{collection.avatarId}"
						referrerpolicy="no-referrer"
						alt={collection.name.charAt(0)}
						loading="eager"
						class="w-4 h-4 mr-1 rounded-full no-lightense"
					/>
					<p>{collection.name}</p>
				</div>
				<span>·</span>
			{/if}
			<span>{creator}</span>
			<span>·</span>
			<span>~{readingTime} min read</span>
			<span class="md:inline">·</span>
			<span>{publishedAt}</span>
		</div>
	</div>
</a>
