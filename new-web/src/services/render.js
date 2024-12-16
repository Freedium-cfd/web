import apiFetch from "@/api";

async function render(serviceName) {
	const response = await apiFetch(`/services/${serviceName}/render`);
	if (!response) {
		throw new Error("Failed to fetch article");
	}
	return {
		text: response.text,
		article: response.article,
	};
}

export { render };
