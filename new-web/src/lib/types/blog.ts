/**
 * Blog-related type definitions
 */

/**
 * Blog post size variants for masonry layout
 */
export type BlogPostSize = 'small' | 'medium' | 'large' | 'wide' | 'tall';

/**
 * Collection/category information for a blog post
 */
export interface BlogCollection {
	name: string;
	avatarId: string;
}

/**
 * Blog post data structure for display in cards
 */
export interface BlogPost {
	id: number;
	title: string;
	excerpt: string;
	imageUrl?: string;
	bottomImageUrl?: string | null;
	size?: BlogPostSize | null;
	readingTime: string;
	publishedAt: string;
	collection?: BlogCollection | null;
	creator: string;
	slug: string;
}

/**
 * Search result post structure
 */
export interface SearchPost {
	id: string;
	title: string;
	date: Date;
	excerpt: string;
	imageUrl: string;
}
