import sys
import re
from loguru import logger
from rl_string_helper import (
    RLStringHelper,
    UTF16Handler,
    StringAssignmentMixin,
    quote_html,
    split_overlapping_ranges,
)


class TestRLStringHelper:
    def setup_method(self):
        logger.remove()
        logger.add(sys.stdout, level="TRACE")

    def test_html_quote(self):
        quoted_string_1 = [i for i in quote_html("<Hello world>", "full")]
        assert quoted_string_1 == [((0, 1), "&lt;"), ((12, 13), "&gt;")]

        # Test with standard HTML characters
        html = '<div class="test">Hello & World</div>'
        result = list(quote_html(html, "full"))
        expected = [
            ((0, 1), "&lt;"),
            ((11, 12), "&quot;"),
            ((16, 17), "&quot;"),
            ((17, 18), "&gt;"),
            ((24, 25), "&amp;"),
            ((31, 32), "&lt;"),
            ((36, 37), "&gt;"),
        ]
        assert sorted(result) == sorted(expected)

        # Test with extra characters
        html = '<div class="test">\nHello & World</div>'
        result = list(quote_html(html, "extra"))
        expected = [
            ((0, 1), "&lt;"),
            ((11, 12), "&quot;"),
            ((16, 17), "&quot;"),
            ((17, 18), "&gt;"),
            ((25, 26), "&amp;"),
            ((32, 33), "&lt;"),
            ((37, 38), "&gt;"),
            ((18, 19), "<br />"),
        ]
        assert sorted(result) == sorted(expected)

        # Test with quote characters
        html = "<div class=\"test\">Hello & 'World'</div>"
        result = list(quote_html(html, "full"))
        expected = [
            ((0, 1), "&lt;"),
            ((11, 12), "&quot;"),
            ((16, 17), "&quot;"),
            ((17, 18), "&gt;"),
            ((24, 25), "&amp;"),
            ((26, 27), "&#39"),
            ((32, 33), "&#39"),
            ((33, 34), "&lt;"),
            ((38, 39), "&gt;"),
        ]
        assert sorted(result) == sorted(expected)

    def test_basic_template(self):
        helper = RLStringHelper("Hello world")
        helper.set_template(0, 5, "<a>{{text}}</a>")
        assert str(helper) == "<a>Hello</a> world"

        helper.set_template(6, 11, "<b>{{text}}</b>")
        assert str(helper) == "<a>Hello</a> <b>world</b>"

        helper.set_template(0, 11, "<i>{{text}}</i>")
        assert str(helper) == "<i><a>Hello</a> <b>world</b></i>"

    def test_super_duper_overlapsing(self):
        text = "Note: The patterns and ideas discussed in this post are broadly applicable."
        helper = RLStringHelper(text)

        markups = [
            {"start": 0, "end": 5, "type": "code", "template": "<code>{{text}}</code>"},
            {
                "start": 0,
                "end": 6,
                "type": "strong",
                "template": "<strong>{{text}}</strong>",
            },
            {"start": 0, "end": 6, "type": "em", "template": "<em>{{text}}</em>"},
        ]

        parsed_markups = split_overlapping_ranges(markups)
        for markup in parsed_markups:
            helper.set_template(markup["start"], markup["end"], markup["template"])

        expected_pattern = r"<em><strong><code>Note:</code></strong></em><em><strong> </strong></em>The patterns and ideas discussed in this post are broadly applicable\."
        result = str(helper)
        assert re.match(expected_pattern, result)

    def test_complex_overlapping_tags(self):
        text = "The quick (brown) fox jumps over 13 lazy dogs!"
        helper = RLStringHelper(text)

        markups = [
            {
                "start": 0,
                "end": 46,
                "type": "span",
                "template": "<span>{{text}}</span>",
            },
            {"start": 4, "end": 17, "type": "bold", "template": "<b>{{text}}</b>"},
            {"start": 10, "end": 21, "type": "italic", "template": "<i>{{text}}</i>"},
            {
                "start": 18,
                "end": 27,
                "type": "underline",
                "template": "<u>{{text}}</u>",
            },
            {
                "start": 33,
                "end": 41,
                "type": "code",
                "template": "<code>{{text}}</code>",
            },
            {
                "start": 40,
                "end": 46,
                "type": "link",
                "template": '<a href="#">{{text}}</a>',
            },
        ]

        parsed_markups = split_overlapping_ranges(markups)
        for markup in parsed_markups:
            helper.set_template(markup["start"], markup["end"], markup["template"])

        expected_output = """<span>The </span><b><span>quick </span></b><i><b><span>(brown)</span></b></i><i><span> </span></i><u><i><span>fox</span></i></u><u><span> jumps</span></u><span> over </span><code><span>13 lazy</span></code><a href="#"><code><span> </span></code></a><a href="#"><span>dogs!</span></a>"""

        assert str(helper) == expected_output

    def test_nmultibyte_emoji(self):
        text = "Noah dragged his two printers out from Settings ⚙️  < Printers & Scanners 🖨️  and dropped them in Dock or Desktop, I don’t remember — but you can drag to both the places."
        string_helper = StringAssignmentMixin(text)
        utf_handler = UTF16Handler()
        string_pos_matrix = list(range(len(text)))
        updated_text, string_pos_matrix, utf_16_bang_list = utf_handler.pre_utf_16_bang(
            string_helper, string_pos_matrix
        )
        updated_text, string_pos_matrix = utf_handler.post_utf_16_bang(
            updated_text, string_pos_matrix, utf_16_bang_list
        )
        assert str(updated_text) == text
        from icecream import ic

        string_helper = RLStringHelper(text, None)
        string_helper.set_template(0, 100000, "<span>{{text}}</span>")
        assert str(string_helper) == f"<span>{text}</span>".replace("’", "'")

        string_helper = RLStringHelper(text, ["None"])
        string_helper.set_template(39, 76, "<code class='test'>{{text}}</code>")
        with open("test.txt", "w") as f:
            f.write(str(string_helper) + "\n")
        assert str(
            string_helper
        ) == f"{text[:39]}<code class='test'>Settings ⚙️  < Printers & Scanners 🖨</code>️{text[76:]}".replace(
            "’", "'"
        )

    def test_basic_replace(self):
        # Replace A to B - ONE to ONE char
        helper = RLStringHelper("ABC")
        helper.set_replace(0, 1, "B")
        assert str(helper) == "BBC"

        # Replace first B to AA - ONE to TWO chars
        helper.set_replace(0, 1, "AA")
        assert str(helper) == "AABC"

        # Replace C to D - ONE to ONE char
        helper.set_replace(2, 3, "D")
        assert str(helper) == "AABD"

        # Replace BD to R - TWO to ONE char
        helper.set_replace(1, 3, "R")
        assert str(helper) == "AAR"

        # Replace AA to CD
        helper.set_replace(0, 2, "CD")
        assert str(helper) == "CD"

    def test_multibyte_replace(self):
        helper = RLStringHelper("TESERT - 📊 - ABC")
        helper.set_replace(0, 6, "B")
        assert helper.get_text() == "B - 📊 - ABC"

        helper = RLStringHelper(
            "Your support means the world to me. If you found this article valuable and insightful, please consider giving it a round of applause by clicking the clapping hands icon 👏."
        )
        helper.set_template(0, 200, "<kr>{{text}}</kr>")
        helper.set_template(0, 200, "<kz>{{text}}</kz>")
        assert (
            helper.get_text()
            == "<kz><kr>Your support means the world to me. If you found this article valuable and insightful, please consider giving it a round of applause by clicking the clapping hands icon 👏.</kr></kz>"
        )

        helper = RLStringHelper("TESERT ALMACOM - 📊 - ABC")
        helper.set_replace(0, 14, "B")
        assert helper.get_text() == "B - 📊 - ABC"

        helper = RLStringHelper("hello - 📊 - ABC")
        helper.set_template(0, 5, "<a>{{text}}</a>")
        assert helper.get_text() == "<a>hello</a> - 📊 - ABC"

        helper = RLStringHelper("ABC 📊 - How are you?")
        helper.set_template(4, 6, "<a>{{text}}</a>")
        assert str(helper) == "ABC <a>📊</a> - How are you?"

        helper = RLStringHelper("We have a 📊, a 📊 and a 📊.")
        helper.set_template(0, 30, "<e>{{text}}</e>")
        assert helper.get_text() == "<e>We have a 📊, a 📊 and a 📊.</e>"

    def test_romano(self):
        issue_text = "Whilst academic research papers have highlighted performance issues with the prophet since 2017, the propagation of package popularity through the data science community has been fueled by 𝙗𝙤𝙩𝙝 𝙚𝙭𝙘𝙚𝙨𝙨𝙞𝙫𝙚 𝙘𝙡𝙖𝙞𝙢𝙨 𝙛𝙧𝙤𝙢 𝙩𝙝𝙚 𝙤𝙧𝙞𝙜𝙞𝙣𝙖𝙡 𝙙𝙚𝙫𝙚𝙡𝙤𝙥𝙢𝙚𝙣𝙩 𝙩𝙚𝙖𝙢 𝙗𝙪𝙩 𝙢𝙤𝙧𝙚 𝙞𝙢𝙥𝙤𝙧𝙩𝙖𝙣𝙩𝙡𝙮 𝙗𝙮 𝙢𝙖𝙧𝙠𝙚𝙩𝙞𝙣𝙜 𝙤𝙛 𝙩𝙝𝙚 𝙣𝙤𝙣-𝙥𝙚𝙧𝙛𝙤𝙧𝙢𝙞𝙣𝙜 𝙥𝙖𝙘𝙠𝙖𝙜𝙚 𝙫𝙞𝙖 𝙖𝙧𝙩𝙞𝙘𝙡𝙚𝙨 𝙤𝙣 𝙈𝙚𝙙𝙞𝙪𝙢 𝙖𝙣𝙙 𝙨𝙤𝙘𝙞𝙖𝙡 𝙢𝙚𝙙𝙞𝙖."
        helper = RLStringHelper(issue_text)
        assert helper.get_text() == issue_text

    def test_markup_parser(self):
        href_markup = {
            "start": 0,
            "end": 12,
            "type": "a",
            "template": '<a href="https://readwise.io/bookreview/{{ book_id }}">{{ text }}</a>',
        }

        helper = RLStringHelper("Hello world")
        parsed_markups = split_overlapping_ranges([href_markup])
        for markup in parsed_markups:
            helper.set_template(markup["start"], markup["end"], markup["template"])

        assert (
            helper.get_text()
            == '<a href="https://readwise.io/bookreview/{{ book_id }}">Hello world</a>'
        )

    def test_medium_all(self):
        helper = RLStringHelper("ABC Hello world")
        helper.set_replace(0, 1, "B")
        assert str(helper) == "BBC Hello world"

        helper.set_template(4, 9, "<a>{{text}}</a>")
        assert str(helper) == "BBC <a>Hello</a> world"

        helper.set_template(10, 15, "<b>{{text}}</b>")
        assert str(helper) == "BBC <a>Hello</a> <b>world</b>"
