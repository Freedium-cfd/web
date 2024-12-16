<script lang="ts">
	import '../app.css';
	import { Toaster } from '$lib/components/ui/sonner';
	import ProgressOverlay from '$lib/elements/ProgressOverlay.svelte';
</script>

<div class="transition-all duration-200 ease-in-out">
	<ProgressOverlay />
	<Toaster position="top-right" expand={true} />
	<slot />
</div>
