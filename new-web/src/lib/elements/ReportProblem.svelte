<script lang="ts">
	import { Label, Separator } from 'bits-ui';
	import { mediaQuery } from 'svelte-legos';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Drawer from '$lib/components/ui/drawer';
	import * as RadioGroup from '$lib/components/ui/radio-group/index.js';
	import { toast } from 'svelte-sonner';
	import HeroiconsExclamationTriangleSolid from '~icons/heroicons/exclamation-triangle-solid';

	let open = false;
	const isDesktop = mediaQuery('(min-width: 768px)');
	let problemDescription = '';
	let problemType = 'ui_problem';

	export let variant: 'default' | 'warning' | 'danger' = 'default';
	export let showBadge = false;
	export let compact = false;

	const handleSubmit = () => {
		console.log({ problemType, problemDescription });
		toast.success(`${problemType} submitted`);
		problemDescription = '';
		problemType = 'ui_problem';
		open = false;
	};

	const getVariantStyles = (variant: string) => {
		const styles = {
			default: 'bg-primary hover:bg-primary/90',
			warning: 'bg-purple-500 hover:bg-purple-600 text-white',
			danger: 'bg-red-500 hover:bg-red-600 text-white'
		};
		return styles[variant] || styles.default;
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
		<form on:submit|preventDefault={handleSubmit}>
			<Dialog.Content class="w-full max-w-[650px] bg-white dark:bg-zinc-900 flex flex-col">
				<Dialog.Header>
					<Dialog.Title class="text-lg font-semibold tracking-tight">Report a Problem</Dialog.Title>
				</Dialog.Header>
				<div class="flex-1">
					<Dialog.Description class="text-foreground-alt">
						<p>
							Please describe the problem you're experiencing. We'll look into it as soon as
							possible.
						</p>
					</Dialog.Description>
					<div class="grid grid-cols-1 gap-2 md:grid-cols-2 pt-7">
						<div class="flex flex-col items-start gap-2">
							<Label.Root class="text-sm font-medium">Problem Type</Label.Root>
							<RadioGroup.Root bind:value={problemType} class="space-y-2">
								<div class="flex items-center space-x-2">
									<RadioGroup.Item value="ui_problem" id="ui-problem" />
									<Label.Root for="ui-problem">UI problem</Label.Root>
								</div>
								<div class="flex items-center space-x-2">
									<RadioGroup.Item value="article_not_full" id="article-not-full" />
									<Label.Root for="article-not-full">Article is not full</Label.Root>
								</div>
								<div class="flex items-center space-x-2">
									<RadioGroup.Item value="suggestion" id="suggestion" />
									<Label.Root for="suggestion">Suggestion</Label.Root>
								</div>
								<div class="flex items-center space-x-2">
									<RadioGroup.Item value="vulnerability" id="vulnerability" />
									<Label.Root for="vulnerability">Vulnerability (XSS, etc.)</Label.Root>
								</div>
								<div class="flex items-center space-x-2">
									<RadioGroup.Item value="other" id="other" />
									<Label.Root for="other">Other</Label.Root>
								</div>
							</RadioGroup.Root>
						</div>
						<div class="flex flex-col items-start gap-1">
							<Label.Root for="problemDescription" class="text-sm font-medium"
								>Problem Description</Label.Root
							>
							<Textarea
								id="problemDescription"
								bind:value={problemDescription}
								placeholder="Describe the problem you're experiencing..."
								rows={12}
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
			</Dialog.Content>
		</form>
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
		<form on:submit|preventDefault={handleSubmit}>
			<Drawer.Content class="max-h-[90dvh] flex flex-col">
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
								<RadioGroup.Root bind:value={problemType} class="space-y-2">
									<div class="flex items-center space-x-2">
										<RadioGroup.Item value="ui_problem" id="ui-problem-mobile" />
										<Label.Root for="ui-problem-mobile">UI problem</Label.Root>
									</div>
									<div class="flex items-center space-x-2">
										<RadioGroup.Item value="article_not_full" id="article-not-full-mobile" />
										<Label.Root for="article-not-full-mobile">Article is not full</Label.Root>
									</div>
									<div class="flex items-center space-x-2">
										<RadioGroup.Item value="suggestion" id="suggestion-mobile" />
										<Label.Root for="suggestion-mobile">Suggestion</Label.Root>
									</div>
									<div class="flex items-center space-x-2">
										<RadioGroup.Item value="vulnerability" id="vulnerability-mobile" />
										<Label.Root for="vulnerability-mobile">Vulnerability (XSS, etc.)</Label.Root>
									</div>
									<div class="flex items-center space-x-2">
										<RadioGroup.Item value="other" id="other-mobile" />
										<Label.Root for="other-mobile">Other</Label.Root>
									</div>
								</RadioGroup.Root>
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
			</Drawer.Content>
		</form>
	</Drawer.Root>
{/if}
