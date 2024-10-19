<script lang="ts">
	import Icon from '@iconify/svelte';
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Dialog from '$lib/components/ui/dialog';
	import CodeBlock from './CodeBlock.svelte';
	import copy from 'copy-to-clipboard';
	import { toast } from 'svelte-sonner';

	function handleCopy(text: string) {
		copy(text);
		toast.success('Copied to clipboard');
	}
</script>

<Dialog.Root>
	<Dialog.Trigger class="w-full">
		<DropdownMenu.Item on:click={($event) => $event.preventDefault()}>
			<Icon icon="mdi:bookmark" class="w-4 h-4 mr-2" />
			<span>Bookmark</span>
		</DropdownMenu.Item>
	</Dialog.Trigger>
	<Dialog.Content
		class="w-full max-w-[94%] sm:max-w-[490px] md:w-full bg-white dark:bg-zinc-900 flex flex-col"
	>
		<Dialog.Header>
			<Dialog.Title class="text-lg font-semibold tracking-tight"
				>Add Bookmark for Medium Bypass</Dialog.Title
			>
		</Dialog.Header>
		<div class="flex-1">
			<Dialog.Description class="space-y-4 text-foreground-alt">
				<p class="text-sm italic">
					Credit: blazeknifecatcher on <a
						href="https://www.reddit.com/r/paywall/comments/15jsr6z/bypass_mediumcom_paywall/"
						class="text-blue-500 hover:underline"
						target="_blank"
						rel="noopener noreferrer">Reddit</a
					>
				</p>

				<div class="p-4 bg-gray-100 rounded-lg dark:bg-zinc-800">
					<div class="flex items-center justify-between mb-2">
						<h3 class="mt-2 font-semibold">Option 1: Redirect in Current Tab</h3>
						<Button
							variant="outline"
							size="icon"
							class="ml-2"
							on:click={() =>
								handleCopy(
									`javascript:window.location="https://freedium.cfd/"+encodeURIComponent(window.location)"`
								)}
						>
							<Icon icon="mdi:content-copy" class="w-4 h-4" />
						</Button>
					</div>
					<p class="mb-2">Create a new bookmark with the following code as the URL:</p>

					<CodeBlock
						code={`javascript:window.location="https://freedium.cfd/"+encodeURIComponent(window.location)"`}
					/>
				</div>

				<div class="p-4 bg-gray-100 rounded-lg dark:bg-zinc-800">
					<div class="flex items-center justify-between mb-2">
						<h3 class="mt-2 font-semibold">Option 2: Open in New Tab</h3>
						<Button
							variant="outline"
							size="icon"
							class="ml-2"
							on:click={() =>
								handleCopy(
									`javascript:(function(){window.open("https://freedium.cfd/"+encodeURIComponent(window.location))})();`
								)}
						>
							<Icon icon="mdi:content-copy" class="w-4 h-4" />
						</Button>
					</div>

					<p class="mb-2">For opening in a new tab, use this code instead:</p>
					<CodeBlock
						code={`javascript:(function(){window.open("https://freedium.cfd/"+encodeURIComponent(window.location))})();`}
					/>
				</div>

				<p>Click the bookmark on any Medium page to bypass the paywall using Freedium.</p>
			</Dialog.Description>
		</div>
		<Dialog.Footer class="flex justify-end p-4">
			<Dialog.Close class={buttonVariants({ variant: 'outline' })}>Close</Dialog.Close>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
