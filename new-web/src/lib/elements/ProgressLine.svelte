<script lang="ts">
	import { onMount } from 'svelte';

	let progress: HTMLElement;
	let scroll = 0;

	$: if (progress) {
		progress.style.setProperty('--scroll', scroll + '%');
	}

	onMount(() => {
		const updateScroll = () => {
			const h = document.documentElement;
			const b = document.body;
			scroll =
				((h.scrollTop || b.scrollTop) / ((h.scrollHeight || b.scrollHeight) - h.clientHeight)) *
				100;
		};

		window.addEventListener('scroll', updateScroll);
		updateScroll();
		return () => {
			window.removeEventListener('scroll', updateScroll);
		};
	});
</script>

<div
	bind:this={progress}
	id="progress"
	class="top-0 z-20 h-1"
	style="background:linear-gradient(to right, hsl(var(--primary)) var(--scroll), transparent 0)"
/>
