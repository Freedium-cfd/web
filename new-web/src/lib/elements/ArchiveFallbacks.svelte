<script lang="ts">
	import HeroiconsOutlineExternalLink from '~icons/heroicons-outline/external-link';

	interface Props {
		url: string;
	}

	let { url }: Props = $props();

	let archivePh = $derived(`https://archive.ph/newest/${url}`);
	let wayback = $derived(`https://web.archive.org/web/2/${url}`);
	let googleCache = $derived(`https://www.google.com/search?q=cache:${encodeURIComponent(url)}`);
</script>

<div class="fallback-card">
	<div class="fallback-header">
		<span>🏛️</span>
		<span>Check public web archives</span>
	</div>
	<p class="fallback-desc">
		A preserved snapshot of this article may already be available:
	</p>
	<div class="fallback-links">
		<a href={archivePh} target="_blank" rel="noopener noreferrer" class="fallback-btn">
			<span>Archive.today</span>
			<HeroiconsOutlineExternalLink class="size-3.5 opacity-70" />
		</a>
		<a href={wayback} target="_blank" rel="noopener noreferrer" class="fallback-btn">
			<span>Wayback Machine</span>
			<HeroiconsOutlineExternalLink class="size-3.5 opacity-70" />
		</a>
		<a href={googleCache} target="_blank" rel="noopener noreferrer" class="fallback-btn">
			<span>Google Cache</span>
			<HeroiconsOutlineExternalLink class="size-3.5 opacity-70" />
		</a>
	</div>
</div>

<style>
	.fallback-card {
		background: var(--bg);
		border: 1px solid var(--line);
		border-radius: 10px;
		padding: 16px 18px;
		margin: 0 auto 24px;
		max-width: 460px;
		text-align: left;
	}

	.fallback-header {
		display: flex;
		align-items: center;
		gap: 6px;
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		color: var(--ink);
		margin-bottom: 6px;
	}

	.fallback-desc {
		font-size: 12px;
		line-height: 1.5;
		color: var(--ink-3);
		margin: 0 0 14px;
	}

	.fallback-links {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.fallback-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 7px 12px;
		border-radius: 6px;
		font-family: var(--font-sans);
		font-size: 12px;
		font-weight: 500;
		text-decoration: none;
		background: var(--bg-2);
		color: var(--ink-2);
		border: 1px solid var(--line);
		transition: all 0.15s ease;
	}

	.fallback-btn:hover {
		background: var(--bg-3);
		color: var(--ink);
		border-color: var(--line-2);
	}
</style>
