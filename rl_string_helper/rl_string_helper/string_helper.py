from loguru import logger
from .utils import quote_html, quote_symbol
from jinja2 import Environment, DebugUndefined, Template

from rl_string_helper.mixins.string_assignment import (
    StringAssignmentMixin_py as StringAssignmentMixin,
)

jinja_env = Environment(undefined=DebugUndefined)


"""
In JavaScript, the `length` property of a String object returns the number of code units (bytes) in the string, which makes use of UTF-16 encoding.
In UTF-16, each Unicode character may be encoded as one or two code units (byte). This means that for certain scripts, such as emojis, mathematical symbols, or some Chinese characters,
the value returned by length might not match the actual number of Unicode characters in the string.

Python uses UTF-8 encoding, which each character is encoded as one byte. So here is a workaround to get the actual number of characters and manipulate them in string as in UTF-16 encoding. See pre_utf_16_bang and post_utf_16_bang function. 
More info to read: https://habr.com/ru/articles/769256/
"""


class UTF16Handler:
    def __init__(self, default_bang_char: str = "R"):
        logger.info(
            f"Initializing UTF16Handler with default_bang_char: {default_bang_char}"
        )
        self._default_bang_char = default_bang_char

    def pre_utf_16_bang(
        self, string: str, string_pos_matrix: list
    ) -> tuple[str, list, list[tuple[int, int, int]]]:
        logger.info("Starting pre_utf_16_bang method")
        utf_16_bang_list: list[tuple[int, int, int]] = []
        string_len_utf_16 = len(string.encode("utf-16-le")) // 2
        logger.debug(f"UTF-16 length of string: {string_len_utf_16}")
        if string_len_utf_16 == len(string):
            logger.trace("String doesn't contain multibyte characters")
            return string, string_pos_matrix, utf_16_bang_list

        i = 0
        while len(string) - 1 > i:
            logger.debug(f"Processing character at index {i}")
            new_i = string_pos_matrix[i]
            char = string[new_i]
            char_len = len(char.encode("utf-16-le")) // 2
            if char_len == 2:
                logger.debug(f"Multibyte character found at index {i}")
                char_len_dif = char_len - 1
                char_present = self._default_bang_char * char_len_dif
                string, string_pos_matrix = self._paste_char(
                    string, string_pos_matrix, new_i + 1, char_present
                )
                logger.info(f"Mutation: Inserted '{char_present}' at index {new_i + 1}")
                i += 1
                utf_16_bang_list.append((i, char_len_dif, i))
            i += 1

        logger.info("Finished pre_utf_16_bang method")
        return string, string_pos_matrix, utf_16_bang_list

    def post_utf_16_bang(
        self,
        string: StringAssignmentMixin,
        string_pos_matrix: list,
        utf_16_bang_list: list,
    ):
        logger.info("Starting post_utf_16_bang method")
        string = StringAssignmentMixin(str(string))
        post_transbang = 0
        for bang_pos, char_len, old_pos in utf_16_bang_list:
            logger.debug(f"Processing bang at position {bang_pos}")
            string, string_pos_matrix = self._delete_char(
                string,
                string_pos_matrix,
                bang_pos - post_transbang,
                char_len,
                old_pos - post_transbang,
            )
            logger.info(
                f"Mutation: Deleted {char_len} character(s) at index {bang_pos - post_transbang}"
            )
            post_transbang += char_len
        logger.info("Finished post_utf_16_bang method")
        return string, string_pos_matrix

    def _paste_char(
        self,
        string: StringAssignmentMixin,
        string_pos_matrix: list,
        pos: int,
        char: str,
    ) -> tuple[StringAssignmentMixin, list]:
        logger.debug(f"Pasting character '{char}' at position {pos}")
        char_len = len(char)
        string_pos_matrix.insert(pos, string_pos_matrix[pos])
        for matrix_i in range(pos + 1, len(string_pos_matrix)):
            string_pos_matrix[matrix_i] += char_len
        string.insert(pos, char)
        logger.info(f"Mutation: Inserted '{char}' at position {pos}")
        return string, string_pos_matrix

    def _delete_char(
        self,
        string: StringAssignmentMixin,
        string_pos_matrix: list,
        pos: int,
        char_len: int,
        old_pos: int,
    ):
        logger.debug(f"Deleting character at position {pos}")
        deleted_char = string[pos : pos + char_len]
        string.pop(pos)
        string_pos_matrix.pop(old_pos)
        logger.info(f"Mutation: Deleted '{deleted_char}' at position {pos}")
        for matrix_i in range(pos, len(string_pos_matrix)):
            if isinstance(string_pos_matrix[matrix_i], int):
                string_pos_matrix[matrix_i] -= char_len
            elif isinstance(string_pos_matrix[matrix_i], tuple):
                string_pos_matrix[matrix_i] = (
                    string_pos_matrix[matrix_i][0] - char_len,
                    string_pos_matrix[matrix_i][1] - char_len,
                )
        return string, string_pos_matrix


class TemplateRenderer:
    def render_templates(
        self,
        string: str,
        string_pos_matrix: list,
        utf_16_bang_list: list,
        templates: list,
    ):
        logger.info("Starting render_templates method")
        if not templates:
            logger.info("No templates to render")
            return string, string_pos_matrix, utf_16_bang_list

        templates = reversed(templates)
        updated_text = string

        for (start, end), template in templates:
            logger.debug(f"Rendering template for range {start}:{end}")
            if start >= len(string_pos_matrix):
                logger.warning("Template start range out of bounds, skipping")
                continue
            if end - 1 >= len(string_pos_matrix):
                logger.warning(
                    "Template end range out of bounds, fixing end position..."
                )
                end = len(string_pos_matrix)
            if start == end:
                logger.warning("Empty template range, skipping")
                continue

            new_start, new_end = (
                string_pos_matrix[start],
                string_pos_matrix[end - 1] + 1,
            )
            if new_end < new_start:
                logger.warning("Invalid template range, skipping")
                continue

            context_text = template.render(text=updated_text[new_start:new_end])
            updated_text_template = jinja_env.from_string(
                "{{ updated_text[:new_start] }}{{ context_text }}{{updated_text[new_end:]}}"
            )
            old_text = updated_text[new_start:new_end]
            updated_text = updated_text_template.render(
                updated_text=updated_text,
                context_text=context_text,
                new_start=new_start,
                new_end=new_end,
            )
            logger.info(
                f"Mutation: Replaced '{old_text}' with '{context_text}' in range {new_start}:{new_end}"
            )

            prefix_len = self._get_prefix_len(template)
            suffix_len = self._get_suffix_len(template)
            self._update_nested_positions(
                string_pos_matrix, utf_16_bang_list, start, end, prefix_len, suffix_len
            )

        logger.info("Finished render_templates method")
        return updated_text, string_pos_matrix, utf_16_bang_list

    def _get_prefix_len(self, template_raw: Template, inner_char: str = "{"):
        logger.debug("Calculating prefix length")
        template = template_raw.render()
        return template.find(inner_char)

    def _get_suffix_len(self, template_raw: Template, outer_char: str = "}"):
        logger.debug("Calculating suffix length")
        template = template_raw.render()
        return len(template) - template.rfind(outer_char) - 1

    def _update_nested_positions(
        self, string_pos_matrix, utf_16_bang_list, start, end, prefix_len, suffix_len
    ):
        logger.debug(f"Updating nested positions for range {start}:{end}")
        for i in range(end, len(string_pos_matrix)):
            string_pos_matrix[i] += suffix_len + prefix_len
        for i in range(start, end):
            string_pos_matrix[i] += prefix_len
        for n in range(len(utf_16_bang_list)):
            utf_16_bang = utf_16_bang_list[n]
            if utf_16_bang[2] > end:
                utf_16_bang_list[n] = (
                    utf_16_bang[0] + prefix_len + suffix_len,
                    utf_16_bang[1],
                    utf_16_bang[2],
                )
            elif utf_16_bang[2] > start:
                utf_16_bang_list[n] = (
                    utf_16_bang[0] + prefix_len,
                    utf_16_bang[1],
                    utf_16_bang[2],
                )
        logger.info(f"Mutation: Updated positions for template in range {start}:{end}")


class StringReplacer:
    def render_replaces(
        self,
        string: StringAssignmentMixin,
        string_pos_matrix: list,
        utf_16_bang_list: list,
        replaces: list,
    ):
        logger.info("Starting render_replaces method")
        if not replaces:
            logger.info("No replacements to perform")
            return string, string_pos_matrix, utf_16_bang_list

        string = StringAssignmentMixin(str(string))

        for (start, end), replace_with in replaces:
            logger.debug(f"Performing replacement for range {start}:{end}")
            new_start, new_end = string_pos_matrix[start], string_pos_matrix[end - 1]
            if isinstance(new_end, int):
                new_end += 1

            if isinstance(new_start, tuple) or isinstance(new_end, tuple):
                new_start = (
                    min(new_start) if isinstance(new_start, tuple) else new_start
                )
                new_end = max(new_end) if isinstance(new_end, tuple) else new_end

            old_text = string[new_start:new_end]
            string[new_start:new_end] = replace_with
            logger.info(
                f"Mutation: Replaced '{old_text}' with '{replace_with}' in range {new_start}:{new_end}"
            )
            self._update_positions(
                string_pos_matrix,
                utf_16_bang_list,
                start,
                end,
                len(replace_with),
                new_start,
                new_end,
            )

        logger.info("Finished render_replaces method")
        return string, string_pos_matrix, utf_16_bang_list

    def _update_positions(
        self,
        string_pos_matrix,
        utf_16_bang_list,
        start,
        end,
        replace_len,
        new_start,
        new_end,
    ):
        logger.debug(f"Updating positions for replacement in range {start}:{end}")
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
                utf_16_bang_list[n] = (
                    utf_16_bang[0] + pos_len_diff,
                    utf_16_bang[1],
                    utf_16_bang[2],
                )
        logger.info(
            f"Mutation: Updated positions for replacement in range {start}:{end}"
        )


class RLStringHelper:
    def __init__(
        self,
        string: str,
        quote_html_type: list[str] = ["full"],
        _default_bang_char: str = "R",
    ):
        logger.info("Initializing RLStringHelper")
        self.string: str = quote_symbol(string)
        self.templates: list[tuple[tuple[int, int], Template]] = []
        self.quote_replaces: list[tuple[tuple[int, int], str]] = []
        self.replaces: list[tuple[tuple[int, int], str]] = []
        self.quote_html_type = quote_html_type
        self.utf16_handler = UTF16Handler(_default_bang_char)
        self.template_renderer = TemplateRenderer()
        self.string_replacer = StringReplacer()

    def set_template(self, start: int, end: int, template: str | Template):
        logger.info(f"Setting template for range {start}:{end}")
        if not isinstance(template, Template):
            template = jinja_env.from_string(template)
        self.templates.append(((start, end), template))
        logger.info(f"Mutation: Added template for range {start}:{end}")

    def set_replace(self, start: int, end: int, replace_with: str):
        logger.info(f"Setting replacement for range {start}:{end}")
        self.replaces.append(((start, end), replace_with))
        logger.info(
            f"Mutation: Added replacement '{replace_with}' for range {start}:{end}"
        )

    def __str__(self):
        logger.info("Converting RLStringHelper to string")
        string = StringAssignmentMixin(self.string)

        string_pos_matrix = list(range(len(string)))
        updated_text, string_pos_matrix, utf_16_bang_list = (
            self.utf16_handler.pre_utf_16_bang(string, string_pos_matrix)
        )

        if self.quote_html_type:
            logger.info("Applying HTML quoting")
            self.quote_replaces = list(
                quote_html(str(updated_text), self.quote_html_type)
            )
            logger.info(
                f"Mutation: Added {len(self.quote_replaces)} HTML quote replacements"
            )

        if not self.templates and not self.replaces and not self.quote_replaces:
            logger.info("No modifications needed, returning original string")
            return self.string

        updated_text, string_pos_matrix, utf_16_bang_list = (
            self.template_renderer.render_templates(
                updated_text, string_pos_matrix, utf_16_bang_list, self.templates
            )
        )
        updated_text, string_pos_matrix, utf_16_bang_list = (
            self.string_replacer.render_replaces(
                updated_text,
                string_pos_matrix,
                utf_16_bang_list,
                self.replaces + self.quote_replaces,
            )
        )
        updated_text, string_pos_matrix = self.utf16_handler.post_utf_16_bang(
            updated_text, string_pos_matrix, utf_16_bang_list
        )
        logger.info("Finished string conversion")
        return str(updated_text)

    def get_text(self):
        logger.info("Getting text from RLStringHelper")
        return self.__str__()


def split_overlapping_ranges(markups):
    logger.info("Starting split_overlapping_ranges")
    new_markups = process_and_optimize_intervals(
        *[
            Interval(markup["start"], markup["end"], markup["type"], markup["template"])
            for markup in markups
        ]
    )
    dict_new_markups = [markup.to_dict() for markup in new_markups]
    return dict_new_markups


class Interval:
    def __init__(self, start, end, type, template=None):
        self.start = start
        self.end = end
        self.type = type
        self.template = template

    def __repr__(self):
        return f"start={self.start}, end={self.end}, type={self.type}, template={self.template}"

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "type": self.type,
            "template": self.template,
        }


def split_intervals_with_types(*intervals):
    points = set()
    for interval in intervals:
        points.add(interval.start)
        points.add(interval.end)

    sorted_points = sorted(points)
    result = []

    for i in range(len(sorted_points) - 1):
        start = sorted_points[i]
        end = sorted_points[i + 1]
        types_and_templates = [
            (interval.type, interval.template)
            for interval in intervals
            if interval.start <= start and interval.end >= end
        ]
        result.append(
            Interval(
                start,
                end,
                [t[0] for t in types_and_templates],
                [t[1] for t in types_and_templates],
            )
        )

    return result


def convert_to_object_string(input_data):
    result = []

    for item in input_data:
        start, end = item.start, item.end
        for type_, template in zip(item.type, item.template):
            result.append(Interval(start, end, type_, template))

    return result


def process_and_optimize_intervals(*intervals):
    split = split_intervals_with_types(*intervals)
    return convert_to_object_string(split)


# intervals = [
#     Interval(4, 17, "bold", "<b>{{text}}</b>"),
#     Interval(10, 21, "italic", "<i>{{text}}</i>"),
#     Interval(18, 27, "underline", "<u>{{text}}</u>"),
#     Interval(33, 41, "code", "<code>{{text}}</code>"),
#     Interval(40, 46, "link", '<a href="#">{{text}}</a>'),
#     Interval(0, 46, "span", "<span>{{text}}</span>"),
# ]

# intervals_result =
# for interval in intervals_result:
#     print(interval)
