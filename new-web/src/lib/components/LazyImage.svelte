<script lang="ts">
	import { onMount } from 'svelte';
	import Skeleton from '$lib/components/ui/skeleton/skeleton.svelte';

	interface Props {
		src: string;
		alt: string;
		class?: string;
		width?: number | string;
		height?: number | string;
		loading?: 'lazy' | 'eager';
		decoding?: 'async' | 'sync' | 'auto';
		fetchpriority?: 'high' | 'low' | 'auto';
		rootMargin?: string;
		threshold?: number | number[];
		once?: boolean;
		placeholderClass?: string;
	}

	let {
		src,
		alt,
		class: className = '',
		width,
		height,
		loading = 'lazy',
		decoding = 'async',
		fetchpriority = 'auto',
		rootMargin = '200px',
		threshold = 0,
		once = true,
		placeholderClass = ''
	}: Props = $props();

	let containerRef = $state<HTMLElement>();
	let imageLoaded = $state(false);
	let imageError = $state(false);
	let shouldLoad = $state(false);

	onMount(() => {
		if (!containerRef) return;

		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting) {
						shouldLoad = true;
						if (once) {
							observer.disconnect();
						}
					} else if (!once) {
						shouldLoad = false;
					}
				}
			},
			{
				rootMargin,
				threshold
			}
		);

		observer.observe(containerRef);

		return () => {
			observer.disconnect();
		};
	});

	function handleLoad() {
		imageLoaded = true;
	}

	function handleError() {
		imageError = true;
		imageLoaded = true;
	}
</script>

<div
	bind:this={containerRef}
	class="relative overflow-hidden {className}"
	style:width={typeof width === 'number' ? `${width}px` : width}
	style:height={typeof height === 'number' ? `${height}px` : height}
>
	{#if !imageLoaded && !imageError}
		<Skeleton class="absolute inset-0 w-full h-full {placeholderClass}" />
	{/if}

	{#if shouldLoad}
		<img
			{src}
			{alt}
			{width}
			{height}
			{loading}
			{decoding}
			{fetchpriority}
			class="w-full h-full object-cover transition-opacity duration-300 {imageLoaded
				? 'opacity-100'
				: 'opacity-0'}"
			onload={handleLoad}
			onerror={handleError}
		/>
	{/if}

	{#if imageError}
		<div
			class="absolute inset-0 flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 text-zinc-400"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="size-8"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="1.5"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
				/>
			</svg>
		</div>
	{/if}
</div>
