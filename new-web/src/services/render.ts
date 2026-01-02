import apiFetch from "@/api";
import type { Article } from "$lib/types";

interface RenderResponse {
	text: string;
	article: Article;
}

export async function render(serviceName: string): Promise<RenderResponse> {
	const response = await apiFetch<RenderResponse>(`/services/${serviceName}/render`);
	if (!response) {
		throw new Error("Failed to fetch article");
	}
	return {
		text: response.text,
		article: response.article,
	};
}
