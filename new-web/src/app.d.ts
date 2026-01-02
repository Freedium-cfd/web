/// <reference types="unplugin-icons/types/svelte" />

// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

// Type declaration for unplugin-icons raw imports
declare module '~icons/*?raw' {
	const src: string;
	export default src;
}

export {};
