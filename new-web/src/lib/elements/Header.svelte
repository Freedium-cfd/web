<script lang="ts">
	import ProgressLine from './ProgressLine.svelte';
	import ThemeToggle from './ThemeToggle.svelte';
	import ReportProblem from './ReportProblem.svelte';
	import PayButtons from './PayButtons.svelte';
	import ExtensionsButton from './ExtensionsButton.svelte';
	import SearchDialog from './SearchDialog.svelte';
	import Menu from '@lucide/svelte/icons/menu';
	import X from '@lucide/svelte/icons/x';
	import Search from '@lucide/svelte/icons/search';
	import Plus from '@lucide/svelte/icons/plus';
	import TeenyiconsCupSolid from '~icons/teenyicons/cup-solid';
	import SimpleIconsLiberapay from '~icons/simple-icons/liberapay';
	import SimpleIconsDiscord from '~icons/simple-icons/discord';

	import { Button } from '$lib/components/ui/button/index.js';
	import { onMount } from 'svelte';

	let isNavOpen = $state(false);
	let isSearchOpen = $state(false);
	let isHeaderVisible = $state(true);
	let lastScrollY = $state(0);

	// Handle scroll events
	function handleScroll() {
		const currentScrollY = window.scrollY;
		const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
		const scrollPercentage = (currentScrollY / documentHeight) * 100;

		if (scrollPercentage > 5) {
			isHeaderVisible = lastScrollY > currentScrollY;
		} else {
			isHeaderVisible = true;
		}

		lastScrollY = currentScrollY;
	}

	onMount(() => {
		window.addEventListener('scroll', handleScroll, { passive: true });
		return () => window.removeEventListener('scroll', handleScroll);
	});

	const toggleNav = () => {
		isNavOpen = !isNavOpen;
	};

	const toggleSearch = () => {
		isSearchOpen = !isSearchOpen;
	};
</script>

<nav
	id="header"
	class="sticky top-0 z-20 w-full transition-transform duration-300 border-b shadow-sm bg-white/95 backdrop-blur-sm dark:bg-zinc-900/95 border-zinc-200 dark:border-zinc-800"
	style="transform: translateY({isHeaderVisible ? '0' : '-100%'})"
>
	<ProgressLine />

	<div class="container flex items-center justify-between h-14 px-4 mx-auto">
		<!-- Logo -->
		<a class="text-xl font-bold transition-opacity text-primary hover:opacity-80" href="/">
			Freedium <span class="text-xs font-normal text-zinc-500 dark:text-zinc-400">beta</span>
		</a>

		<!-- Desktop Navigation -->
		<div class="items-center hidden gap-1 md:flex">
			<!-- Search -->
			<Button variant="ghost" size="icon" onclick={toggleSearch} title="Search">
				<Search class="size-5" />
			</Button>

			<!-- Extensions -->
			<ExtensionsButton />

			<div class="w-px h-5 mx-1 bg-zinc-200 dark:bg-zinc-700"></div>

			<!-- Support Links - Icons only -->
			<div class="flex items-center gap-0.5">
				<PayButtons
					name="Ko-fi"
					url="https://ko-fi.com/zhymabekroman"
					icon={TeenyiconsCupSolid}
					showLabel={false}
				/>
				<PayButtons
					name="Liberapay"
					url="https://liberapay.com/ZhymabekRoman/"
					icon={SimpleIconsLiberapay}
					showLabel={false}
				/>
				<PayButtons
					name="Discord"
					url="https://discord.gg/dAxCuG9nYM"
					icon={SimpleIconsDiscord}
					showLabel={false}
				/>
			</div>

			<div class="w-px h-5 mx-1 bg-zinc-200 dark:bg-zinc-700"></div>

			<!-- Theme Toggle -->
			<ThemeToggle />

			<!-- Report Problem -->
			<ReportProblem compact={true} />

			<!-- Primary CTA -->
			<Button size="sm" class="ml-2 gap-1.5">
				<Plus class="size-4" />
				<span>Add Article</span>
			</Button>
		</div>

		<!-- Mobile Navigation -->
		<div class="flex items-center gap-1 md:hidden">
			<Button variant="ghost" size="icon" onclick={toggleSearch} title="Search">
				<Search class="size-5" />
			</Button>
			<ThemeToggle />
			<ReportProblem compact={true} />
			<Button
				variant="ghost"
				size="icon"
				onclick={toggleNav}
				aria-expanded={isNavOpen}
				aria-controls="mobile-menu"
			>
				{#if isNavOpen}
					<X class="size-5" />
				{:else}
					<Menu class="size-5" />
				{/if}
				<span class="sr-only">Toggle menu</span>
			</Button>
		</div>
	</div>

	<!-- Mobile Menu -->
	{#if isNavOpen}
		<div
			id="mobile-menu"
			class="w-full bg-white border-t md:hidden dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
		>
			<div class="flex flex-col gap-2 p-4">
				<!-- Primary CTA -->
				<Button class="w-full gap-2">
					<Plus class="size-4" />
					<span>Add Article</span>
				</Button>

				<!-- Support Section -->
				<div class="pt-2 mt-2 border-t border-zinc-200 dark:border-zinc-700">
					<p class="mb-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">Support Freedium</p>
					<div class="flex flex-wrap gap-2">
						<PayButtons
							name="Ko-fi"
							url="https://ko-fi.com/zhymabekroman"
							icon={TeenyiconsCupSolid}
							showLabel={true}
						/>
						<PayButtons
							name="Liberapay"
							url="https://liberapay.com/ZhymabekRoman/"
							icon={SimpleIconsLiberapay}
							showLabel={true}
						/>
						<PayButtons
							name="Discord"
							url="https://discord.gg/dAxCuG9nYM"
							icon={SimpleIconsDiscord}
							showLabel={true}
						/>
					</div>
				</div>

				<!-- Extensions -->
				<div class="pt-2 mt-2 border-t border-zinc-200 dark:border-zinc-700">
					<p class="mb-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">Browser Extensions</p>
					<ExtensionsButton />
				</div>
			</div>
		</div>
	{/if}
</nav>

<SearchDialog bind:open={isSearchOpen} />
