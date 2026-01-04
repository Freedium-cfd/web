/**
 * Article-related type definitions
 */

/**
 * Author information for an article
 */
export interface Author {
	name: string;
	role?: string;
	avatar: string;
}

/**
 * Table of contents item for article navigation
 */
export interface TableOfContentsItem {
	id: string;
	title: string;
}

/**
 * Full article data structure
 */
export interface Article {
	title: string;
	subtitle?: string;
	date: string;
	url?: string;
	postImage?: string;
	postImageZoom?: string;
	author: Author;
	tableOfContents?: TableOfContentsItem[];
}

/**
 * Error information for article loading failures
 */
export interface ArticleError {
	status: number;
	message: string;
	code: ArticleErrorCode;
	details?: string;
}

/**
 * Error codes for article loading failures
 */
export type ArticleErrorCode =
	| 'ARTICLE_NOT_FOUND'
	| 'RENDER_ERROR'
	| 'COMPILE_ERROR'
	| 'INTERNAL_ERROR';

/**
 * Data structure returned by the article page loader
 */
export interface ArticlePageData {
	slug: string;
	loading: boolean;
	content: string | null;
	markdown: string | null;
	article: Article | null;
	postImageZoom: string | null;
	error: ArticleError | null;
}
