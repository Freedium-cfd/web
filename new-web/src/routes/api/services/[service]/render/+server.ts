import { json } from "@sveltejs/kit";
import { compile } from "mdsvex";
import type { MdsvexCompileOptions } from "mdsvex";
import type { RequestHandler } from "./$types";

const mdsvexConfig: MdsvexCompileOptions = {
	extensions: [".svx", ".md"],
	smartypants: {
		dashes: "oldschool" as const,
	},
	remarkPlugins: [],
	rehypePlugins: [],
};

export const GET: RequestHandler = async ({ params }) => {
	try {
		const { service } = params;

		// Example content - replace with your actual content fetching
		const markdown = `
# Test Content ${service}
This is a test article.
    `;

		const compiled = await compile(markdown, mdsvexConfig);

		if (!compiled) {
			throw new Error("Failed to compile markdown");
		}

		return json({
			text: compiled.code,
		});
	} catch (error) {
		return json({ error: (error as Error).message }, { status: 500 });
	}
};
