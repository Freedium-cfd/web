<script lang="ts">
	import { navigating } from '$app/stores';
	import { fade } from 'svelte/transition';
	import { writable } from 'svelte/store';

	const MIN_DURATION = 400;
	const isVisible = writable(false);

	$: {
		if ($navigating) {
			$isVisible = true;
		} else {
			setTimeout(() => {
				$isVisible = false;
			}, MIN_DURATION);
		}
	}
</script>

{#if $isVisible}
	<div class="fixed inset-0 z-40 bg-black/30 dark:bg-black/40" transition:fade={{ duration: 300 }}>
		<div class="fixed z-50 top-4 right-4"></div>
	</div>
{/if}
