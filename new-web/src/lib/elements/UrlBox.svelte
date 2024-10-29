<script lang="ts">
	import { goto } from '$app/navigation';
	let url = '';

	const handleSubmit = async (event: Event) => {
		event.preventDefault();
		await goto(`/${url}`);
	};
</script>

<div class="w-full p-8 mt-8 bg-white rounded-md shadow-md md:max-w-6xl dark:bg-zinc-800">
	<form
		on:submit={handleSubmit}
		class="flex items-center px-4 py-2 border rounded-md border-zinc-300"
	>
		<svg
			class="w-5 h-5 mr-2 text-zinc-500 dark:text-zinc-100"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M12 6v6m0 0v6m0-6h6m-6 0H6"
			></path>
		</svg>
		<!-- svelte-ignore a11y-autofocus -->
		<input
			type="text"
			placeholder="Enter Medium post link"
			class="w-full bg-transparent border-zinc-300 focus:outline-none text-primary"
			autofocus
			bind:value={url}
		/>
		<button
			type="submit"
			class="px-4 py-2 ml-2 text-white rounded-md bg-primary hover:bg-primary/90 focus:outline-none"
		>
			Unlock
		</button>
	</form>
</div>
