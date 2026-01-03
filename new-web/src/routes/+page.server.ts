import type { PageServerLoad } from "./$types";

// Home page - no server-side data loading needed
// Article rendering happens on [slug] route
export const load: PageServerLoad = async () => {
	return {};
};
