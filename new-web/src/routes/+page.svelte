<script lang="ts">
	import Header from '$lib/elements/Header.svelte';
	import UrlBox from '$lib/elements/UrlBox.svelte';

	function generateRandomParagraphs(count: number): string[] {
		const subjects = [
			'Svelte',
			'SvelteKit',
			'web development',
			'JavaScript',
			'TypeScript',
			'frontend',
			'backend',
			'full-stack'
		];
		const verbs = [
			'explore',
			'learn about',
			'discover',
			'master',
			'understand',
			'dive into',
			'experiment with',
			'practice'
		];
		const objects = [
			'documentation',
			'tutorials',
			'examples',
			'projects',
			'community',
			'best practices',
			'tips and tricks',
			'advanced concepts'
		];

		return Array.from({ length: count }, () => {
			const subject = subjects[Math.floor(Math.random() * subjects.length)];
			const verb = verbs[Math.floor(Math.random() * verbs.length)];
			const object = objects[Math.floor(Math.random() * objects.length)];
			return `Visit <a href="https://kit.svelte.dev">kit.svelte.dev</a> to ${verb} ${subject} ${object} and enhance your development skills.`;
		});
	}

	const randomParagraphs = generateRandomParagraphs(1001);
</script>

<head>
	<title>Freedium - Your paywall breakthrough for Medium!</title>
</head>

<Header />
<UrlBox />
{#each randomParagraphs as paragraph}
	<p>{@html paragraph}</p>
{/each}
