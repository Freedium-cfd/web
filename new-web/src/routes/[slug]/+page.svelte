<script lang="ts">
	import { onMount } from 'svelte';
import { initializeCodeCopyButtons } from '$lib/codeCopy';

onMount(() => {
  initializeCodeCopyButtons();
});
	import ArticlePage from '$lib/elements/ArticlePage.svelte';

	export let data;
</script>

<ArticlePage {data} />
