<script lang="ts">
	import ArticlePage from '$lib/elements/ArticlePage.svelte';
	import ArticlePageSkeleton from '$lib/elements/ArticlePageSkeleton.svelte';

	let { data } = $props();

	/** Map a render result (eager or streamed) into ArticlePage's data shape. */
	function toArticleData(result: {
		html: string | null;
		markdown: string | null;
		article: unknown;
		error: unknown;
		cacheStatus?: string;
		renderTimeMs?: number;
	}) {
		return {
			slug: data.slug,
			originalUrl: data.originalUrl,
			loading: false,
			content: result.html,
			markdown: result.markdown,
			article: result.article,
			error: result.error,
			cacheStatus: result.cacheStatus ?? 'miss',
			renderTimeMs: result.renderTimeMs ?? 0,
		};
	}
</script>

{#if data.eager}
	<!-- Won the render-race: full article in the initial HTML (good for
	     save-it / reader apps + crawlers). -->
	<ArticlePage data={toArticleData(data.eager)} />
{:else}
	<!-- Cold render: stream the skeleton, body arrives when it resolves. -->
	{#await data.streamed}
		<ArticlePageSkeleton slug={data.slug} />
	{:then result}
		<ArticlePage data={toArticleData(result)} />
	{:catch err}
		<ArticlePage
			data={{
				slug: data.slug,
				loading: false,
				content: null,
				markdown: null,
				article: null,
				error: {
					status: 500,
					message: (err as Error)?.message ?? 'Render failed',
					code: 'RENDER_ERROR',
				},
			}}
		/>
	{/await}
{/if}
