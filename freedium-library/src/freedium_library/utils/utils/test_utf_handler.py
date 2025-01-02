from loguru import logger

from freedium_library.utils.utils.utf_handler import UTFEncoding, UTFHandler

logger.add("test.log", level="TRACE")


def test_multibyte_emoji():
    # Test string with emoji characters
    text = "Noah dragged his two printers out from Settings ⚙️  < Printers & Scanners 🖨️  and dropped them in Dock or Desktop, I don’t remember — but you can drag to both the places.'"

    # Initialize handler with UTF-16 encoding
    handler = UTFHandler(text, UTFEncoding.UTF16)

    assert str(handler) == text

    # Test position mappings around emojis
    assert handler.get_encoded_position(39) == 39  # Before "Settings ⚙️"
    assert handler.get_encoded_position(76) == 77  # After "Scanners 🖨️"

    # Test string slicing around emoji
    emoji_section = handler[39:76]
    assert emoji_section == "Settings ⚙️  < Printers & Scanners 🖨️"

    # Test insertion before emoji
    handler.insert(39, "<code class='test'>")
    handler.insert(77, "</code>")

    expected = text[:39] + "<code class='test'>" + text[39:76] + "</code>" + text[76:]
    # expected = expected.replace("🖨️", "🖨")

    assert bytes(str(handler), "utf-8") == bytes(expected, "utf-8")
    assert str(handler) == expected


def test_mathematical_monospace_x():
    text = "Whilst academic research papers have highlighted performance issues with the prophet since 2017, the propagation of package popularity through the data science community has been fueled by 𝙗𝙤𝙩𝙝 𝙚𝙭𝙘𝙚𝙨𝙨𝙞𝙫𝙚 𝙘𝙡𝙖𝙞𝙢𝙨 𝙛𝙧𝙤𝙢 𝙩𝙝𝙚 𝙤𝙧𝙞𝙜𝙞𝙣𝙖𝙡 𝙙𝙚𝙫𝙚𝙡𝙤𝙥𝙢𝙚𝙣𝙩 𝙩𝙚𝙖𝙢 𝙗𝙪𝙩 𝙢𝙤𝙧𝙚 𝙞𝙢𝙥𝙤𝙧𝙩𝙖𝙣𝙩𝙡𝙮 𝙗𝙮 𝙢𝙖𝙧𝙠𝙚𝙩𝙞𝙣𝙜 𝙤𝙛 𝙩𝙝𝙚 𝙣𝙤𝙣-𝙥𝙚𝙧𝙛𝙤𝙧𝙢𝙞𝙣𝙜 𝙥𝙖𝙘𝙠𝙖𝙜𝙚 𝙫𝙞𝙖 𝙖𝙧𝙩𝙞𝙘𝙡𝙚𝙨 𝙤𝙣 𝙈𝙚𝙙𝙞𝙪𝙢 𝙖𝙣𝙙 𝙨𝙤𝙘𝙞𝙖𝙡 𝙢𝙚𝙙𝙞𝙖."

    handler = UTFHandler(text, UTFEncoding.UTF16)

    assert str(handler) == text

    start_pos = text.index("𝙗")

    assert handler.get_encoded_position(start_pos) == start_pos

    o_multibyte = text.index("𝙤")
    assert handler.get_encoded_position(o_multibyte) > o_multibyte

    handler.insert(189, "<math>")
    handler.insert(197, "</math>")

    expected = text[:189] + "<math>" + text[189:193] + "</math>" + text[193:]
    assert str(handler) == expected


def test_mathematical_monospace():
    text = "by 𝙗𝙤𝙩𝙝 𝙚𝙭"

    handler = UTFHandler(text, UTFEncoding.UTF16)

    assert str(handler) == text

    # Test encoded positions for mathematical monospace characters
    assert handler.get_encoded_position(3) == 3  # Position before '𝙗'
    assert handler.get_encoded_position(5) == 7  # Position after '𝙗'
    assert handler.get_encoded_position(7) == 11  # Position after '𝙤'
    # assert handler.get_encoded_position(9) == 15  # Position after '𝙩'

    handler.insert(3, "<math>")
    handler.insert(11, "</math>")

    expected = text[:3] + "<math>" + text[3:7] + "</math>" + text[7:]
    assert str(handler) == expected


def test_utf8_handling():
    # Test with UTF-8 encoded text containing special characters
    text = "Hello 世界! 🌍"
    handler = UTFHandler(text, UTFEncoding.UTF8)

    assert str(handler) == text

    # Test position mapping with UTF-8 characters
    assert handler.get_encoded_position(6) == 6  # Position before '世'
    assert handler.get_encoded_position(8) == 12  # Position after '界'

    # Test insertion around UTF-8 characters
    handler.insert(6, "<zh>")
    handler.insert(17, "</zh>")

    expected = "Hello <zh>世界</zh>! 🌍"
    assert str(handler) == expected


def test_utf32_handling():
    # Test with UTF-32 encoded text
    text = "Testing 🚀 UTF-32 🎯"
    handler = UTFHandler(text, UTFEncoding.UTF32)

    assert str(handler) == text

    # Test position mapping with UTF-32 characters
    assert handler.get_encoded_position(8) == 8  # Position before rocket
    assert handler.get_encoded_position(18) == 18  # Position before target

    # Test deletion around UTF-32 characters
    handler.delete(7, 2)  # Delete " 🚀 "
    assert str(handler) == "Testing UTF-32 🎯"


def test_edge_cases():
    # Test empty string
    handler = UTFHandler("", UTFEncoding.UTF16)
    assert str(handler) == ""

    # Test string with only special characters
    handler = UTFHandler("🌟✨💫", UTFEncoding.UTF16)
    assert str(handler) == "🌟✨💫"

    # Test consecutive insertions
    handler.insert(0, "<")
    handler.insert(10, ">")
    assert str(handler) == "<🌟✨💫>"

    # Test deletion at boundaries
    handler.delete(1, 1)  # Delete first emoji
    assert str(handler) == "<✨💫>"


def test_position_tracking():
    text = "Mix of ASCII and 漢字 with 🎮"
    handler = UTFHandler(text, UTFEncoding.UTF16)

    # Test position tracking before and after modifications
    original_pos = handler.get_encoded_position(13)  # Position before 漢
    handler.insert(13, "[")
    handler.insert(17, "]")

    # Verify position tracking is maintained
    new_pos = handler.get_encoded_position(14)  # Should account for inserted '['
    assert new_pos == original_pos + 1

    expected = "Mix of ASCII [and] 漢字 with 🎮"
    assert str(handler) == expected
