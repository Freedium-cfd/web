import { visit } from 'unist-util-visit';
import type { Root, Html, Parent } from 'mdast';

function remarkMixtapeEmbed() {
	return (tree: Root) => {
		visit(tree, 'paragraph', (node, index, parent) => {
			const firstChild = node.children[0];
			if (!('value' in firstChild)) return;
			
			const text = firstChild.value;
			if (typeof text !== 'string') return;
			
			const mixtapeRegex = /\[!\[(.*?)\]\((.*?)\)\]\((.*?)\)\n>(.*?)\n>(.*?)\n/;

			const match = mixtapeRegex.exec(text);
			if (match && parent && typeof index === 'number') {
				const [, _altText, linkUrl, imageUrl, title, description] = match;
				const siteName = new URL(linkUrl).hostname;

				const htmlNode: Html = {
					type: 'html',
					value: `
					<div class="mixtape-embed">
						<a href="${linkUrl}" target="_blank" rel="noopener follow">
							<div class="mixtape-content">
								<div class="mixtape-text">
									<h2>${title}</h2>
									<div class="mixtape-description">
										<h3>${description}</h3>
									</div>
									<div class="mixtape-site">
										<p>${siteName}</p>
									</div>
								</div>
								<div class="mixtape-image">
									<div class="mixtape-image-inner" style="background-image: url(${imageUrl})"></div>
								</div>
							</div>
						</a>
					</div>
				`
				};
				(parent as Parent).children[index] = htmlNode;
			}
		});
	};
}

export default remarkMixtapeEmbed;
