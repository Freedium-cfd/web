<script lang="ts">
	import { toggleMode, mode } from 'mode-watcher';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';

	const isDark = $derived(mode.current === 'dark');
</script>

<button
	onclick={toggleMode}
	class="relative inline-flex min-h-[36px] min-w-[60px] cursor-pointer items-center rounded-full bg-gray-200 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 data-[state=checked]:bg-primary dark:bg-gray-700"
	data-state={isDark ? 'checked' : 'unchecked'}
	role="switch"
	aria-checked={isDark}
>
	<span
		class="pointer-events-none flex h-[30px] w-[30px] items-center justify-center rounded-full bg-white transition-transform duration-200"
		style:transform={isDark ? 'translateX(24px)' : 'translateX(3px)'}
	>
		{#if !isDark}
			<Sun class="text-gray-600 size-4" />
		{:else}
			<Moon class="text-gray-600 size-4" />
		{/if}
	</span>
</button>
