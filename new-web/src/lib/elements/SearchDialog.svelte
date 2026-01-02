<script lang="ts">
	import * as Command from '$lib/components/ui/command/index.js';
	import { debounce } from 'es-toolkit';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import type { SearchPost } from '$lib/types';

	let value = $state('');
	let searchQuery = $state('');

	interface Props {
		open?: boolean;
	}

	let { open = $bindable(false) }: Props = $props();
	let loading = $state(false);

	let searchResults: SearchPost[] = $state([]);

	const mockSearch = async (query: string): Promise<SearchPost[]> => {
		loading = true;

		await new Promise((resolve) => setTimeout(resolve, 1500)); // Increased delay for demo

		loading = false;

		return [
			{
				id: Math.random().toString(),
				title: `Post 1 about ${query}`,
				date: new Date(),
				excerpt: 'This is a short excerpt of the post...',
				imageUrl: 'https://picsum.photos/50/50?random=1'
			},
			{
				id: Math.random().toString(),
				title: `Post 2 mentioning ${query}`,
				date: new Date(Date.now() - 86400000),
				excerpt: 'Another interesting excerpt here...',
				imageUrl: 'https://picsum.photos/50/50?random=2'
			},
			{
				id: Math.random().toString(),
				title: `Post 3 related to ${query}`,
				date: new Date(Date.now() - 172800000),
				excerpt: 'Yet another captivating excerpt...',
				imageUrl: 'https://picsum.photos/50/50?random=3'
			}
		];
	};

	const debouncedSearch = debounce(async (query: string) => {
		const searchResultsData = await mockSearch(query);
		searchResults = searchResultsData;
	}, 300);

	$effect(() => {
		if (searchQuery) {
			debouncedSearch(searchQuery);
		} else {
			searchResults = [];
			loading = false;
			debouncedSearch.cancel();
		}
	});

	function formatDate(date: Date): string {
		return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
	}

	const defaultImageUrl = 'https://via.placeholder.com/50';
</script>

<Command.Dialog bind:open bind:value shouldFilter={false} loop>
	<Command.Input placeholder="Search posts..." bind:value={searchQuery} />
	<Command.List>
		<!-- <Command.Empty>No posts found. Try a different search term.</Command.Empty> -->

		{#if loading}
			{#each Array(3) as _}
				<div class="flex items-start py-2 m-2">
					<Skeleton class="w-12 h-12 mr-3 rounded" />
					<div class="flex flex-col grow">
						<Skeleton class="w-3/4 h-5 mb-1" />
						<Skeleton class="w-1/4 h-4 mb-1" />
						<Skeleton class="w-full h-4" />
					</div>
				</div>
			{/each}
		{:else}
			{#each searchResults as post}
				<Command.Item value={post.id} class="flex items-start py-2">
					<img
						src={post.imageUrl || defaultImageUrl}
						alt={post.title}
						class="object-cover w-12 h-12 mr-3 rounded"
					/>
					<div class="flex flex-col grow">
						<span class="font-medium">{post.title}</span>
						<div class="mt-1 text-sm text-gray-500">{formatDate(post.date)}</div>
						<div class="mt-1 text-sm">{post.excerpt}</div>
					</div>
				</Command.Item>
			{/each}
		{/if}
		{#if searchResults.length === 0 && !loading}
			<Command.Item>
				<div class="flex flex-col gap-2">
					<span class="text-sm italic text-muted-foreground"
						>Start typing post name to search or enter URL.</span
					>
					<span class="text-sm italic text-muted-foreground">For example:</span>
					<span class="text-sm italic text-muted-foreground">
						- https://medium.com/post-test-1</span
					>
					<span class="text-sm italic text-muted-foreground"> - How to create a blog post</span>
				</div>
			</Command.Item>
		{/if}
	</Command.List>
</Command.Dialog>
