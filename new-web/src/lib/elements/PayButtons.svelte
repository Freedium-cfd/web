<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';

	export let name: string;
	export let url: string;
	export let icon: string;
</script>

<Button variant="ghost" class="w-24 px-3 py-7">
	<a
		class="flex flex-col items-center gap-1 transition-colors text-zinc-600 dark:text-zinc-300 hover:text-primary dark:hover:text-primary"
		href={url}
		target="_blank"
		rel="noopener noreferrer"
	>
		<span class={`${icon} size-5`} />
		{name}
	</a>
</Button>
