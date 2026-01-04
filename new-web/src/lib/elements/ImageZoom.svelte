<script>
	import mediumZoom from 'medium-zoom';

	/** @type {string | undefined} */
	export let src = undefined;
	/** @type {string | undefined} */
	export let alt = undefined;
	/** @type {string | undefined} */
	export let zoomSrc = undefined;
	/** @type {import('medium-zoom').ZoomOptions | undefined} */
	export let options = undefined;

	/** @type {import('medium-zoom').Zoom | null} */
	let zoom = null;

	function getZoom() {
		if (zoom === null) {
			zoom = mediumZoom(options);
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
</script>

<img {src} {alt} data-zoom-src={zoomSrc} {...$$restProps} use:attachZoom />
