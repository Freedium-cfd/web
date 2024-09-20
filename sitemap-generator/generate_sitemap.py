from aiohttp_client_cache import CachedSession, SQLiteBackend
import asyncio
from loguru import logger
import json
from jinja2 import Template

from progress.bar import Bar

import datetime

MEDIUM_URLS = []


async def main():
    async with CachedSession(cache=SQLiteBackend('medium_cache.sqlite')) as session:
        responses = [resp async for resp in session.cache.responses.values()]
        bar = Bar('Processing...', max=len(responses))
        for resp in responses:
            body = json.loads(resp._body)
            lastmod_date = datetime.datetime.now().strftime('%Y-%m-%d')
            url = body["data"]["post"]["mediumUrl"] if body["data"]["post"] is not None else None
            if url is None:
                logger.error("Ignoring non valid Medium post data")
                bar.next()
                continue
            MEDIUM_URLS.append({"url": url, "lastmod": lastmod_date, "changefreq": "monthly", "priority": "1.0"})
            bar.next()

        bar.finish()

    sitemap_template = '''<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {% for page in pages %}
        <url>
            <loc>{{page.url|safe}}</loc>
            <lastmod>{{page.lastmod}}</lastmod>
            <changefreq>{{page.changefreq}}</changefreq>
            <priority>{{page.priority}}</priority>
        </url>
        {% endfor %}
    </urlset>'''

    template = Template(sitemap_template)

    sitemap_output = template.render(pages=MEDIUM_URLS)
    with open("static/sitemap.xml", 'w') as f:
        f.write(sitemap_output)

    logger.info("Done")

asyncio.run(main())
