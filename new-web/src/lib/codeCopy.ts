export function initializeCodeCopyButtons(): void {
	document.querySelectorAll<HTMLElement>(".code-copy-btn").forEach((button) => {
		button.addEventListener("click", handleCodeCopy);
	});
}

function handleCodeCopy(event: Event): void {
	const button = event.currentTarget as HTMLElement;
	if (button.classList.contains("copied")) return;

	const code = button.dataset.code ?? "";
	const toggleMs = parseInt(button.dataset.toggleMs ?? "3000", 10);
	const ready = button.querySelector<HTMLElement>(".ready");
	const success = button.querySelector<HTMLElement>(".success");

	navigator.clipboard.writeText(code);
	button.classList.add("copied");
	if (ready) ready.style.display = "none";
	if (success) success.style.display = "block";

	setTimeout(() => {
		button.classList.remove("copied");
		if (ready) ready.style.display = "block";
		if (success) success.style.display = "none";
	}, toggleMs);

	window.dispatchEvent(
		new CustomEvent("toast", {
			detail: { message: "Copied to clipboard" },
		}),
	);
}
