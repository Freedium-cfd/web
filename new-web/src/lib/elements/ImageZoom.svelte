<script>
	import mediumZoom from 'medium-zoom';
	import { onDestroy } from 'svelte';

	/** @type {string | undefined} */
	export let src = undefined;
	/** @type {string | undefined} */
	export let alt = undefined;
	/** @type {string | undefined} */
	export let zoomSrc = undefined;
	/** @type {string | undefined} */
	export let caption = undefined;
	/** @type {import('medium-zoom').ZoomOptions | undefined} */
	export let options = undefined;

	/** @type {import('medium-zoom').Zoom | null} */
	let zoom = null;
	/** @type {HTMLDivElement | null} */
	let captionElement = null;

	function getZoom() {
		if (zoom === null) {
			const defaultOptions = {
				background: 'rgba(0, 0, 0, 0.8)',
				margin: 24,
			};
			zoom = mediumZoom({ ...defaultOptions, ...options });

			// Add event listeners to show/hide caption
			zoom.on('open', (event) => {
				/** @type {HTMLImageElement | null} */
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

		return zoom;
	}

	/**
	 * @param {HTMLImageElement} image
	 */
	function attachZoom(image) {
		const zoom = getZoom();
		zoom.attach(image);

		return {
			/** @param {import('medium-zoom').ZoomOptions} newOptions */
			update(newOptions) {
				zoom.update(newOptions);
			},
			destroy() {
				zoom.detach();
			}
		};
	}

	onDestroy(() => {
		if (captionElement) {
			captionElement.remove();
			captionElement = null;
		}
	});
</script>

<img {src} {alt} data-zoom-src={zoomSrc} data-caption={caption} {...$$restProps} use:attachZoom />
