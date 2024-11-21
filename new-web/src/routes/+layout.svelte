<script lang="ts">
	import '../app.css';
	import { Toaster } from '$lib/components/ui/sonner';
</script>

<Toaster position="top-right" expand={true} />
<slot />
