<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
</script>

<footer
	class="z-20 w-full bg-white border-t shadow-sm dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
>
	<div
		class="container flex flex-col items-center justify-between px-4 py-6 mx-auto space-y-4 md:flex-row md:space-y-0"
	>
		<div class="text-sm text-center text-zinc-500 dark:text-zinc-400">
			By Freedium and its contributors.<br />
			Made with ❤️
		</div>

		<nav class="flex flex-wrap justify-center space-x-4">
			<a
				href="/about"
				class="text-sm text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300"
				>About</a
			>
			<a
				href="/privacy"
				class="text-sm text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300"
				>Privacy</a
			>
			<a
				href="/terms"
				class="text-sm text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300"
				>Terms</a
			>
		</nav>

		<div class="flex space-x-2">
			<Button
				variant="ghost"
				size="icon"
				href="https://github.com/Freedium-cfd"
				target="_blank"
				rel="noopener noreferrer"
			>
				<span class="icon-[simple-icons--github] size-5" />
			</Button>
			<Button
				variant="ghost"
				size="icon"
				href="https://codeberg.org/Freedium-cfd"
				target="_blank"
				rel="noopener noreferrer"
			>
				<span class="icon-[simple-icons--codeberg] size-5" />
			</Button>
		</div>
	</div>
</footer>
