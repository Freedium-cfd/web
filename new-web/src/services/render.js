import apiFetch from "@/api";

async function render(serviceName) {
	const response = await apiFetch(`/services/${serviceName}/render`);
	return response;
}

export { render };
