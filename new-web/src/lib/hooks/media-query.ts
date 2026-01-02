import { readable } from 'svelte/store';
import { browser } from '$app/environment';

/**
 * Creates a media query store that returns true/false based on whether the query matches.
 * Compatible with Svelte 5.
 */
export function mediaQuery(query: string) {
	return readable(false, (set) => {
		if (!browser) return;

		const mediaQueryList = window.matchMedia(query);
		set(mediaQueryList.matches);

		const handler = (event: MediaQueryListEvent) => {
			set(event.matches);
		};

		mediaQueryList.addEventListener('change', handler);

		return () => {
			mediaQueryList.removeEventListener('change', handler);
		};
	});
}
