<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import BookmarkButton from './BookmarkButton.svelte';
	import MdiPuzzle from '~icons/mdi/puzzle';
	import MdiFirefox from '~icons/mdi/firefox';
	import HeroiconsOutlineExternalLink from '~icons/heroicons-outline/external-link';
	import MdiGoogleChrome from '~icons/mdi/google-chrome';
	import MdiScriptText from '~icons/mdi/script-text';
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger asChild let:builder>
		<Button
			builders={[builder]}
			variant="ghost"
			class="px-3 text-gray-600 py-7 dark:text-white hover:text-primary dark:hover:text-primary"
			><MdiPuzzle class="size-5" /></Button
		>
	</DropdownMenu.Trigger>
	<DropdownMenu.Content class="w-56 text-zinc-600 dark:text-zinc-300 ">
		<DropdownMenu.Label>Browser Extensions</DropdownMenu.Label>
		<DropdownMenu.Item class="text-xs text-gray-600 cursor-default dark:text-gray-500">
			<span
				>Note: These solutions are <span class="border-b border-dashed border-zinc-900">not</span> developed or
				controlled by the Freedium developers team. Use at your own risk.</span
			>
		</DropdownMenu.Item>
		<DropdownMenu.Item class="text-xs text-gray-600 cursor-default dark:text-gray-500">
			<span> Freedium is not responsible for any damages or losses caused by these solutions.</span>
		</DropdownMenu.Item>
		<DropdownMenu.Separator />
		<DropdownMenu.Group>
			<DropdownMenu.Item>
				<MdiFirefox class="w-4 h-4 mr-2" />
				<span>Firefox</span>
				<HeroiconsOutlineExternalLink class="size-3.5" />
			</DropdownMenu.Item>
			<DropdownMenu.Item>
				<MdiGoogleChrome class="w-4 h-4 mr-2" />
				<span>Chrome</span>
				<HeroiconsOutlineExternalLink class="size-3.5" />
			</DropdownMenu.Item>
		</DropdownMenu.Group>
		<DropdownMenu.Separator />
		<DropdownMenu.Item>
			<a
				class="flex flex-row items-center"
				href="https://gist.github.com/mathix420/e0604ab0e916622972372711d2829555"
				target="_blank"
			>
				<MdiScriptText class="w-4 h-4 mr-2" />
				<span>Userscript - only Medium</span>
				<HeroiconsOutlineExternalLink class="size-3.5" />
			</a>
		</DropdownMenu.Item>
		<DropdownMenu.Separator />
		<BookmarkButton />
	</DropdownMenu.Content>
</DropdownMenu.Root>
