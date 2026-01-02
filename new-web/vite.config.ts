import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import path from "path";
import Icons from "unplugin-icons/vite";

export default defineConfig({
	plugins: [
		sveltekit(),
		tailwindcss(),
		Icons({
			compiler: "svelte",
		}),
	],
	resolve: {
		alias: {
			$lib: path.resolve("./src/lib"),
			"@": path.resolve("./src"),
		},
	},
});
