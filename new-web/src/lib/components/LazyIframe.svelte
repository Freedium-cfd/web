<script lang="ts">
	import { onMount } from 'svelte';
	import Skeleton from '$lib/components/ui/skeleton/skeleton.svelte';

	interface Props {
		src: string;
		title?: string;
		class?: string;
		width?: number | string;
		height?: number | string;
		allow?: string;
		allowfullscreen?: boolean;
		rootMargin?: string;
		threshold?: number | number[];
		once?: boolean;
		placeholderClass?: string;
	}

	let {
		src,
		title = '',
		class: className = '',
		width,
		height,
		allow = '',
		allowfullscreen = true,
		rootMargin = '200px',
		threshold = 0,
		once = true,
		placeholderClass = ''
	}: Props = $props();

	let containerRef = $state<HTMLElement>();
	let iframeLoaded = $state(false);
	let iframeError = $state(false);
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
		iframeLoaded = true;
	}

	function handleError() {
		iframeError = true;
		iframeLoaded = true;
	}
</script>

<div
	bind:this={containerRef}
	class="relative overflow-hidden {className}"
	style:width={typeof width === 'number' ? `${width}px` : width}
	style:height={typeof height === 'number' ? `${height}px` : height}
>
	{#if !iframeLoaded && !iframeError}
		<Skeleton class="absolute inset-0 w-full h-full {placeholderClass}" />
	{/if}

	{#if shouldLoad}
		<iframe
			{src}
			{title}
			{width}
			{height}
			{allow}
			{allowfullscreen}
			loading="lazy"
			class="w-full h-full border-0 transition-opacity duration-300 {iframeLoaded
				? 'opacity-100'
				: 'opacity-0'}"
			onload={handleLoad}
			onerror={handleError}
		></iframe>
	{/if}

	{#if iframeError}
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
					d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
				/>
			</svg>
		</div>
	{/if}
</div>
