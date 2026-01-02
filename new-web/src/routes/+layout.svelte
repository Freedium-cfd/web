<script lang="ts">
	import '../app.css';
	import { Toaster } from '$lib/components/ui/sonner';
	import { ModeWatcher } from 'mode-watcher';
	import ProgressOverlay from '$lib/elements/ProgressOverlay.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

<ModeWatcher disableTransitions={false} />
<div class="flex flex-col min-h-screen transition-all duration-200 ease-in-out">
	<ProgressOverlay />
	<Toaster position="top-right" expand={true} />
	{@render children()}
</div>
