import asyncio
import json
import sys

import jinja2
from loguru import logger
from medium_parser.core import MediumParser

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
    # logger.add(sys.stderr, level="INFO")
    logger.add(sys.stderr, level="TRACE")

    # dl = await MediumParser.from_url("")
    dl = MediumParser("3d8e0ba02d10", 8, "localhost")
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
