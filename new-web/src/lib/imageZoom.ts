import mediumZoom from 'medium-zoom';
import type { Zoom } from 'medium-zoom';

let zoom: Zoom | null = null;
let captionElement: HTMLDivElement | null = null;

export function initializeImageZoom(): void {
	// Initialize zoom instance if not already created
	if (zoom === null) {
		zoom = mediumZoom({
			background: 'rgba(0, 0, 0, 0.8)',
			margin: 24,
		});

		// Add event listeners to show/hide caption
		zoom.on('open', (event) => {
			const img = event.target instanceof HTMLImageElement ? event.target : null;
			const captionText = img?.getAttribute('data-caption');

			if (captionText && !captionElement) {
				captionElement = document.createElement('div');
				captionElement.style.position = 'fixed';
				captionElement.style.bottom = '40px';
				captionElement.style.left = '50%';
				captionElement.style.transform = 'translateX(-50%)';
				captionElement.style.color = 'white';
				captionElement.style.fontSize = '16px';
				captionElement.style.fontStyle = 'italic';
				captionElement.style.textAlign = 'center';
				captionElement.style.maxWidth = '80%';
				captionElement.style.padding = '10px 20px';
				captionElement.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
				captionElement.style.borderRadius = '8px';
				captionElement.style.zIndex = '9999';
				captionElement.style.pointerEvents = 'none';
				captionElement.textContent = captionText;
				document.body.appendChild(captionElement);
			}
		});

		zoom.on('close', () => {
			if (captionElement) {
				captionElement.remove();
				captionElement = null;
			}
		});
	}

	// Find all zoomable images (both preview image and article prose images)
	// .prose-image class is added to all img elements that should support zoom
	const images = document.querySelectorAll<HTMLImageElement>('.prose-image');

	// Attach zoom to each image
	images.forEach((img) => {
		zoom?.attach(img);
	});
}

export function cleanupImageZoom(): void {
	if (zoom) {
		zoom.detach();
	}
	if (captionElement) {
		captionElement.remove();
		captionElement = null;
	}
}
