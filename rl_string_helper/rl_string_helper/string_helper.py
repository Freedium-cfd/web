from loguru import logger
from .logger_trace import trace
from .utils import quote_html, quote_symbol
from jinja2 import Environment, DebugUndefined, Template

from rl_string_helper.mixins.string_assignment import StringAssignmentMixin_py as StringAssignmentMixin

jinja_env = Environment(undefined=DebugUndefined)


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
    __slots__ = ("string", "templates", "replaces", "quote_html_type", "quote_replaces", "_default_bang_char")

    def __init__(self, string: str, quote_html_type: list[str] = ["full"], _default_bang_char: str = "R"):
        self.string: str = quote_symbol(string)
        self.templates = []
        self.quote_replaces = []
        self.replaces = []
        self.quote_html_type = quote_html_type
        self._default_bang_char = _default_bang_char

    @trace
    def pre_utf_16_bang(self, string: str, string_pos_matrix: list):
        utf_16_bang_list = []
        string_len_utf_16 = len(string.encode("utf-16-le")) // 2
        if string_len_utf_16 == len(string):
            logger.trace("String doesn't contain multibyte characters")
            return string, string_pos_matrix, utf_16_bang_list

        i = 0
        while len(string) - 1 > i:
            new_i = string_pos_matrix[i]
            char = string[new_i]
            char_len = len(char.encode("utf-16-le")) // 2
            if char_len == 2:
                char_len_dif = char_len - 1
                char_present = self._default_bang_char * char_len_dif
                string, string_pos_matrix = self._paste_char(string, string_pos_matrix, new_i + 1, char_present)
                i += 1
                utf_16_bang_list.append((i, char_len_dif, i))
            i += 1

        return string, string_pos_matrix, utf_16_bang_list

    def _paste_char(self, string: str, string_pos_matrix: list, pos: int, char: str):
        char_len = len(char)
        string_pos_matrix.insert(pos, string_pos_matrix[pos])
        for matrix_i in range(pos + 1, len(string_pos_matrix)):
            string_pos_matrix[matrix_i] += char_len
        string.insert(pos, char)
        return string, string_pos_matrix

    def _delete_char(self, string: str, string_pos_matrix: list, pos: int, char_len: int, old_pos: int):
        string.pop(pos)
        string_pos_matrix.pop(old_pos)
        for matrix_i in range(pos, len(string_pos_matrix)):
            if isinstance(string_pos_matrix[matrix_i], int):
                string_pos_matrix[matrix_i] -= char_len
            elif isinstance(string_pos_matrix[matrix_i], tuple):
                string_pos_matrix[matrix_i] = (string_pos_matrix[matrix_i][0] - char_len, string_pos_matrix[matrix_i][1] - char_len)
        return string, string_pos_matrix

    @trace
    def post_utf_16_bang(self, string: StringAssignmentMixin, string_pos_matrix: list, utf_16_bang_list: list):
        string = StringAssignmentMixin(str(string))
        post_transbang = 0
        for bang_pos, char_len, old_pos in utf_16_bang_list:
            string, string_pos_matrix = self._delete_char(string, string_pos_matrix, bang_pos - post_transbang, char_len, old_pos - post_transbang)
            post_transbang += char_len
        return string, string_pos_matrix

    @trace
    def set_template(self, start: int, end: int, template: str):
        if not isinstance(template, Template):
            template = jinja_env.from_string(template)
        self.templates.append(((start, end), template))

    @trace
    def set_replace(self, start: int, end: int, replace_with: str):
        self.replaces.append(((start, end), replace_with))

    @trace
    def _render_templates(self, string: str, string_pos_matrix: list, utf_16_bang_list: list):
        if not self.templates:
            return string, string_pos_matrix, utf_16_bang_list

        templates = reversed(self.templates)
        updated_text = string

        @trace
        def _get_prefix_len(template_raw: Template, inner_char: str = "{"):
            template = template_raw.render()
            return template.find(inner_char)

        @trace
        def _get_suffix_len(template_raw: Template, outer_char: str = "}"):
            template = template_raw.render()
            return len(template) - template.rfind(outer_char) - 1

        @trace
        def update_nested_positions(start, end, prefix_len, suffix_len):
            for i in range(end, len(string_pos_matrix)):
                string_pos_matrix[i] += suffix_len + prefix_len
            for i in range(start, end):
                string_pos_matrix[i] += prefix_len
            for n in range(len(utf_16_bang_list)):
                utf_16_bang = utf_16_bang_list[n]
                if utf_16_bang[2] > end:
                    utf_16_bang_list[n] = (utf_16_bang[0] + prefix_len + suffix_len, utf_16_bang[1], utf_16_bang[2])
                elif utf_16_bang[2] > start:
                    utf_16_bang_list[n] = (utf_16_bang[0] + prefix_len, utf_16_bang[1], utf_16_bang[2])

        for (start, end), template in templates:
            if start >= len(string_pos_matrix) or end - 1 >= len(string_pos_matrix):
                continue
            if start == end:
                continue

            new_start, new_end = string_pos_matrix[start], string_pos_matrix[end - 1] + 1
            if new_end < new_start:
                continue

            context_text = template.render(text=updated_text[new_start:new_end])
            updated_text_template = jinja_env.from_string("{{ updated_text[:new_start] }}{{ context_text }}{{updated_text[new_end:]}}")
            updated_text = updated_text_template.render(updated_text=updated_text, context_text=context_text, new_start=new_start, new_end=new_end)

            prefix_len = _get_prefix_len(template)
            suffix_len = _get_suffix_len(template)
            update_nested_positions(start, end, prefix_len, suffix_len)

        return updated_text, string_pos_matrix, utf_16_bang_list

    @trace
    def _render_replaces(self, string: StringAssignmentMixin, string_pos_matrix: list, utf_16_bang_list: list):
        if not self.replaces and not self.quote_replaces:
            return string, string_pos_matrix, utf_16_bang_list

        string = StringAssignmentMixin(str(string))
        replaces = self.replaces + self.quote_replaces

        @trace
        def update_positions(start: int, end: int, replace_len: int, new_start: int, new_end: int):
            pos_len_diff = replace_len - (end - start)
            for pos_index in range(end, len(string_pos_matrix)):
                if isinstance(string_pos_matrix[pos_index], int):
                    string_pos_matrix[pos_index] += pos_len_diff
                elif isinstance(string_pos_matrix[pos_index], tuple):
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

        for (start, end), replace_with in replaces:
            new_start, new_end = string_pos_matrix[start], string_pos_matrix[end - 1]
            if isinstance(new_end, int):
                new_end += 1

            if isinstance(new_start, tuple) or isinstance(new_end, tuple):
                new_start = min(new_start) if isinstance(new_start, tuple) else new_start
                new_end = max(new_end) if isinstance(new_end, tuple) else new_end

            string[new_start:new_end] = replace_with
            update_positions(start, end, len(replace_with), new_start, new_end)

        return string, string_pos_matrix, utf_16_bang_list

    @trace
    def __str__(self):
        string = StringAssignmentMixin(self.string)

        string_pos_matrix = list(range(len(string)))
        updated_text, string_pos_matrix, utf_16_bang_list = self.pre_utf_16_bang(string, string_pos_matrix)

        if self.quote_html_type:
            self.quote_replaces = list(quote_html(str(updated_text), self.quote_html_type))

        if not self.templates and not self.replaces and not self.quote_replaces:
            return self.string

        updated_text, string_pos_matrix, utf_16_bang_list = self._render_templates(updated_text, string_pos_matrix, utf_16_bang_list)
        updated_text, string_pos_matrix, utf_16_bang_list = self._render_replaces(updated_text, string_pos_matrix, utf_16_bang_list)
        updated_text, string_pos_matrix = self.post_utf_16_bang(updated_text, string_pos_matrix, utf_16_bang_list)
        return str(updated_text)

    def get_text(self):
        return self.__str__()


def split_overlapping_ranges(markups, _retry_count: int = 7):
    for _ in range(len(markups) * _retry_count):
        new_markups = split_overlapping_range_position(markups)
        if len(new_markups) == len(markups):
            break
        markups = new_markups
    return markups


def split_overlapping_range_position(positions):
    if not positions:
        return []

    positions.sort(key=lambda x: x["start"])
    result = [positions[0]]

    for pos in positions[1:]:
        last = result[-1]
        if not pos["start"] < last["end"]:
            result.append(pos.copy())
            continue

        if pos["type"] != last["type"]:
            if pos["end"] <= last["end"]:
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
                result[-1] = {
                    "start": last["start"],
                    "end": pos["start"],
                    "type": last["type"],
                    "template": last["template"],
                }
                result.append(pos.copy())
        else:
            result[-1]["end"] = max(last["end"], pos["end"])

    return result


def raw_render(**kwargs):
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = f"{{% raw %}}{value}{{% endraw %}}"
    return kwargs


def parse_markups(markups: list[str]):
    markups_out = []

    for markup in markups:
        if markup["type"] == "A":
            if markup["anchorType"] == "LINK":
                template = jinja_env.from_string('<a style="text-decoration: underline;" rel="{{rel}}" title="{{title}}" href="{{href}}" target="_blank">{{text}}</a>')
                template = template.render(raw_render(rel=markup.get("rel", ""), title=markup.get("title", ""), href=markup["href"]))
            elif markup["anchorType"] == "USER":
                template = jinja_env.from_string('<a style="text-decoration: underline;" href="https://medium.com/u/{{userId}}">{{text}}</a>')
                template = template.render(userId=markup["userId"])
            else:
                continue
        elif markup["type"] == "STRONG":
            template = "<strong>{{text}}</strong>"
        elif markup["type"] == "EM":
            template = "<em>{{text}}</em>"
        elif markup["type"] == "CODE":
            template = "<code class='p-1.5 bg-gray-300 dark:bg-gray-600'>{{text}}</code>"
        else:
            continue

        template = jinja_env.from_string(template)
        markup["template"] = template
        markups_out.append(markup)

    return markups_out
