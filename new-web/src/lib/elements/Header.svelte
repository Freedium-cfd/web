<script lang="ts">
	import Advertise from './Advertise.svelte';
	import ProgressLine from './ProgressLine.svelte';
	import ThemeToggle from './ThemeToggle.svelte';
	import ReportProblem from './ReportProblem.svelte';
	import PayButtons from './PayButtons.svelte';
	import ExtensionsButton from './ExtensionsButton.svelte';
	import Icon from '@iconify/svelte';
	import SearchDialog from './SearchDialog.svelte';
	import { Menu } from 'lucide-svelte';

	import { Button } from '$lib/components/ui/button/index.js';

	let isNavOpen = false;

	const toggleNav = () => {
		isNavOpen = !isNavOpen;
	};

	let isSearchOpen = false;
	const toggleSearch = () => {
		isSearchOpen = !isSearchOpen;
	};
</script>

<nav
	id="header"
	class="sticky top-0 z-20 w-full bg-white border-b shadow-sm dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
>
	<Advertise />
	<ProgressLine />

	<div class="container flex items-center justify-between h-16 px-4 mx-auto space-x-2">
		<a class="text-2xl font-bold transition-opacity text-primary hover:opacity-80" href="/"
			>Freedium βeta</a
		>

		<div class="flex-grow max-w-md mx-2">
			<Button
				class="items-center hidden w-full h-8 gap-2 pl-2 pr-3 text-sm transition bg-white rounded-full ui-not-focus-visible:outline-none text-zinc-500 ring-1 ring-zinc-900/10 hover:ring-zinc-900/20 lg:flex dark:bg-white/5 dark:text-zinc-400 dark:ring-inset dark:ring-white/10 dark:hover:ring-white/20"
				on:click={toggleSearch}
			>
				<Icon icon="heroicons:magnifying-glass" />
				Search
			</Button>
		</div>

		<div class="items-center hidden space-x-2 md:flex">
			<Button class="lg:hidden" variant="ghost" size="icon" on:click={toggleSearch}>
				<Icon class="size-5" icon="heroicons:magnifying-glass" />
			</Button>
			<ExtensionsButton />
			<div class="w-px h-6 bg-zinc-300 dark:bg-zinc-700"></div>
			<PayButtons name="Ko-fi" url="https://ko-fi.com/zhymabekroman" icon="teenyicons:cup-solid" />
			<PayButtons
				name="Liberapay"
				url="https://liberapay.com/ZhymabekRoman/"
				icon="simple-icons:liberapay"
			/>
			<!-- <PayButtons name="PayPal" url="" icon="simple-icons:paypal" /> -->
			<div class="w-px h-6 bg-zinc-300 dark:bg-zinc-700"></div>
			<ThemeToggle />
			<ReportProblem />
		</div>

		<div class="flex items-center space-x-2 md:hidden">
			<Button class="lg:hidden" variant="ghost" size="icon" on:click={toggleSearch}>
				<Icon class="size-5" icon="heroicons:magnifying-glass" />
			</Button>
			<ThemeToggle />
			<Button variant="ghost" size="icon" on:click={toggleNav}>
				<Menu />
			</Button>
		</div>
	</div>

	{#if isNavOpen}
		<div
			class="!sticky w-full bg-white border-b shadow-sm md:hidden dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
		>
			<div
				class="sticky z-20 flex flex-wrap items-center justify-center px-4 py-2 mx-auto space-x-2 space-y-2"
			>
				<ReportProblem />
			</div>
		</div>
	{/if}
</nav>

<SearchDialog bind:open={isSearchOpen} />
