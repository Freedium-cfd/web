export function initializeCodeCopyButtons() {
	document.querySelectorAll(".code-copy-btn").forEach((button) => {
		button.addEventListener("click", handleCodeCopy);
	});
}

function handleCodeCopy(event) {
	const button = event.currentTarget;
	if (button.classList.contains("copied")) return;

	const code = button.dataset.code;
	const toggleMs = parseInt(button.dataset.toggleMs, 10);
	const ready = button.querySelector(".ready");
	const success = button.querySelector(".success");

	navigator.clipboard.writeText(code);
	button.classList.add("copied");
	ready.style.display = "none";
	success.style.display = "block";

	setTimeout(() => {
		button.classList.remove("copied");
		ready.style.display = "block";
		success.style.display = "none";
	}, toggleMs);

	window.dispatchEvent(
		new CustomEvent("toast", {
			detail: { message: "Copied to clipboard" },
		}),
	);
}
