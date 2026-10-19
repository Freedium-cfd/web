/**
 * Centralized list of supported publications across the Freedium web frontend.
 */
export const SUPPORTED_PUBLICATIONS = [
	'Medium',
	'The New York Times',
	'The Washington Post',
	'Bloomberg',
	'Reuters',
	'The Economist',
	'Financial Times',
	'The Athletic',
	'Quora',
] as const;

export const SUPPORTED_PUBLICATIONS_SHORT = [
	'Medium',
	'NYT',
	'WaPo',
	'Bloomberg',
	'Reuters',
	'Economist',
	'FT',
	'The Athletic',
	'Quora',
] as const;

export const URL_INPUT_PLACEHOLDER =
	'paste a link — ' + SUPPORTED_PUBLICATIONS_SHORT.join(', ');

export const SUPPORT_MILESTONE_TEXT =
	'across Medium, NYT, The Washington Post, Bloomberg, Reuters, The Economist, Financial Times, The Athletic & Quora.';
