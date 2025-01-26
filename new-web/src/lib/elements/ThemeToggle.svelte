<script lang="ts">
	import { createSwitch } from '@melt-ui/svelte';
	import { browser } from '$app/environment';
	import { Moon, Sun } from 'lucide-svelte';

	const initialChecked = browser
		? localStorage.theme === 'dark' ||
			(!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
		: false;

	const {
		elements: { root, input },
		states: { checked }
	} = createSwitch({
		defaultChecked: initialChecked
	});

	$: if (browser) {
		const isDark = $checked;
		localStorage.setItem('theme', isDark ? 'dark' : 'light');
		isDark
			? document.documentElement.classList.add('dark')
			: document.documentElement.classList.remove('dark');
	}

	if (browser) {
		const isDark =
			localStorage.theme === 'dark' ||
			(!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
		isDark
			? document.documentElement.classList.add('dark')
			: document.documentElement.classList.remove('dark');
	}
</script>

<button
	{...$root}
	use:root
	class="relative inline-flex h-[36px] w-[60px] cursor-pointer items-center rounded-full bg-gray-200 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 data-[state=checked]:bg-primary dark:bg-gray-700"
>
	<span
		class="pointer-events-none flex h-[30px] w-[30px] items-center justify-center rounded-full bg-white transition-transform duration-200"
		style:transform={$checked ? 'translateX(24px)' : 'translateX(3px)'}
	>
		{#if !$checked}
			<Sun class="text-gray-600 size-4" />
		{:else}
			<Moon class="text-gray-600 size-4" />
		{/if}
	</span>
	<input {...$input} use:input type="checkbox" class="sr-only" />
</button>
