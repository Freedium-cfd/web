<script lang="ts">
	import Icon from '@iconify/svelte';
	import { Label, Separator } from 'bits-ui';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog';
	import * as RadioGroup from '$lib/components/ui/radio-group/index.js';
	import { toast } from 'svelte-sonner';

	let problemDescription = '';
	let problemType = 'ui_problem';

	const handleSubmit = () => {
		console.log({ problemType, problemDescription });
		toast.success(`${problemType} submitted`);
		problemDescription = '';
		problemType = 'ui_problem';
	};
</script>

<Dialog.Root>
	<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>
		<div class="flex items-center space-x-2 text-white">
			<Icon icon="heroicons:exclamation-triangle-solid" class="size-5" />
			<span class="text-sm font-medium">Report a problem</span>
		</div>
	</Dialog.Trigger>
	<form on:submit={handleSubmit}>
		<Dialog.Content
			class="w-full max-w-[94%] sm:max-w-[490px] md:w-full bg-white dark:bg-zinc-900 flex flex-col"
		>
			<Dialog.Header>
				<Dialog.Title class="text-lg font-semibold tracking-tight">Report a Problem</Dialog.Title>
			</Dialog.Header>
			<div class="flex-1">
				<Dialog.Description class="text-foreground-alt">
					<p>
						Please describe the problem you're experiencing. We'll look into it as soon as possible.
					</p>
				</Dialog.Description>
				<div class="flex flex-col items-start gap-2 pb-6 pt-7">
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
				<div class="flex flex-col items-start gap-1 pb-6">
					<Label.Root for="problemDescription" class="text-sm font-medium">
						Problem Description
					</Label.Root>
					<Textarea
						id="problemDescription"
						bind:value={problemDescription}
						placeholder="Describe the problem you're experiencing..."
						rows={12}
					></Textarea>
					<p class="mt-2 text-sm text-foreground-alt">
						The current opened link will be automatically attached to your report.
					</p>
				</div>
			</div>

			<div class="self-end p-4">
				<Dialog.Footer>
					<Dialog.Close class={buttonVariants({ variant: 'outline' })}>Cancel</Dialog.Close>
					<Button type="submit" on:click={handleSubmit}>Submit</Button>
				</Dialog.Footer>
			</div>
		</Dialog.Content>
	</form>
</Dialog.Root>
