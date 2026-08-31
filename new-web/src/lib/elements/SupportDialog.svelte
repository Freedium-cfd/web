<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Drawer from '$lib/components/ui/drawer';
	import { mediaQuery } from '$lib/hooks/media-query';
	import SimpleIconsPaypal from '~icons/simple-icons/paypal';
	import TeenyiconsCupSolid from '~icons/teenyicons/cup-solid';
	import SimpleIconsLiberapay from '~icons/simple-icons/liberapay';
	import SimpleIconsDiscord from '~icons/simple-icons/discord';
	import MdiContentCopy from '~icons/mdi/content-copy';
	import HeroiconsOutlineExternalLink from '~icons/heroicons-outline/external-link';
	import copy from 'copy-to-clipboard';
	import { toast } from 'svelte-sonner';

	interface Props {
		open?: boolean;
	}

	let { open = $bindable(false) }: Props = $props();
	const isDesktop = mediaQuery('(min-width: 768px)');
	const PAYPAL_URL = 'https://www.paypal.me/qHDa3';

	function handleCopy(text: string) {
		copy(text);
		toast.success('PayPal link copied to clipboard!');
	}
</script>

{#snippet contentBody()}
	<div class="space-y-4 text-zinc-700 dark:text-zinc-300">
		<!-- Milestone celebration banner -->
		<div class="p-3.5 rounded-lg border border-amber-500/20 bg-amber-500/10 dark:bg-amber-500/15">
			<div class="flex items-center gap-2 text-amber-700 dark:text-amber-300 font-semibold text-sm">
				<span>🎉</span>
				<span>1.1M+ Articles Unlocked!</span>
			</div>
			<p class="mt-1.5 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
				Freedium has served over <strong>1,100,000</strong> paywall-free reads across Medium, NYT, The Washington Post, Bloomberg, Reuters, The Economist, Financial Times &amp; The Athletic.
			</p>
		</div>

		<p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
			Freedium runs zero ads, zero tracking, and zero paid tiers. We operate high-speed proxy infrastructure to keep articles open and accessible for everyone. Your support directly funds server and proxy hosting.
		</p>

		<!-- Main PayPal Card -->
		<div class="p-4 rounded-xl border border-sky-500/30 bg-sky-500/5 dark:bg-sky-500/10 space-y-3">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2.5">
					<div class="p-2 rounded-lg bg-[#0079C1]/15 text-[#0079C1] dark:text-sky-400">
						<SimpleIconsPaypal class="size-5 shrink-0" />
					</div>
					<div>
						<h3 class="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Donate via PayPal</h3>
						<p class="text-[11px] text-zinc-500 dark:text-zinc-400">Direct one-time or recurring support</p>
					</div>
				</div>
				<Button
					variant="outline"
					size="sm"
					class="gap-1.5 text-xs h-8"
					onclick={() => handleCopy(PAYPAL_URL)}
					title="Copy PayPal link"
				>
					<MdiContentCopy class="size-3.5" />
					<span>Copy</span>
				</Button>
			</div>

			<Button
				href={PAYPAL_URL}
				target="_blank"
				rel="noopener noreferrer"
				class="w-full justify-center gap-2 bg-[#0070BA] hover:bg-[#005ea6] text-white text-sm font-medium h-10 shadow-sm"
			>
				<SimpleIconsPaypal class="size-4 shrink-0" />
				<span>Send via PayPal (paypal.me/qHDa3)</span>
				<HeroiconsOutlineExternalLink class="size-3.5 opacity-80" />
			</Button>
		</div>

		<!-- Alternative Support Methods -->
		<div class="pt-1 space-y-2">
			<div class="text-[11px] font-mono uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
				Other ways to support
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
				<a
					href="https://ko-fi.com/zhymabekroman"
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-2 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800/80 transition-colors text-xs font-medium"
				>
					<TeenyiconsCupSolid class="size-4 text-amber-600 dark:text-amber-400 shrink-0" />
					<span class="truncate">Ko-fi</span>
					<HeroiconsOutlineExternalLink class="size-3 ml-auto text-zinc-400 shrink-0" />
				</a>

				<a
					href="https://liberapay.com/ZhymabekRoman/"
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-2 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800/80 transition-colors text-xs font-medium"
				>
					<SimpleIconsLiberapay class="size-4 text-amber-500 shrink-0" />
					<span class="truncate">Liberapay</span>
					<HeroiconsOutlineExternalLink class="size-3 ml-auto text-zinc-400 shrink-0" />
				</a>

				<a
					href="https://discord.gg/dAxCuG9nYM"
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-2 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800/80 transition-colors text-xs font-medium"
				>
					<SimpleIconsDiscord class="size-4 text-indigo-500 shrink-0" />
					<span class="truncate">Discord</span>
					<HeroiconsOutlineExternalLink class="size-3 ml-auto text-zinc-400 shrink-0" />
				</a>
			</div>
		</div>
	</div>
{/snippet}

{#if $isDesktop}
	<Dialog.Root bind:open>
		<Dialog.Content class="w-full max-w-[94%] sm:max-w-[490px] flex flex-col p-6">
			<Dialog.Header class="pb-2">
				<Dialog.Title class="text-lg font-semibold tracking-tight">
					Support Freedium
				</Dialog.Title>
			</Dialog.Header>

			<div class="flex-1 py-1">
				{@render contentBody()}
			</div>

			<Dialog.Footer class="flex justify-end pt-3">
				<Dialog.Close class={buttonVariants({ variant: 'outline', size: 'sm' })}>
					Close
				</Dialog.Close>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Root>
{:else}
	<Drawer.Root bind:open>
		<Drawer.Content class="max-h-[90vh]">
			<Drawer.Header class="pb-2">
				<Drawer.Title class="text-lg font-semibold tracking-tight">
					Support Freedium
				</Drawer.Title>
			</Drawer.Header>

			<div class="flex-1 px-4 py-2 overflow-y-auto">
				{@render contentBody()}
			</div>

			<Drawer.Footer class="flex justify-end p-4 pt-2">
				<Drawer.Close class={buttonVariants({ variant: 'outline', size: 'sm' })}>
					Close
				</Drawer.Close>
			</Drawer.Footer>
		</Drawer.Content>
	</Drawer.Root>
{/if}
