<script lang="ts">
	import { onMount } from 'svelte';
	import { initializeCodeCopyButtons } from '$lib/codeCopy';
	import ArticlePage from '$lib/elements/ArticlePage.svelte';

	let { data } = $props();

	onMount(() => {
		if (data.content) {
			initializeCodeCopyButtons();
		}
	});
</script>

<ArticlePage {data} />
