import asyncio
import json
import sys

import jinja2
from loguru import logger
from medium_parser.core import MediumParser
from database_lib import SQLiteCacheBackend

jinja2_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("./"),
)

async def safe_main():
    try:
        await main()
    except Exception as ex:
        logger.exception(ex)


async def main():
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    # logger.add(sys.stderr, level="TRACE")
    logger.add("trace.log", level="TRACE")

    # dl = await MediumParser.from_url("")
    sqlite = SQLiteCacheBackend("test_db.sqlite")
    sqlite.init_db()
    dl = MediumParser("ef85d8e72883", sqlite, 8, "localhost")
    query_result = await dl.query(use_cache=False)

    with open("query_result.json", "w") as f:
        json.dump(query_result, f, indent=2)

    result = await dl.render_as_html()

    with open("medium.html", "w") as f:
        template = jinja2_env.get_template("example_base_template.html")
        template_result = template.render(body_template=result.data)
        f.write(template_result)

    print("See medium.html for the result. Press CTRL-C to exit.")
    sys.exit()


if __name__ == "__main__":
    asyncio.run(safe_main())
