import { visit } from 'unist-util-visit';

function remarkMixtapeEmbed() {
	return (tree) => {
		visit(tree, 'paragraph', (node) => {
			const text = node.children[0].value;
			const mixtapeRegex = /\[!\[(.*?)\]\((.*?)\)\]\((.*?)\)\n>(.*?)\n>(.*?)\n/;

			const match = mixtapeRegex.exec(text);
			if (match) {
				const [, altText, linkUrl, imageUrl, title, description] = match;
				const siteName = new URL(linkUrl).hostname;

				node.type = 'html';
				node.value = `
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
				`;
				node.children = undefined;
			}
		});
	};
}

export default remarkMixtapeEmbed;
