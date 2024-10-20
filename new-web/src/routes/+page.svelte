<script lang="ts">
	import Header from '$lib/elements/Header.svelte';
	import Masonry from 'svelte-bricks';
	import HomeBanner from '$lib/elements/HomeBanner.svelte';
	import BlogCard from '$lib/elements/BlogCard.svelte';
	import Footer from '$lib/elements/Footer.svelte';

	const blogPosts = [
		{
			title: '10 Productivity Hacks for Remote Workers',
			excerpt: 'Boost your efficiency while working from home with these game-changing strategies.',
			imageUrl: 'https://picsum.photos/seed/post1/400/300',
			readingTime: '7',
			publishedAt: '2023-04-10',
			collection: { name: 'Productivity Tips', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'Jane Doe',
			slug: '10-productivity-hacks-for-remote-workers'
		},
		{
			title: 'The Future of AI in Healthcare',
			excerpt:
				'Exploring how artificial intelligence is revolutionizing medical diagnoses and treatment plans.',
			imageUrl: 'https://picsum.photos/seed/post2/400/300',
			readingTime: '10',
			publishedAt: '2023-04-12',
			collection: { name: 'Tech in Medicine', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'John Smith',
			slug: 'the-future-of-ai-in-healthcare'
		},
		{
			title: 'Mastering the Art of Time Management',
			excerpt: 'Learn how to take control of your schedule and achieve more in less time.',
			imageUrl: 'https://picsum.photos/seed/post3/400/300',
			size: 'small',
			readingTime: '5',
			publishedAt: '2023-04-14',
			collection: { name: 'Personal Development', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'Emily Johnson',
			slug: 'mastering-the-art-of-time-management'
		},
		{
			title: 'Cybersecurity Essentials for Small Businesses',
			excerpt: 'Protect your company from digital threats with these crucial security measures.',
			imageUrl: 'https://picsum.photos/seed/post4/400/300',
			size: 'wide',
			readingTime: '8',
			publishedAt: '2023-04-16',
			collection: { name: 'Business Security', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'Michael Brown',
			slug: 'cybersecurity-essentials-for-small-businesses'
		},
		{
			title: 'The Psychology of Habit Formation',
			excerpt: 'Understand the science behind creating lasting habits and breaking bad ones.',
			imageUrl: 'https://picsum.photos/seed/post5/400/300',
			size: 'tall',
			readingTime: '6',
			publishedAt: '2023-04-18',
			collection: { name: 'Psychology Insights', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'Sarah Wilson',
			slug: 'the-psychology-of-habit-formation'
		},
		{
			title: 'Sustainable Tech: Innovations for a Greener Future',
			excerpt: 'Discover cutting-edge technologies that are helping to combat climate change.',
			bottomImageUrl: 'https://picsum.photos/seed/post6/400/300',
			size: 'medium',
			readingTime: '9',
			publishedAt: '2023-04-20',
			collection: { name: 'Green Technology', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'David Lee',
			slug: 'sustainable-tech-innovations-for-a-greener-future'
		},
		{
			title: 'Mindfulness in the Digital Age',
			excerpt: 'Find balance and reduce stress in an increasingly connected world.',
			bottomImageUrl: 'https://picsum.photos/seed/post7/400/300',
			size: 'small',
			readingTime: '4',
			publishedAt: '2023-04-22',
			collection: { name: 'Digital Wellness', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'Lisa Chen',
			slug: 'mindfulness-in-the-digital-age'
		},
		{
			title: 'The Rise of No-Code Development',
			excerpt: 'How no-code platforms are democratizing software creation for non-programmers.',
			imageUrl: 'https://picsum.photos/seed/post8/400/300',
			size: 'medium',
			readingTime: '7',
			publishedAt: '2023-04-24',
			collection: { name: 'Software Trends', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'Alex Rodriguez',
			slug: 'the-rise-of-no-code-development'
		},
		{
			title: 'The Rise of No-Code Development',
			excerpt: 'How no-code platforms are democratizing software creation for non-programmers.',
			size: 'medium',
			readingTime: '7',
			publishedAt: '2023-04-26',
			collection: { name: 'Software Trends', avatarId: '1*AZxiin1Cvws3J0TwNUP2sQ.png' },
			creator: 'Chris Taylor',
			slug: 'the-rise-of-no-code-development-2'
		}
	];

	$: items = blogPosts.map((post, index) => ({ ...post, id: index }));

	let [minColWidth, maxColWidth, gap] = [300, 600, 20];
</script>

<head>
	<title>Freedium - Your paywall breakthrough for Medium!</title>
</head>

<Header />
<HomeBanner />

<div class="container px-4 py-8 mx-auto">
	<Masonry {items} {minColWidth} {maxColWidth} {gap} let:item>
		<BlogCard {...item} />
	</Masonry>
</div>

<Footer />
