import mediumZoom from 'medium-zoom';
import type { Zoom } from 'medium-zoom';

let zoom: Zoom | null = null;

export function initializeImageZoom(): void {
	// Initialize zoom instance if not already created
	if (zoom === null) {
		zoom = mediumZoom({
			background: 'rgba(0, 0, 0, 0.8)',
			margin: 24,
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
}
