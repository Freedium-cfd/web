<script lang="ts">
	import Icon from '@iconify/svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { browser } from '$app/environment';

	let darkMode = true;

	function handleSwitchDarkMode() {
		darkMode = !darkMode;
		localStorage.setItem('theme', darkMode ? 'dark' : 'light');
		darkMode
			? document.documentElement.classList.add('dark')
			: document.documentElement.classList.remove('dark');
	}

	if (browser) {
		if (
			localStorage.theme === 'dark' ||
			(!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
		) {
			document.documentElement.classList.add('dark');
			darkMode = true;
		} else {
			document.documentElement.classList.remove('dark');
			darkMode = false;
		}
	}
</script>

<Button
	class="px-3 text-gray-600 py-7 dark:text-white hover:text-primary dark:hover:text-primary"
	on:click={handleSwitchDarkMode}
	variant="ghost"
>
	<Icon icon={darkMode ? 'heroicons:moon-solid' : 'heroicons:sun-solid'} class="size-5" />
</Button>
