from loguru import logger

from .logger_trace import trace
from .utils import quote_html, quote_symbol

from jinja2 import Environment, DebugUndefined, Template

jinja_env = Environment(undefined=DebugUndefined)


# TODO: doc!
class StringAsignmentMix:
    __slots__ = ("string", "string_list")

    def __init__(self, string: str):
        if isinstance(string, str):
            self.string = string
        elif isinstance(string, StringAsignmentMix):
            self.string = string.string
        else:
            raise ValueError(f"Incorrect string type: {type(string)}")

        self.string_list = list(self.string)

    def __render_string(self):
        self.string = "".join(self.string_list)

    def __len__(self):
        self.__render_string()
        return len(self.string)

    def pop(self, key):
        self.string_list.pop(key)
        # self.__render_string()
        return self

    def encode(self, encoding: str):
        self.__render_string()
        return self.string.encode(encoding, "surrogatepass")

    def insert(self, key: int, value):
        self.string_list.insert(key, value)
        # self.__render_string()
        return self

    def __setitem__(self, key, value):
        logger.trace(f"Calling __setitem__ with {key=}, {value=}")
        self.string_list[key] = value
        return self

    def __getitem__(self, key):
        logger.trace(f"Calling __getitem__ with {key=}")
        str_list_res = self.string_list[key]
        return "".join(str_list_res)

    def __str__(self):
        self.__render_string()
        return self.string

    def __repr__(self):
        self.__render_string()
        return self.__str__()


# TODO: more clarified description
"""
In JavaScript, the `length` property of a String object returns the number of code units (bytes) in the string, which makes use of UTF-16 encoding.
In UTF-16, each Unicode character may be encoded as one or two code units (byte). This means that for certain scripts, such as emojis, mathematical symbols, or some Chinese characters,
the value returned by length might not match the actual number of Unicode characters in the string.

Python uses UTF-8 encoding, which each character is encoded as one byte. So here is a workaround to get the actual number of characters and manipulate them in string as in UTF-16 encoding. See pre_utf_16_bang and post_utf_16_bang function. 
"""

# TODO: doc! Who will read this noodles lol?
# TODO: check cases when UTF-16 character can be more that 2 bytes
class RLStringHelper:
    __slots__ = ("string", "templates", "replaces", "quote_html_type", "quote_replaces")

    def __init__(self, string: str, quote_html_type: list[str] = ["full"]):
        self.string = StringAsignmentMix(quote_symbol(string))
        self.templates = []
        self.quote_replaces = []
        self.replaces = []
        self.quote_html_type = quote_html_type

    @trace
    def pre_utf_16_bang(self, string: str, string_pos_matrix: list, _default_bang_char: str = "R"):
        utf_16_bang_list = []
        string_len_utf_16 = len(string.encode("utf-16-le")) // 2
        if string_len_utf_16 == len(string):
            logger.trace("String is doesn't contain multibyte characters")
            return string, string_pos_matrix, utf_16_bang_list

        i = 0
        while len(string) - 1 > i:
            new_i = string_pos_matrix[i]
            char = string[new_i]
            char_len = len(char.encode("utf-16-le")) // 2
            if char_len == 2:
                char_len_dif = char_len - 1
                logger.trace(char_len_dif)
                logger.trace(f"'{char}' char is two bytes")
                # logger.trace(f"'{char}' char is multibyte")
                char_present = _default_bang_char * char_len_dif
                logger.trace(f"{char_present=}")
                string, string_pos_matrix = self._paste_char(string, string_pos_matrix, new_i + 1, char_present)
                i += 1
                utf_16_bang_list.append((i, char_len_dif, i))
            elif char_len == 1:
                logger.trace(f"'{char}' char is single byte")
                pass
            else:
                ValueError(f"Invalid char: {char}")

            i += 1
        logger.trace(utf_16_bang_list)
        logger.trace(string_pos_matrix)
        logger.trace(len(string))
        return string, string_pos_matrix, utf_16_bang_list

    def _paste_char(self, string: str, string_pos_matrix: list, pos: int, char: str):
        char_len = len(char)
        string_pos_matrix.insert(pos, string_pos_matrix[pos])
        for matrix_i, matrix in enumerate(string_pos_matrix[pos + 1:], pos + 1):
            string_pos_matrix[matrix_i] += char_len
        string.insert(pos, char)
        return string, string_pos_matrix

    def _delete_char(self, string: str, string_pos_matrix: list, pos: int, char_len: int, old_pos: int):
        string.pop(pos)
        string_pos_matrix.pop(old_pos)
        for matrix_i, matrix in enumerate(string_pos_matrix[pos:], pos):
            if isinstance(string_pos_matrix[matrix_i], int):
                string_pos_matrix[matrix_i] -= char_len
            elif isinstance(string_pos_matrix[matrix_i], tuple):
                string_pos_matrix[matrix_i] = (string_pos_matrix[matrix_i][0] - char_len, string_pos_matrix[matrix_i][1] - char_len)
        return string, string_pos_matrix

    @trace
    def post_utf_16_bang(self, string: str, string_pos_matrix: list, utf_16_bang_list: list, _default_bang_char: str = "R"):
        string = StringAsignmentMix(string)

        post_transbang = 0
        for bang_pos, char_len, old_pos in utf_16_bang_list:
            string, string_pos_matrix = self._delete_char(string, string_pos_matrix, bang_pos - post_transbang, char_len, old_pos - post_transbang)
            post_transbang += char_len

        logger.trace(utf_16_bang_list)
        logger.trace(string_pos_matrix)
        return string, string_pos_matrix

    @trace
    def set_template(self, start: int, end: int, template: str):
        if not isinstance(template, Template):
            template = jinja_env.from_string(template)
        lazy_template = (start, end), template
        self.templates.append(lazy_template)
        logger.trace(self.templates)

    @trace
    def set_replace(self, start: int, end: int, replace_with: str):
        lazy_replace = (start, end), replace_with
        self.replaces.append(lazy_replace)
        logger.trace(self.replaces)

    def _render_templates(self, string: str, string_pos_matrix: list, utf_16_bang_list: list):
        if not self.templates:
            return string, string_pos_matrix, utf_16_bang_list

        templates = self.templates
        templates.reverse()

        older_text = string
        updated_text = string

        logger.trace(string_pos_matrix)

        @trace
        def _get_prefix_len(template_raw: Template, inner_char: str = "{"):
            prefix_len = 0
            template = template_raw.render()
            for i in range(len(template)):
                if template[i] == inner_char:
                    return prefix_len
                prefix_len += 1
            else:
                raise ValueError(f"Invalid template: {template}")

        @trace
        def _get_suffix_len(template_raw: Template, outer_char: str = "}"):
            suffix_len = 0
            template = template_raw.render()
            for i in range(len(template) - 1, -1, -1):
                if template[i] == outer_char:
                    return suffix_len
                suffix_len += 1
            else:
                raise ValueError(f"Invalid template: {template}")

        @trace
        def update_nested_positions(start, end, prefix_len, suffix_len):
            logger.trace(len(self.string) == len(string_pos_matrix))
            logger.trace(f"{len(self.string)=}")
            for i in range(end, len(string_pos_matrix)):
                logger.trace(f"{i=}")
                logger.trace(f"{string_pos_matrix[i]=}")
                string_pos_matrix[i] = string_pos_matrix[i] + suffix_len + prefix_len

            for i in range(start, end):
                string_pos_matrix[i] = string_pos_matrix[i] + prefix_len

            for n in range(len(utf_16_bang_list)):
                utf_16_bang = utf_16_bang_list[n]
                if utf_16_bang[2] > end:
                    utf_16_bang_list[n] = (utf_16_bang[0] + prefix_len + suffix_len, utf_16_bang[1], utf_16_bang[2])
                elif utf_16_bang[2] > start:
                    utf_16_bang_list[n] = (utf_16_bang[0] + prefix_len, utf_16_bang[1], utf_16_bang[2])

            logger.trace(string_pos_matrix)
            logger.trace(utf_16_bang_list)

        logger.trace(string_pos_matrix)

        for (start, end), template in templates:
            logger.trace(older_text == updated_text)
            logger.trace(f"{updated_text}")

            logger.trace(f"{start=}, {end=}, template={str(template)}")

            if start >= len(string_pos_matrix):
                logger.warning("Start position is out of range. Ignore...")
                continue
            elif end - 1 >= len(string_pos_matrix):
                logger.warning("End position is out of range. Using workaround.")
                while end - 1 >= len(string_pos_matrix):
                    end -= 1

            if start == end:
                logger.trace("Start and end positions are the same")
                continue

            logger.trace(f"{len(string_pos_matrix)=}")

            new_start, new_end = (
                string_pos_matrix[start],
                string_pos_matrix[end - 1] + 1,
            )

            if new_end < new_start:
                logger.error(f"Invalid negative range: {new_start=} {new_end=}. Ignore.....")
                # we had to ignore this error since we need to release new version
                # raise ValueError(f"Invalid negative range: {new_start=} {new_end=}")
                continue

            logger.trace(f"{new_start=}, {new_end=}")

            logger.trace(updated_text[new_start:new_end])

            older_text = updated_text
            logger.trace(f"{older_text=}")

            context_text = template.render(text=older_text[new_start:new_end])
            logger.trace(context_text)
            updated_text_template = jinja_env.from_string("{{ updated_text[:new_start] }}{{ context_text }}{{updated_text[new_end:]}}")
            updated_text = updated_text_template.render(updated_text=updated_text, context_text=context_text, new_start=new_start, new_end=new_end)
            logger.trace(updated_text)

            prefix_len = _get_prefix_len(template)
            suffix_len = _get_suffix_len(template)

            update_nested_positions(start, end, prefix_len, suffix_len)

            logger.trace(string_pos_matrix)

        return updated_text, string_pos_matrix, utf_16_bang_list

    @trace
    def _render_replaces(self, string: str, string_pos_matrix: list, utf_16_bang_list: list):
        if not self.replaces and not self.quote_replaces:
            return string, string_pos_matrix, utf_16_bang_list

        string = StringAsignmentMix(string)
        replaces = self.replaces + self.quote_replaces

        @trace
        def update_positions(start: int, end: int, replace_len: int, new_start: int, new_end: int):
            pos_len = len(range(start, end))
            logger.trace(pos_len)
            pos_len_diff = replace_len - pos_len
            logger.trace(pos_len_diff)
            for pos_index, pos_matrix in enumerate(string_pos_matrix[end:], end):
                if isinstance(pos_matrix, int):
                    string_pos_matrix[pos_index] += pos_len_diff
                elif isinstance(pos_matrix, tuple):
                    string_pos_matrix[pos_index] = (
                        string_pos_matrix[pos_index][0] + pos_len_diff,
                        string_pos_matrix[pos_index][1] + pos_len_diff,
                    )

            if pos_len_diff != 0:
                for i in range(start, end):
                    if isinstance(string_pos_matrix[i], int):
                        string_pos_matrix[i] = (
                            string_pos_matrix[i],
                            string_pos_matrix[i] + replace_len,
                        )
                    elif isinstance(string_pos_matrix[i], tuple):
                        string_pos_matrix[i] = (
                            string_pos_matrix[i][0] + replace_len,
                            string_pos_matrix[i][1] + replace_len,
                        )

            for n in range(len(utf_16_bang_list)):
                utf_16_bang = utf_16_bang_list[n]
                if utf_16_bang[0] > end:
                    utf_16_bang_list[n] = (utf_16_bang[0] + pos_len_diff, utf_16_bang[1], utf_16_bang[2])

        logger.trace(string_pos_matrix)

        for (start, end), replace_with in replaces:
            new_start, new_end = string_pos_matrix[start], string_pos_matrix[end - 1]
            if isinstance(new_end, int):
                new_end += 1

            if isinstance(new_start, tuple) or isinstance(new_end, tuple):
                if isinstance(new_start, tuple):
                    new_start_tmp = list(range(new_start[0], new_start[1] + 1))
                else:
                    new_start_tmp = [new_start]

                if isinstance(new_end, tuple):
                    new_end_tmp = list(range(new_end[0], new_end[1] + 1))
                else:
                    new_end_tmp = [new_end]

                new_range = new_start_tmp + new_end_tmp
                logger.trace(new_range)
                new_start, new_end = min(new_range), max(new_range)

            logger.trace(f"{new_start=}, {new_end=}")

            logger.trace(string[new_start:new_end])

            string[new_start:new_end] = replace_with
            logger.trace(string)

            update_positions(start, end, len(replace_with), new_start, new_end)
            logger.trace(string_pos_matrix)

        return string, string_pos_matrix, utf_16_bang_list

    @trace
    def __str__(self):
        string = StringAsignmentMix(self.string)

        string_pos_matrix = [pos for pos in range(len(string))]
        updated_text, string_pos_matrix, utf_16_bang_list = self.pre_utf_16_bang(string, string_pos_matrix)

        if self.quote_html_type:
            self.quote_replaces = []
            html_quote_replaces = quote_html(str(updated_text), self.quote_html_type)
            for html_quote in html_quote_replaces:
                self.quote_replaces.append(html_quote)

        if not self.templates and not self.replaces and not self.quote_replaces:
            logger.trace("No templates, no replaces, no quote_replaces")
            return str(self.string)

        updated_text, string_pos_matrix, utf_16_bang_list = self._render_templates(updated_text, string_pos_matrix, utf_16_bang_list)
        updated_text, string_pos_matrix, utf_16_bang_list = self._render_replaces(updated_text, string_pos_matrix, utf_16_bang_list)
        updated_text, string_pos_matrix = self.post_utf_16_bang(updated_text, string_pos_matrix, utf_16_bang_list)
        return str(updated_text)

    def get_text(self):
        return self.__str__()


def split_overlapping_ranges(markups, _retry_count: int = 7):
    last_fixed_markup = markups
    for _ in range(len(markups) * _retry_count):
        markups = split_overlapping_range_position(markups)
        if last_fixed_markup and len(last_fixed_markup) == len(markups):
            break
        last_fixed_markup = markups
    return last_fixed_markup


def split_overlapping_range_position(positions):
    if not positions:
        return []

    positions.sort(key=lambda x: x["start"])
    logger.debug(f"Sorted positions: {positions}")

    result = [positions[0]]
    logger.debug(f"Initial result: {result}")

    for pos in positions[1:]:
        logger.debug(f"Processing position: {pos}")
        last = result[-1]

        if pos["start"] < last["end"]:
            logger.debug("Overlap detected")
            if pos["type"] != last["type"]:
                logger.debug("Different type")
                if pos["end"] <= last["end"]:
                    logger.debug("Case 1: Different type, ends before or at last")
                    result[-1] = {
                        "start": last["start"],
                        "end": pos["start"],
                        "type": last["type"],
                        "template": last["template"],
                    }
                    result.append(pos.copy())
                    if pos["end"] < last["end"]:
                        result.append(
                            {
                                "start": pos["end"],
                                "end": last["end"],
                                "type": last["type"],
                                "template": last["template"],
                            }
                        )
                else:
                    logger.debug("Case 2: Different type, ends after last")
                    result[-1] = {
                        "start": last["start"],
                        "end": pos["start"],
                        "type": last["type"],
                        "template": last["template"],
                    }
                    result.append(pos.copy())
            else:
                logger.debug("Case 3: Same type, update end")
                result[-1]["end"] = max(last["end"], pos["end"])
        else:
            logger.debug("Case 4: No overlap, add new position")
            result.append(pos.copy())

        logger.debug(f"Updated result: {result}")

    logger.debug(f"Final result: {result}")
    return result
def raw_render(**kwargs):
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = f"{{% raw %}}{value}{{% endraw %}}"
    return kwargs


def parse_markups(markups: list[str]):
    logger.trace(f"Given {markups=}")
    markups_out = []

    for markup in markups:
        logger.trace(f"Processing {markups=}")
        logger.trace(markup)
        if markup["type"] == "A":
            if markup["anchorType"] == "LINK":
                template = jinja_env.from_string('<a style="text-decoration: underline;" rel="{{rel}}" title="{{title}}" href="{{href}}" target="_blank">{{text}}</a>')
                template = template.render(raw_render(rel=markup.get("rel", ""), title=markup.get("title", ""), href=markup["href"]))
            elif markup["anchorType"] == "USER":
                template = jinja_env.from_string('<a style="text-decoration: underline;" href="https://medium.com/u/{{userId}}">{{text}}</a>')
                template = template.render(userId=markup["userId"])
            else:
                logger.error(f"Can't proccess 'anchorType': {markup['anchorType']}")
                continue
        elif markup["type"] == "STRONG":
            template = "<strong>{{text}}</strong>"
        elif markup["type"] == "EM":
            template = "<em>{{text}}</em>"
        elif markup["type"] == "CODE":
            template = "<code class='p-1.5 bg-gray-300 dark:bg-gray-600'>{{text}}</code>"
        else:
            logger.error(f"Unknown markup type: {markup}")
            continue

        template = jinja_env.from_string(template)

        markup["template"] = template
        markups_out.append(markup)

    return markups_out
