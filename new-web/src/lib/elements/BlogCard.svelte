<script lang="ts">
	import Icon from '@iconify/svelte';
	const sizes = ['small', 'medium', 'large'];

	export let id: number;
	export let title: string;
	export let excerpt: string;
	export let imageUrl: string;
	export let bottomImageUrl: string | null = null;
	export let size: 'small' | 'medium' | 'large' | null = randomSize();
	export let readingTime: string;
	export let publishedAt: string;
	export let collection: { name: string; avatarId: string } | null = null;
	export let creator: string;
	export let slug: string;

	const sizeClasses = {
		small: 'w-full',
		medium: 'w-full',
		large: 'w-full'
	};

	const imageClasses = {
		small: 'h-32',
		medium: 'h-48',
		large: 'h-64'
	};

	function randomSize(): 'small' | 'medium' | 'large' {
		return sizes[Math.floor(Math.random() * sizes.length)] as 'small' | 'medium' | 'large';
	}
</script>

<a href={`/${slug}`} class="block no-underline">
	<div
		class={`border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg shadow-md overflow-hidden ${sizeClasses[size]} transition-transform duration-300 ease-in-out hover:scale-105 mb-4`}
	>
		{#if imageUrl}
			<img src={imageUrl} alt={title} class={`w-full object-cover ${imageClasses[size]}`} />
		{/if}
		<div class="p-4">
			<h2 class="mb-2 text-xl font-bold text-zinc-900 dark:text-zinc-100">{title}</h2>
			<p class="text-gray-600 dark:text-gray-300">{excerpt}</p>

			<div class="flex flex-wrap items-center mt-2 space-x-2 text-sm text-gray-500 dark:text-white">
				<Icon icon="mage:medium" class="w-4 h-4 mr-1" />
				{#if collection}
					<div class="flex items-center">
						<img
							src="https://miro.medium.com/v2/resize:fill:48:48/{collection.avatarId}"
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
		{#if bottomImageUrl}
			<img src={bottomImageUrl} alt={title} class={`w-full object-cover ${imageClasses[size]}`} />
		{/if}
	</div>
</a>
