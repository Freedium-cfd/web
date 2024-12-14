import { render } from "@/services";
import { compile } from "mdsvex";

export async function load({ params }) {
	try {
		const transformed = await render("medium");
		const { code } = await compile(transformed.text);

		return {
			content: code,
			article: {
				title: "UploadThing is 5x Faster",
				date: "2024-09-13T12:00:00Z",
				author: {
					name: "Theo Browne",
					role: "CEO @ Ping Labs",
					avatar: "https://picsum.photos/seed/post1/400/300",
				},
				postImage: "https://picsum.photos/seed/postimage/1200/600",
				tableOfContents: [
					{ id: "v7-is-here", title: "V7 Is Here!" },
					{ id: "benchmarks", title: "Benchmarks" },
					{ id: "the-road-to-v7", title: "The Road To V7" },
					{ id: "uploadthing-has-served", title: "UploadThing Has Served..." },
					{
						id: "and-were-just-getting-started",
						title: "...and we're just getting started",
					},
				],
			},
		};
	} catch (error) {
		return {
			content: null,
			article: null,
			error: "Failed to load article",
		};
	}
}
