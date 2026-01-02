<script lang="ts">
	import { Command as CommandPrimitive } from "cmdk-sv";
	import { cn } from "$lib/utils.js";
	type $$Props = CommandPrimitive.GroupProps;

	let className: string | undefined | null = undefined;
	export { className as class };
</script>

<CommandPrimitive.Group
	class={cn(
		"text-foreground **:data-cmdk-group-heading:text-muted-foreground overflow-hidden p-1 **:data-cmdk-group-heading:px-2 **:data-cmdk-group-heading:py-1.5 **:data-cmdk-group-heading:text-xs **:data-cmdk-group-heading:font-medium",
		className
	)}
	{...$$restProps}
>
	<slot />
</CommandPrimitive.Group>
