<script lang="ts">
	import Advertise from './Advertise.svelte';
	import ProgressLine from './ProgressLine.svelte';
	import ThemeToggle from './ThemeToggle.svelte';
	import ReportProblem from './ReportProblem.svelte';
	import PayButtons from './PayButtons.svelte';
	import ExtensionsButton from './ExtensionsButton.svelte';

	import { Menu } from 'lucide-svelte';

	let isNavOpen = false;

	const toggleNav = () => {
		isNavOpen = !isNavOpen;
	};
</script>

<nav
	id="header"
	class="sticky top-0 z-20 w-full bg-white border-b shadow-sm dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
>
	<Advertise />
	<ProgressLine />

	<div class="container flex items-center justify-between h-16 px-4 mx-auto">
		<a class="text-2xl font-bold transition-opacity text-primary hover:opacity-80" href="/"
			>Freedium</a
		>

		<button
			id="nav-toggle"
			on:click={toggleNav}
			class="p-2 transition-colors rounded-full md:hidden hover:bg-zinc-100 dark:hover:bg-zinc-800"
			aria-label="Toggle navigation menu"
		>
			<Menu class="w-6 h-6" />
		</button>

		<div class="items-center hidden space-x-2 md:flex">
			<ThemeToggle />
			<ExtensionsButton />
			<div class="w-px h-6 bg-zinc-300 dark:bg-zinc-700"></div>
			<PayButtons name="Ko-fi" url="https://ko-fi.com/zhymabekroman" icon="teenyicons:cup-solid" />
			<PayButtons
				name="Liberapay"
				url="https://liberapay.com/ZhymabekRoman/"
				icon="simple-icons:liberapay"
			/>
			<PayButtons name="PayPal" url="" icon="simple-icons:paypal" />
			<div class="w-px h-6 bg-zinc-300 dark:bg-zinc-700"></div>
			<ReportProblem />
		</div>
	</div>
</nav>
