/**
 * Initialize lazy loading for iframes in the article content.
 * This works with iframes that are rendered via {@html content}.
 */
export function initializeLazyIframes(rootSelector: string = '.prose') {
	const root = document.querySelector(rootSelector);
	if (!root) return;

	const iframes = root.querySelectorAll('iframe');
	
	iframes.forEach((iframe) => {
		// Skip if already processed
		if (iframe.dataset.lazyInitialized) return;
		iframe.dataset.lazyInitialized = 'true';

		// Store the original src and remove it
		const src = iframe.src || iframe.dataset.src;
		if (!src) return;

		iframe.removeAttribute('src');
		iframe.dataset.src = src;

		// Add loading styles
		iframe.style.opacity = '0';
		iframe.style.transition = 'opacity 300ms ease';

		// Create skeleton placeholder
		const wrapper = document.createElement('div');
		wrapper.style.position = 'relative';
		wrapper.style.width = iframe.width ? `${iframe.width}px` : '100%';
		wrapper.style.height = iframe.height ? `${iframe.height}px` : '315px';
		
		const skeleton = document.createElement('div');
		skeleton.className = 'animate-pulse bg-zinc-200 dark:bg-zinc-700 rounded-lg absolute inset-0';
		
		iframe.parentNode?.insertBefore(wrapper, iframe);
		wrapper.appendChild(skeleton);
		wrapper.appendChild(iframe);

		// Set up intersection observer
		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						const targetIframe = entry.target as HTMLIFrameElement;
						const lazySrc = targetIframe.dataset.src;
						
						if (lazySrc) {
							targetIframe.src = lazySrc;
							targetIframe.onload = () => {
								targetIframe.style.opacity = '1';
								skeleton.remove();
							};
							targetIframe.onerror = () => {
								targetIframe.style.opacity = '1';
								skeleton.textContent = 'Failed to load';
								skeleton.className = 'flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 text-zinc-400 absolute inset-0';
							};
						}
						
						observer.disconnect();
					}
				});
			},
			{
				rootMargin: '200px',
				threshold: 0
			}
		);

		observer.observe(iframe);
	});
}
