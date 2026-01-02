<script lang="ts">
	import { Label } from 'bits-ui';
	import { mediaQuery } from '$lib/hooks/media-query';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Drawer from '$lib/components/ui/drawer';
	import * as Select from '$lib/components/ui/select/index.js';
	import { toast } from 'svelte-sonner';
	import HeroiconsExclamationTriangleSolid from '~icons/heroicons/exclamation-triangle-solid';
	import type { ReportProblemProps } from '$lib/types';

	let { variant = 'default', showBadge = false, compact = false }: ReportProblemProps = $props();

	let open = $state(false);
	const isDesktop = mediaQuery('(min-width: 768px)');
	let problemDescription = $state('');
	let problemType = $state<{ value: string; label: string }>({ value: 'ui_problem', label: 'UI problem' });

	const problemTypeOptions = [
		{ value: 'ui_problem', label: 'UI problem' },
		{ value: 'article_not_full', label: 'Article is not full' },
		{ value: 'suggestion', label: 'Suggestion' },
		{ value: 'vulnerability', label: 'Vulnerability (XSS, etc.)' },
		{ value: 'other', label: 'Other' }
	];

	const handleSubmit = (e: SubmitEvent) => {
		e.preventDefault();
		console.log({ problemType: problemType.value, problemDescription });
		toast.success(`${problemType.label} submitted`);
		problemDescription = '';
		problemType = { value: 'ui_problem', label: 'UI problem' };
		open = false;
	};

	const getVariantStyles = (v: string) => {
		const styles: Record<string, string> = {
			default: 'bg-primary hover:bg-primary/90',
			warning: 'bg-purple-500 hover:bg-purple-600 text-white',
			danger: 'bg-red-500 hover:bg-red-600 text-white'
		};
		return styles[v] || styles.default;
	};
</script>

{#if $isDesktop}
	<Dialog.Root bind:open>
		<Dialog.Trigger
			class={`${buttonVariants({ variant: 'default', size: compact ? 'icon' : 'default' })} ${getVariantStyles(variant)} relative`}
		>
			{#if compact}
				<HeroiconsExclamationTriangleSolid class="size-5" />
			{:else}
				<div class="flex items-center space-x-2">
					<HeroiconsExclamationTriangleSolid class="size-5" />
					<span class="hidden text-sm font-medium lg:block">Report a problem</span>
				</div>
			{/if}
			{#if showBadge}
				<span class="absolute flex w-3 h-3 -top-1 -right-1">
					<span
						class="absolute inline-flex w-full h-full bg-red-400 rounded-full opacity-75 animate-ping"
					></span>
					<span class="relative inline-flex w-3 h-3 bg-red-500 rounded-full"></span>
				</span>
			{/if}
		</Dialog.Trigger>
		<Dialog.Content class="w-full max-w-[650px] bg-white dark:bg-zinc-900 flex flex-col">
			<form onsubmit={handleSubmit}>
				<Dialog.Header>
					<Dialog.Title class="text-lg font-semibold tracking-tight">Report a Problem</Dialog.Title>
				</Dialog.Header>
				<div class="flex-1">
					<Dialog.Description class="text-foreground-alt">
						Please describe the problem you're experiencing. We'll look into it as soon as
						possible.
					</Dialog.Description>
					<div class="flex flex-col gap-4 pt-7">
						<div class="flex flex-col items-start gap-2">
							<Label.Root class="text-sm font-medium">Problem Type</Label.Root>
							<Select.Root type="single" bind:value={problemType}>
								<Select.Trigger class="w-full">
									{problemType.label}
								</Select.Trigger>
								<Select.Content>
									{#each problemTypeOptions as option}
										<Select.Item value={option.value} label={option.label} />
									{/each}
								</Select.Content>
							</Select.Root>
						</div>
						<div class="flex flex-col items-start gap-1">
							<Label.Root for="problemDescription" class="text-sm font-medium"
								>Problem Description</Label.Root
							>
							<Textarea
								id="problemDescription"
								bind:value={problemDescription}
								placeholder="Describe the problem you're experiencing..."
								rows={6}
							/>
							<p class="mt-2 text-sm text-foreground-alt">
								The current opened page will be automatically attached to your report.
							</p>
						</div>
					</div>
				</div>
				<div class="self-end p-4">
					<Dialog.Footer>
						<Dialog.Close class={buttonVariants({ variant: 'outline' })}>Cancel</Dialog.Close>
						<Button type="submit">Submit</Button>
					</Dialog.Footer>
				</div>
			</form>
		</Dialog.Content>
	</Dialog.Root>
{:else}
	<Drawer.Root bind:open>
		<Drawer.Trigger class={buttonVariants({ variant: 'default', size: compact ? 'icon' : 'default' })}>
			{#if compact}
				<HeroiconsExclamationTriangleSolid class="size-5 text-white" />
			{:else}
				<div class="flex items-center space-x-2 text-white">
					<HeroiconsExclamationTriangleSolid class="size-5" />
					<span class="hidden text-sm font-medium lg:block">Report a problem</span>
				</div>
			{/if}
		</Drawer.Trigger>
		<Drawer.Content class="max-h-[90dvh] flex flex-col">
			<form onsubmit={handleSubmit}>
				<div class="flex-1 mb-5 overflow-y-auto">
					<Drawer.Header class="text-left">
						<Drawer.Title class="text-lg font-semibold tracking-tight"
							>Report a Problem</Drawer.Title
						>
						<Drawer.Description class="text-foreground-alt">
							Please describe the problem you're experiencing. We'll look into it as soon as
							possible.
						</Drawer.Description>
					</Drawer.Header>
					<div class="px-4 space-y-4">
						<div class="space-y-4">
							<div class="flex flex-col items-start space-y-2">
								<Label.Root class="text-sm font-medium">Problem Type</Label.Root>
								<Select.Root type="single" bind:value={problemType}>
									<Select.Trigger class="w-full">
										{problemType.label}
									</Select.Trigger>
									<Select.Content>
										{#each problemTypeOptions as option}
											<Select.Item value={option.value} label={option.label} />
										{/each}
									</Select.Content>
								</Select.Root>
							</div>
							<div class="flex flex-col items-start space-y-2">
								<Label.Root for="problemDescription-mobile" class="text-sm font-medium"
									>Problem Description</Label.Root
								>
								<Textarea
									id="problemDescription-mobile"
									bind:value={problemDescription}
									placeholder="Describe the problem you're experiencing..."
									rows={12}
								/>
								<p class="mt-2 text-sm text-foreground-alt">
									The current opened page will be automatically attached to your report.
								</p>
							</div>
						</div>

						<div class="flex justify-center gap-2">
							<Drawer.Close class={buttonVariants({ variant: 'outline' })}>Cancel</Drawer.Close>
							<Button type="submit">Submit</Button>
						</div>
					</div>
				</div>
			</form>
		</Drawer.Content>
	</Drawer.Root>
{/if}
