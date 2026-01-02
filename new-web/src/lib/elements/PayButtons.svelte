<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import type { PayButtonProps } from '$lib/types';

	let { name, url, icon: Icon, showLabel = true }: PayButtonProps = $props();
</script>

<Button variant="ghost" class={showLabel ? 'h-auto px-3 py-2' : 'size-9 p-0'}>
	<a
		class="flex items-center gap-2 transition-colors text-zinc-600 dark:text-zinc-300 hover:text-primary dark:hover:text-primary"
		href={url}
		target="_blank"
		rel="noopener noreferrer"
		title={name}
	>
		<Icon class="size-5 shrink-0" />
		{#if showLabel}
			<span class="text-sm font-medium">{name}</span>
		{/if}
	</a>
</Button>
