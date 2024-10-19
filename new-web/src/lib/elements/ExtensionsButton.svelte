<script lang="ts">
	import Icon from '@iconify/svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import BookmarkButton from './BookmarkButton.svelte';
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger asChild let:builder>
		<Button
			builders={[builder]}
			variant="ghost"
			class="px-3 text-gray-600 py-7 dark:text-white hover:text-primary dark:hover:text-primary"
			><Icon icon="mdi:puzzle" class="size-5" /></Button
		>
	</DropdownMenu.Trigger>
	<DropdownMenu.Content class="w-56 text-zinc-600 dark:text-zinc-300 ">
		<DropdownMenu.Label>Browser Extensions</DropdownMenu.Label>
		<DropdownMenu.Item class="text-xs text-gray-600 cursor-default dark:text-gray-500">
			<span
				>Note: These solutions are not developed or controlled by the Freedium developers team. Use
				at your own risk.</span
			>
		</DropdownMenu.Item>
		<DropdownMenu.Item class="text-xs text-gray-600 cursor-default dark:text-gray-500">
			<span> Freedium is not responsible for any damages or losses caused by these solutions.</span>
		</DropdownMenu.Item>
		<DropdownMenu.Separator />
		<DropdownMenu.Group>
			<DropdownMenu.Item>
				<Icon icon="mdi:firefox" class="w-4 h-4 mr-2" />
				<span>Firefox</span>
				<Icon icon="heroicons-outline:external-link" class="size-3.5" />
			</DropdownMenu.Item>
			<DropdownMenu.Item>
				<Icon icon="mdi:google-chrome" class="w-4 h-4 mr-2" />
				<span>Chrome</span>
				<Icon icon="heroicons-outline:external-link" class="size-3.5" />
			</DropdownMenu.Item>
		</DropdownMenu.Group>
		<DropdownMenu.Separator />
		<DropdownMenu.Item>
			<a
				class="flex flex-row items-center"
				href="https://gist.github.com/mathix420/e0604ab0e916622972372711d2829555"
				target="_blank"
			>
				<Icon icon="mdi:script-text" class="w-4 h-4 mr-2" />
				<span>Userscript - only Medium</span>
				<Icon icon="heroicons-outline:external-link" class="size-3.5" />
			</a>
		</DropdownMenu.Item>
		<DropdownMenu.Separator />
		<BookmarkButton />
	</DropdownMenu.Content>
</DropdownMenu.Root>
