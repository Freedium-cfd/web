import apiFetch from "@/api";
import type { Article } from "$lib/types";

interface RenderRequest {
	content: string;
	frontmatter?: boolean;
}

interface RenderResponse {
	markdown: string;
	service: string;
}

export async function render(content: string, frontmatter = false): Promise<RenderResponse> {
	const response = await apiFetch<RenderResponse>("/render", {
		method: "POST",
		body: JSON.stringify({
			content,
			frontmatter,
		}),
		headers: {
			"Content-Type": "application/json",
		},
	});

	if (!response) {
		throw new Error("Failed to render content");
	}

	return response;
}
