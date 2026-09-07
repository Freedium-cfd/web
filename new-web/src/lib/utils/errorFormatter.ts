import type { ArticlePageData } from '$lib/types';

export function getErrorMessage(error: ArticlePageData['error']): string {
	if (!error) return '';

	switch (error.code) {
		case 'ARTICLE_NOT_FOUND':
			return "We couldn't find the article you're looking for.";
		case 'RENDER_ERROR':
			return 'There was a problem preparing this article.';
		case 'COMPILE_ERROR':
			return 'There was a problem processing the article content.';
		case 'UNSUPPORTED_SITE':
			return error.message || "This site isn't supported.";
		default:
			return error.message || 'An unexpected error occurred.';
	}
}
