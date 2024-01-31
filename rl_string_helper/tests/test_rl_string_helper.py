import sys

from loguru import logger
from rl_string_helper import RLStringHelper, quote_html, parse_markups


class TestRLStringHelper:
    def setup_method(self):
        logger.remove()
        logger.add(sys.stdout, level="TRACE")

    def test_html_quote(self):
        quoted_string_1 = [i for i in quote_html("<Hello world>")]
        assert quoted_string_1 == [((0, 1), '&lt;'), ((12, 13), '&gt;')]

        # Test with standard HTML characters
        html = '<div class="test">Hello & World</div>'
        result = list(quote_html(html))
        expected = [((0, 1), '&lt;'), ((11, 12), '&quot;'), ((16, 17), '&quot;'), ((17, 18), '&gt;'), ((24, 25), '&amp;'), ((31, 32), '&lt;'), ((36, 37), '&gt;')]
        assert result == expected

        # Test with extra characters
        html = '<div class="test">\nHello & World</div>'
        result = list(quote_html(html, True))
        expected = [((0, 1), '&lt;'), ((11, 12), '&quot;'), ((16, 17), '&quot;'), ((17, 18), '&gt;'), ((25, 26), '&amp;'), ((32, 33), '&lt;'), ((37, 38), '&gt;'), ((18, 19), '<br />')]
        assert result == expected

        # Test with quote characters
        html = '<div class="test">Hello & \'World\'</div>'
        result = list(quote_html(html))
        expected = [((0, 1), '&lt;'), ((11, 12), '&quot;'), ((16, 17), '&quot;'), ((17, 18), '&gt;'), ((24, 25), '&amp;'), ((26, 27), '&#39'), ((32, 33), '&#39'), ((33, 34), '&lt;'), ((38, 39), '&gt;')]
        assert result == expected

    def test_basic_template(self):
        helper = RLStringHelper("Hello world")
        helper.set_template(0, 5, "<a>{{text}}</a>")
        assert str(helper) == "<a>Hello</a> world"

        helper.set_template(6, 11, "<b>{{text}}</b>")
        assert str(helper) == "<a>Hello</a> <b>world</b>"

        helper.set_template(0, 11, "<i>{{text}}</i>")
        assert str(helper) == "<i><a>Hello</a> <b>world</b></i>"

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

        helper = RLStringHelper("Your support means the world to me. If you found this article valuable and insightful, please consider giving it a round of applause by clicking the clapping hands icon 👏.")
        helper.set_template(0, 200, "<kr>{{text}}</kr>")
        helper.set_template(0, 200, "<kz>{{text}}</kz>")
        assert helper.get_text() == "<kz><kr>Your support means the world to me. If you found this article valuable and insightful, please consider giving it a round of applause by clicking the clapping hands icon 👏.</kr></kz>"

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
            "__typename": 'Markup',
            "anchorType": 'LINK',
            "end": 12,
            "href": 'https://readwise.io/bookreview/{{book_id',
            "name": None,
            "rel": 'nofollow',
            "start": 0,
            "title": '',
            "type": 'A',
            "userId": None
        }

        helper = RLStringHelper("Hello world")
        markups = parse_markups([href_markup])
        for markup in markups:
            helper.set_template(markup["start"], markup["end"], markup["template"])
        assert helper.get_text() == '<a style="text-decoration: underline;" rel="nofollow" title="" href="https://readwise.io/bookreview/{{book_id" target="_blank">Hello world</a>'

    def test_medium_all(self):
        helper = RLStringHelper("ABC Hello world")
        helper.set_replace(0, 1, "B")
        assert str(helper) == "BBC Hello world"

        helper.set_template(4, 9, "<a>{{text}}</a>")
        assert str(helper) == "BBC <a>Hello</a> world"

        helper.set_template(10, 15, "<b>{{text}}</b>")
        assert str(helper) == "BBC <a>Hello</a> <b>world</b>"
