from aiohttp_client_cache import CachedSession, SQLiteBackend
import asyncio
import json
from jinja2 import Template

import datetime

from icecream import ic

MEDIUM_URLS = []


async def main():
    async with CachedSession(cache=SQLiteBackend('medium_cache.sqlite')) as session:
        async for resp in session.cache.responses.values():
            body = json.loads(resp._body)
            ic("Processing")
            lastmod_date = datetime.datetime.now().strftime('%Y-%m-%d')
            MEDIUM_URLS.append({"url": body["data"]["post"]["mediumUrl"], "lastmod": lastmod_date, "changefreq": "monthly", "priority": "1.0"})

    sitemap_template ='''<?xml version="1.0" encoding="UTF-8"?>
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
    with open("scripts/sitemap.xml", 'w') as f:
        f.write(sitemap_output)

    ic("DONE!")

asyncio.run(main())
