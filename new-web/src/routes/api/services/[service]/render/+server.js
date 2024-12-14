import { json } from "@sveltejs/kit";
import { compile } from "mdsvex";

const mdsvexConfig = {
	extensions: [".svx", ".md"],
	smartypants: {
		dashes: "oldschool",
	},
	remarkPlugins: [],
	rehypePlugins: [],
};

export async function GET({ params }) {
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
		return json({ error: error.message }, { status: 500 });
	}
}
