import asyncio
import math
import textwrap
import typing
import urllib.parse
from typing import Optional

import jinja2
import tld
from asyncer import asyncify
from loguru import logger

from rl_string_helper import RLStringHelper, parse_markups, split_overlapping_ranges

from . import jinja_env
from .exceptions import InvalidMediumPostID, InvalidMediumPostURL, InvalidURL, MediumParserException, MediumPostQueryError
from .medium_api import query_post_by_id
from .models.html_result import HtmlResult
from .time import convert_datetime_to_human_readable
from .utils import correct_url, extract_hex_string, getting_percontage_of_match, is_has_valid_medium_post_id, is_valid_medium_url, is_valid_url, resolve_medium_url

if typing.TYPE_CHECKING:
    from database_lib import SQLiteCacheBackend


class MediumParser:
    __slots__ = ("cache", "host_address", "jinja_template", "post_template", "timeout", "auth_cookies")

    def __init__(self, cache: "SQLiteCacheBackend", timeout: int, host_address: str, auth_cookies: Optional[str] = None, template_folder: str = "./templates"):
        self.timeout = timeout
        self.cache = cache
        self.host_address = host_address
        self.auth_cookies = auth_cookies
        self.jinja_template = jinja2.Environment(loader=jinja2.FileSystemLoader(template_folder))
        self.post_template = self.jinja_template.get_template("post.html")

    async def resolve(self, unknown: str) -> str:
        logger.debug(f"We got some unknown data: {unknown=}. Trying resolve them...///")

        if is_has_valid_medium_post_id(unknown):
            logger.debug("Seems like it's valid post_id")
            return extract_hex_string(unknown)

        logger.debug("...maybe it's URL. Let's checkout...")
        post_id = await self.resolve_url(unknown)
        return post_id

    async def resolve_url(self, url: str) -> str:
        sanitized_url = correct_url(url)
        if not is_valid_url(url) or not await is_valid_medium_url(sanitized_url):
            raise InvalidURL(f"Invalid Medium URL: {sanitized_url}")

        post_id = await resolve_medium_url(sanitized_url, self.timeout)
        if not post_id:
            raise InvalidMediumPostURL(f"Could not find Medium post ID for URL: {sanitized_url}")

        return post_id

    async def delete_from_cache(self, post_id: str):
        self.cache.delete(post_id)
        return True

    async def get_post_data_from_cache(self, post_id: str):
        async def _get_from_cache():
            logger.debug("Using cache backend")
            post_data = self.cache.pull(post_id)
            if post_data:
                logger.debug("post query was found on cache")
                return post_data.json()
            logger.debug(f"No data found in cache by {post_id}")
            return None

        try:
            return await asyncio.wait_for(_get_from_cache(), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.debug("Timeout while waiting for cache")
            return None
        except Exception as e:
            logger.error(f"Error while waiting for cache: {e}")
            return None

    async def get_post_data_from_api(self, post_id: str):
        async def _get_from_api():
            logger.debug("Using API to gather post data")
            try:
                return await query_post_by_id(post_id, self.timeout, self.auth_cookies)
            except Exception as ex:
                logger.debug("Error while querying post data from Medium API")
                logger.exception(ex)
                return None

        try:
            return await asyncio.wait_for(_get_from_api(), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.debug("Timeout while waiting for cache")
            return None
        except Exception as e:
            logger.error(f"Error while waiting for cache: {e}")
            return None

    async def query_get(self, post_id: str, use_cache: bool, force_cache: bool = False):
        cache_used = True
        post_data = await self.get_post_data_from_cache(post_id) if use_cache else None

        if not post_data and not force_cache:
            logger.debug("Getting value from cache failed, using API")
            cache_used = False
            post_data = await self.get_post_data_from_api(post_id)

        return post_data, cache_used

    async def query(self, post_id: str, use_cache: bool = True, retry: int = 2, force_cache: bool = False):
        logger.debug(f"Medium QUERY: {use_cache=}, {retry=}, {force_cache=}")

        post_data, is_cache_used = None, False

        attempt = 0
        reason = None
        while not post_data and attempt < retry:
            try:
                post_data, is_cache_used = await self.query_get(post_id, use_cache, force_cache)

                if not post_data:
                    reason = "No post data returned"
                elif not isinstance(post_data, dict):
                    reason = f"Post data is not a dictionary: {post_data=}"
                elif post_data.get("error"):
                    reason = f"Post data contains an error: {post_data=}"
                elif not post_data.get("data"):
                    reason = f"Post data missing 'data' key: {post_data=}"
                elif not post_data.get("data", {}).get("post"):
                    reason = f"Post data missing 'data.post' key: {post_data=}"

                if reason is None:
                    logger.debug("Post data was successfully queried")
                    break
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with exception: {e}")
                logger.debug(f"Retrying in {2 ** attempt} seconds...")
                await asyncio.sleep(2**attempt)
            finally:
                attempt += 1
        else:
            if not reason:
                reason = "Unknown"

            raise MediumPostQueryError(f"Could not query post by ID from API: {post_id}. Reason: {reason}")

        if not is_cache_used:
            logger.debug("Pushing post data to cache")
            self.cache.push(post_id, post_data)

        logger.trace(f"Query: done")
        return post_data

    def _parse_and_render_content_html_post(self, content: dict, title: str, subtitle: str, preview_image_id: str, highlights: list, tags: list) -> tuple[list, str, str]:
        paragraphs = content["bodyModel"]["paragraphs"]
        tags_list = [tag["displayTitle"] for tag in tags]
        out_paragraphs: list[str] = []
        current_pos = 0

        def parse_paragraph_text(text: str, markups: list, is_code: bool = False) -> str:
            if is_code:
                quote_html_type = ["minimal"]
            else:
                quote_html_type = ["full"]
            text_formater = RLStringHelper(text, quote_html_type=quote_html_type)

            parsed_markups = parse_markups(markups)
            fixed_markups = split_overlapping_ranges(parsed_markups)

            for markup in fixed_markups:
                text_formater.set_template(markup["start"], markup["end"], markup["template"])

            return text_formater

        while len(paragraphs) > current_pos:
            paragraph = paragraphs[current_pos]
            logger.trace(f"Current paragraph #{current_pos} data: {paragraph}")

            # For debugging stuff...
            # if paragraph["id"] != "":
            #     current_pos += 1
            #     continue

            if current_pos in range(4):
                if paragraph["type"] in ["H3", "H4", "H2"]:
                    if getting_percontage_of_match(paragraph["text"], title) > 80:
                        if title.endswith("…"):
                            logger.trace("Title was detected, replace...")
                            title = paragraph["text"]
                        else:
                            logger.trace("Title was detected, ignore...")
                        current_pos += 1
                        continue
                if paragraph["type"] in ["H4"]:
                    if paragraph["text"] in tags_list:
                        logger.trace("Tag was detected, ignore...")
                        current_pos += 1
                        continue
                if paragraph["type"] in ["H4", "P"]:
                    is_paragraph_subtitle = getting_percontage_of_match(paragraph["text"], subtitle) > 80
                    if is_paragraph_subtitle and not subtitle.endswith("…"):
                        logger.trace("Subtitle was detected, ignore...")
                        subtitle = paragraph["text"]
                        current_pos += 1
                        continue
                    elif subtitle and subtitle.endswith("…") and len(paragraph["text"]) > 100:
                        subtitle = ""
                elif paragraph["type"] == "IMG":
                    if paragraph["metadata"] and paragraph["metadata"]["id"] == preview_image_id:
                        logger.trace("Preview image was detected, ignore...")
                        current_pos += 1
                        continue

            if paragraph["text"] is not None:
                text_formater = parse_paragraph_text(paragraph["text"], paragraph["markups"])
            else:
                text_formater = None

                for highlight in highlights:
                    for highlight_paragraph in highlight["paragraphs"]:
                        if highlight_paragraph["name"] == paragraph["name"]:
                            logger.trace("Apply highlight to this paragraph")
                            if highlight_paragraph["text"] != text_formater.get_text():
                                logger.warning("Highlighted text and paragraph text are not the same! Skip...")
                                break
                            quote_markup_template = '<mark class="bg-emerald-300">{{ text }}</mark>'
                            text_formater.set_template(
                                highlight["startOffset"],
                                highlight["endOffset"],
                                quote_markup_template,
                            )
                            break

            if paragraph["type"] == "H2":
                css_class = []
                if out_paragraphs:
                    css_class.append("pt-12")
                header_template = jinja_env.from_string('<h2 class="font-bold font-sans break-normal text-gray-900 dark:text-gray-100 text-1xl md:text-2xl {{ css_class }}">{{ text }}</h2>')
                header_template_rendered = header_template.render(text=text_formater.get_text(), css_class="".join(css_class))
                out_paragraphs.append(header_template_rendered)
            elif paragraph["type"] == "H3":
                css_class = []
                if out_paragraphs:
                    css_class.append("pt-12")
                header_template = jinja_env.from_string('<h3 class="font-bold font-sans break-normal text-gray-900 dark:text-gray-100 text-1xl md:text-2xl {{ css_class }}">{{ text }}</h3>')
                header_template_rendered = header_template.render(text=text_formater.get_text(), css_class="".join(css_class))
                out_paragraphs.append(header_template_rendered)
            elif paragraph["type"] == "H4":
                css_class = []
                if out_paragraphs:
                    css_class.append("pt-8")
                header_template = jinja_env.from_string('<h4 class="font-bold font-sans break-normal text-gray-900 dark:text-gray-100 text-l md:text-xl {{ css_class }}">{{ text }}</h4>')
                header_template_rendered = header_template.render(text=text_formater.get_text(), css_class="".join(css_class))
                out_paragraphs.append(header_template_rendered)
            elif paragraph["type"] == "IMG":
                image_template = jinja_env.from_string(
                    '<div class="mt-7"><img alt="{{ paragraph.metadata.alt }}" class="pt-5 lazy m-auto" role="presentation" data-src="https://miro.medium.com/v2/resize:fit:700/{{ paragraph.metadata.id }}"></div>'
                )
                image_caption_template = jinja_env.from_string("<figcaption class='mt-3 text-sm text-center text-gray-500 dark:text-gray-200'>{{ text }}</figcaption>")
                if paragraph["layout"] == "OUTSET_ROW":
                    image_templates_row = []
                    img_row_template = jinja_env.from_string('<div class="mx-5"><div class="flex flex-row justify-center">{{ images }}</div></div>')
                    image_template_rendered = image_template.render(paragraph=paragraph)
                    image_templates_row.append(image_template_rendered)
                    _tmp_current_pos = current_pos + 1
                    while len(paragraphs) > _tmp_current_pos:
                        _paragraph = paragraphs[_tmp_current_pos]
                        if _paragraph["layout"] == "OUTSET_ROW_CONTINUE":
                            image_template_rendered = image_template.render(paragraph=_paragraph)
                            image_templates_row.append(image_template_rendered)
                        else:
                            break

                        _tmp_current_pos += 1

                    img_row_template_rendered = img_row_template.render(images="".join(image_templates_row))
                    out_paragraphs.append(img_row_template_rendered)

                    current_pos = _tmp_current_pos - 1
                elif paragraph["layout"] == "FULL_WIDTH":
                    logger.warning("IMG: not implemented FULL_WIDTH layout")
                    current_pos += 1
                    continue
                else:
                    image_template_rendered = image_template.render(paragraph=paragraph)
                    out_paragraphs.append(image_template_rendered)
                    if paragraph["text"]:
                        out_paragraphs.append(image_caption_template.render(text=text_formater.get_text()))
            elif paragraph["type"] == "P":
                css_class = ["leading-8"]
                paragraph_template = jinja_env.from_string('<p class="{{ css_class }}">{{ text }}</p>')
                if paragraphs[current_pos - 1]["type"] in ["H4", "H3"]:
                    css_class.append("mt-3")
                else:
                    css_class.append("mt-7")
                paragraph_template_rendered = paragraph_template.render(text=text_formater.get_text(), css_class=" ".join(css_class))
                out_paragraphs.append(paragraph_template_rendered)
            elif paragraph["type"] == "ULI":
                uli_template = jinja_env.from_string('<ul class="list-disc pl-8 mt-2">{{ li }}</ul>')
                li_template = jinja_env.from_string("<li class='mt-3'>{{ text }}</li>")
                li_templates = []

                _tmp_current_pos = current_pos
                while len(paragraphs) > _tmp_current_pos:
                    _paragraph = paragraphs[_tmp_current_pos]
                    if _paragraph["type"] == "ULI":
                        text_formater = parse_paragraph_text(_paragraph["text"], _paragraph["markups"])
                        li_template_rendered = li_template.render(text=text_formater.get_text())
                        li_templates.append(li_template_rendered)
                    else:
                        break

                    _tmp_current_pos += 1

                uli_template_rendered = uli_template.render(li="".join(li_templates))
                out_paragraphs.append(uli_template_rendered)

                current_pos = _tmp_current_pos - 1
            elif paragraph["type"] == "OLI":
                ol_template = jinja_env.from_string('<ol class="list-decimal pl-8 mt-2">{{ li }}</ol>')
                li_template = jinja_env.from_string("<li class='mt-3'>{{ text }}</li>")
                li_templates = []

                _tmp_current_pos = current_pos
                while len(paragraphs) > _tmp_current_pos:
                    _paragraph = paragraphs[_tmp_current_pos]
                    if _paragraph["type"] == "OLI":
                        text_formater = parse_paragraph_text(_paragraph["text"], _paragraph["markups"])
                        li_template_rendered = li_template.render(text=text_formater.get_text())
                        li_templates.append(li_template_rendered)
                    else:
                        break

                    _tmp_current_pos += 1

                ol_template_rendered = ol_template.render(li="".join(li_templates))
                out_paragraphs.append(ol_template_rendered)

                current_pos = _tmp_current_pos - 1
            elif paragraph["type"] == "PRE":
                pre_template = jinja_env.from_string('<pre class="mt-7 flex flex-col justify-center border dark:border-gray-700">{{code_block}}</pre>')
                code_block_template = jinja_env.from_string('<code class="p-2 bg-gray-100 dark:bg-gray-900 overflow-x-auto {{ code_css_class }}">{{ text }}</code>')

                code_css_class = []
                if paragraph["codeBlockMetadata"] and paragraph["codeBlockMetadata"]["lang"] is not None:
                    code_css_class.append(f'language-{paragraph["codeBlockMetadata"]["lang"]}')
                else:
                    code_css_class.append("nohighlight")
                    # code_css_class.append("auto")

                code_list = []
                _tmp_current_pos = current_pos
                while len(paragraphs) > _tmp_current_pos:
                    _paragraph = paragraphs[_tmp_current_pos]
                    if _paragraph["type"] == "PRE":
                        text_formater = parse_paragraph_text(_paragraph["text"], _paragraph["markups"], is_code=True)
                        code_list.append(text_formater.get_text())
                    else:
                        break

                    _tmp_current_pos += 1

                code_block_template_rendered = code_block_template.render(text="\n".join(code_list), code_css_class=" ".join(code_css_class))
                pre_template_rendered = pre_template.render(code_block=code_block_template_rendered)

                out_paragraphs.append(pre_template_rendered)
                current_pos = _tmp_current_pos - 1
            elif paragraph["type"] == "BQ":
                bq_template = jinja_env.from_string(
                    '<blockquote style="box-shadow: inset 3px 0 0 0 rgb(209 207 239 / var(--tw-bg-opacity));" class="px-5 pt-3 pb-3 mt-5"><p class="font-italic">{{ text }}</p></blockquote>'
                )
                bq_template_rendered = bq_template.render(text=text_formater.get_text())
                logger.trace(bq_template_rendered)
                out_paragraphs.append(bq_template_rendered)
            elif paragraph["type"] == "PQ":
                pq_template = jinja_env.from_string('<blockquote class="mt-7 text-2xl ml-5 text-gray-600 dark:text-gray-300"><p>{{ text }}</p></blockquote>')
                pq_template_rendered = pq_template.render(text=text_formater.get_text())
                logger.trace(pq_template_rendered)
                out_paragraphs.append(pq_template_rendered)
            elif paragraph["type"] == "MIXTAPE_EMBED":
                # TODO: redirect all Medium embeding articles to Fredium
                embed_template = jinja_env.from_string(
                    '<div class="border border-gray-300 p-2 mt-7 items-center overflow-hidden"><a rel="noopener follow" href="{{ url }}" target="_blank"> <div class="flex flex-row justify-between p-2 overflow-hidden"><div class="flex flex-col justify-center p-2"><h2 class="text-black dark:text-gray-100 text-base font-bold">{{ embed_title }}</h2><div class="mt-2 block"><h3 class="text-grey-darker text-sm">{{ embed_description }}</h3></div><div class="mt-5"><p class="text-grey-darker text-xs">{{ embed_site }}</p></div></div><div class="relative flex flew-row h-40 w-60"><div class="lazy absolute inset-0 bg-cover bg-center" data-bg="https://miro.medium.com/v2/resize:fit:320/{{ paragraph.mixtapeMetadata.thumbnailImageId }}"></div></div></div> </a></div>'
                )
                if paragraph.get("mixtapeMetadata") is not None:
                    url = paragraph["mixtapeMetadata"]["href"]
                else:
                    logger.warning("Ignore MIXTAPE_EMBED paragraph type, since we can't get url")
                    current_pos += 1
                    continue

                text_raw = paragraph["text"]

                if len(paragraph["markups"]) != 3:
                    logger.warning("Ignore MIXTAPE_EMBED paragraph type, since we can't split text")
                    current_pos += 1
                    continue

                title_range = paragraph["markups"][1]
                description_range = paragraph["markups"][2]

                logger.trace(f"{title_range=}")
                logger.trace(f"{description_range=}")

                embed_title = text_raw[title_range["start"] : title_range["end"]]
                embed_description = text_raw[description_range["start"] : description_range["end"]]

                logger.trace(f"{embed_title=}")
                logger.trace(f"{embed_description=}")

                try:
                    embed_site = tld.get_fld(url)
                except Exception as ex:
                    logger.warning(f"Can't get embed site fld: {ex}. Using custom logic...")
                    parsed_url = urllib.parse.urlparse(url)
                    embed_site = parsed_url.hostname

                logger.trace(f"{embed_site=}")

                embed_template_rendered = embed_template.render(paragraph=paragraph, url=url, embed_title=embed_title, embed_description=embed_description, embed_site=embed_site)
                out_paragraphs.append(embed_template_rendered)
            elif paragraph["type"] == "IFRAME":
                iframe_template = jinja_env.from_string(
                    '<div class="mt-7"><iframe class="lazy w-full" data-src="{{ host_address }}/render_iframe/{{ iframe_id }}" allowfullscreen="" frameborder="0" scrolling="no"></iframe></div>'
                )
                iframe_template_rendered = iframe_template.render(host_address=self.host_address, iframe_id=paragraph["iframe"]["mediaResource"]["id"])
                out_paragraphs.append(iframe_template_rendered)

            else:
                logger.error(f"Unknown {paragraph['type']}: {paragraph}")

            current_pos += 1

        return out_paragraphs, title, subtitle

    async def render_as_html(self, post_id: str):
        post_data = await self.query(post_id)
        try:
            result = await self._render_as_html(post_data, post_id)
        except Exception as ex:
            raise ex
        else:
            return result

    async def generate_metadata(self, post_data: dict, post_id: str, as_dict: bool = False) -> tuple:
        title = RLStringHelper(post_data["data"]["post"]["title"], ["minimal"]).get_text()
        subtitle = RLStringHelper(post_data["data"]["post"]["previewContent"]["subtitle"]).get_text()
        description = RLStringHelper(textwrap.shorten(subtitle, width=100, placeholder="...")).get_text()
        preview_image_id = post_data["data"]["post"]["previewImage"]["id"]
        creator = post_data["data"]["post"]["creator"]
        collection = post_data["data"]["post"]["collection"]
        url = post_data["data"]["post"]["mediumUrl"]

        reading_time = math.ceil(post_data["data"]["post"]["readingTime"])
        free_access = "No" if post_data["data"]["post"]["isLocked"] else "Yes"
        updated_at = convert_datetime_to_human_readable(post_data["data"]["post"]["updatedAt"])
        first_published_at = convert_datetime_to_human_readable(post_data["data"]["post"]["firstPublishedAt"])
        tags = post_data["data"]["post"]["tags"]

        if as_dict:
            return {
                "post_id": post_id,
                "title": title,
                "subtitle": subtitle,
                "description": description,
                "url": url,
                "creator": creator,
                "collection": collection,
                "reading_time": reading_time,
                "free_access": free_access,
                "updated_at": updated_at,
                "first_published_at": first_published_at,
                "preview_image_id": preview_image_id,
                "tags": tags,
            }

        return title, subtitle, description, url, creator, collection, reading_time, free_access, updated_at, first_published_at, preview_image_id, tags

    async def _render_as_html(self, post_data: dict, post_id: str) -> "HtmlResult":
        # Generate metadata in parallel
        metadata_task = asyncio.create_task(self.generate_metadata(post_data, post_id))

        # Parse and render content in parallel
        content, title, subtitle = await asyncify(self._parse_and_render_content_html_post)(
            post_data["data"]["post"]["content"],
            post_data["data"]["post"]["title"],
            post_data["data"]["post"]["previewContent"]["subtitle"],
            post_data["data"]["post"]["previewImage"]["id"],
            post_data["data"]["post"]["highlights"],
            post_data["data"]["post"]["tags"],
        )

        # Await metadata
        title, subtitle, description, url, creator, collection, reading_time, free_access, updated_at, first_published_at, preview_image_id, tags = await metadata_task

        post_page_title_raw = "{{ title }} | by {{ creator.name }}"
        if collection:
            post_page_title_raw += " | in {{ collection.name }}"
        post_page_title = jinja_env.from_string(post_page_title_raw)
        post_page_title_rendered = post_page_title.render(title=title, creator=creator, collection=collection)

        post_context = {
            "subtitle": subtitle,
            "title": title,
            "url": url,
            "creator": creator,
            "collection": collection,
            "readingTime": reading_time,
            "freeAccess": free_access,
            "updatedAt": updated_at,
            "firstPublishedAt": first_published_at,
            "previewImageId": preview_image_id,
            "content": content,
            "tags": tags,
        }
        post_template_rendered = self.post_template.render(post_context)

        return HtmlResult(post_page_title_rendered, description, url, post_template_rendered)

    async def render_as_markdown(self) -> str:
        raise NotImplementedError("Markdown rendering is not implemented. Please use HTML rendering instead")
