from loguru import logger
from freedium_library.utils.utils.utf_handler import (
    UTFEncoding,
    UTFHandler,
    CharacterMapping,
    PositionTracker,
)

logger.add("test.log", level="TRACE")


def test_multibyte_emoji():
    text = "Noah dragged his two printers out from Settings ⚙️  < Printers & Scanners 🖨️  and dropped them in Dock or Desktop, I don't remember — but you can drag to both the places.'"

    handler = UTFHandler(text, UTFEncoding.UTF16)

    assert str(handler) == text

    assert handler.get_encoded_position(39) == 39  # Before "Settings ⚙️"
    assert handler.get_encoded_position(76) == 77  # After "Scanners 🖨️"

    emoji_section = handler[39:76]
    assert emoji_section == "Settings ⚙️  < Printers & Scanners 🖨️"

    handler.insert(39, "<code class='test'>")
    handler.insert(77, "</code>")

    expected = text[:39] + "<code class='test'>" + text[39:76] + "</code>" + text[76:]

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

    assert handler.get_encoded_position(3) == 3  # Position before '𝙗'
    assert handler.get_encoded_position(5) == 7  # Position after '𝙗'
    assert handler.get_encoded_position(7) == 11  # Position after '𝙤'

    handler.insert(3, "<math>")
    handler.insert(11, "</math>")

    expected = text[:3] + "<math>" + text[3:7] + "</math>" + text[7:]
    assert str(handler) == expected


def test_utf8_handling():
    text = "Hello 世界! 🌍"
    handler = UTFHandler(text, UTFEncoding.UTF8)

    assert str(handler) == text

    assert handler.get_encoded_position(6) == 6  # Position before '世'
    assert handler.get_encoded_position(8) == 12  # Position after '界'

    handler.insert(6, "<zh>")
    handler.insert(17, "</zh>")

    expected = "Hello <zh>世界</zh>! 🌍"
    assert str(handler) == expected


def test_utf32_handling():
    text = "Testing 🚀 UTF-32 🎯"
    handler = UTFHandler(text, UTFEncoding.UTF32)

    assert str(handler) == text

    assert handler.get_encoded_position(8) == 8  # Position before rocket
    assert handler.get_encoded_position(18) == 18  # Position before target

    handler.delete(7, 2)  # Delete " 🚀 "
    assert str(handler) == "Testing UTF-32 🎯"


def test_edge_cases():
    handler = UTFHandler("", UTFEncoding.UTF16)
    assert str(handler) == ""

    handler = UTFHandler("🌟✨💫", UTFEncoding.UTF16)
    assert str(handler) == "🌟✨💫"

    handler.insert(0, "<")
    handler.insert(10, ">")
    assert str(handler) == "<🌟✨💫>"

    handler.delete(1, 1)  # Delete first emoji
    assert str(handler) == "<✨💫>"


def test_position_tracking():
    text = "Mix of ASCII and 漢字 with 🎮"
    handler = UTFHandler(text, UTFEncoding.UTF16)

    original_pos = handler.get_encoded_position(13)  # Position before 漢
    handler.insert(13, "[")
    handler.insert(17, "]")

    new_pos = handler.get_encoded_position(14)  # Should account for inserted '['
    assert new_pos == original_pos + 1

    expected = "Mix of ASCII [and] 漢字 with 🎮"
    assert str(handler) == expected


def test_insert_and_getitem():
    original = "Hello World"
    handler = UTFHandler(original, UTFEncoding.UTF8)
    handler.insert(5, " Amazing")
    expected = "Hello Amazing World"
    assert str(handler) == expected
    assert handler[0] == expected[0]
    assert handler[-1] == expected[-1]


def test_delete_and_get_slice():
    original = "Hello Amazing World"
    handler = UTFHandler(original, UTFEncoding.UTF8)
    handler.delete(5, 8)
    expected = "Hello World"
    assert str(handler) == expected
    assert handler.get_string_slice(0, 5) == "Hello"
    assert handler[6:] == "World"


def test_repr_returns_repr():
    text = "Test string"
    handler = UTFHandler(text, UTFEncoding.UTF8)
    rep = repr(handler)
    assert text in rep


def test_character_mapping_negative():
    try:
        CharacterMapping(
            char="a",
            original_pos=-1,
            original_encoded_pos=0,
            current_pos=0,
            encoded_pos=0,
            original_char_length=1,
            char_length=1,
        )
        assert False, "ValueError not raised for negative original_pos"
    except ValueError:
        pass
    try:
        CharacterMapping(
            char="a",
            original_pos=0,
            original_encoded_pos=0,
            current_pos=-1,
            encoded_pos=0,
            original_char_length=1,
            char_length=1,
        )
        assert False, "ValueError not raised for negative current_pos"
    except ValueError:
        pass


def test_character_mapping_char_length():
    try:
        CharacterMapping(
            char="a",
            original_pos=0,
            original_encoded_pos=0,
            current_pos=0,
            encoded_pos=0,
            original_char_length=1,
            char_length=0,
        )
        assert False, "ValueError not raised for char_length less than 1"
    except ValueError:
        pass


def test_shift_positions():
    cm = CharacterMapping(
        char="a",
        original_pos=0,
        original_encoded_pos=0,
        current_pos=5,
        encoded_pos=10,
        original_char_length=1,
        char_length=1,
    )
    cm.shift_positions(2, 3)
    assert cm.current_pos == 7
    assert cm.encoded_pos == 13


def test_position_tracker():
    tracker = PositionTracker()
    cm1 = CharacterMapping(
        char="a",
        original_pos=1,
        original_encoded_pos=1,
        current_pos=1,
        encoded_pos=1,
        original_char_length=1,
        char_length=1,
    )
    cm2 = CharacterMapping(
        char="b",
        original_pos=5,
        original_encoded_pos=5,
        current_pos=5,
        encoded_pos=5,
        original_char_length=1,
        char_length=1,
    )
    tracker.add(cm1)
    tracker.add(cm2)
    mappings = tracker.get()
    assert len(mappings) == 2

    cleared = tracker.clear(0, 3)
    assert cleared == 1
    mappings = tracker.get()
    assert len(mappings) == 1
    assert mappings[0].char == "b"

    cm3 = CharacterMapping(
        char="c",
        original_pos=10,
        original_encoded_pos=10,
        current_pos=10,
        encoded_pos=10,
        original_char_length=1,
        char_length=1,
    )
    tracker.add(cm3)
    tracker.update(3, 2, 3)
    mappings = tracker.get()
    for mapping in mappings:
        if mapping.char == "b":
            assert mapping.original_pos == 3
            assert mapping.encoded_pos == 2
        if mapping.char == "c":
            assert mapping.original_pos == 8
            assert mapping.encoded_pos == 7


def test_utf_encoding_properties():
    assert hasattr(UTFEncoding, "UTF8")
    assert hasattr(UTFEncoding, "UTF16")
    assert hasattr(UTFEncoding, "UTF32")
    assert hasattr(UTFEncoding, "UTF32")


def test_position_tracker_update_edge_cases():
    """Test PositionTracker.update() with various modification scenarios"""
    tracker = PositionTracker()
    mappings = [
        CharacterMapping(
            char="a",
            original_pos=5,
            original_encoded_pos=10,
            current_pos=5,
            encoded_pos=10,
            original_char_length=1,
            char_length=2,
        ),
        CharacterMapping(
            char="b",
            original_pos=10,
            original_encoded_pos=20,
            current_pos=10,
            encoded_pos=20,
            original_char_length=1,
            char_length=3,
        ),
    ]
    for m in mappings:
        tracker.add(m)

    # Test update before all mappings
    tracker.update(0, 3, 6)
    assert tracker.get()[0].original_pos == 2  # 5 - 3 = 2
    assert tracker.get()[0].encoded_pos == 4  # 10 - 6 = 4
    assert tracker.get()[1].original_pos == 7  # 10 - 3 = 7
    assert tracker.get()[1].encoded_pos == 14  # 20 - 6 = 14

    # Test update overlapping first mapping (should not affect it)
    tracker.update(3, 4, 2)
    # Only second mapping should be affected
    assert tracker.get()[0].original_pos == 2  # Unchanged
    assert tracker.get()[0].encoded_pos == 4  # Unchanged
    assert tracker.get()[1].original_pos == 3  # 7 - 4 = 3
    assert tracker.get()[1].encoded_pos == 12  # 14 - 2 = 12


def test_full_repr_verification():
    """Test UTFHandler __repr__ contains encoding information"""
    text = "Test"
    handler = UTFHandler(text, UTFEncoding.UTF16)
    rep = repr(handler)
    assert "utf-16-le" in rep  # Check actual encoding name
    assert text in rep
    assert "UTFHandler" in rep


def test_encoded_position_boundary_conditions():
    """Test position conversion at multi-byte character boundaries"""
    text = "a🚀b"
    handler = UTFHandler(text, UTFEncoding.UTF16)

    # UTF-16 encoded positions:
    # 'a' (1 code unit) -> pos 0
    # 🚀 (2 code units) -> starts at pos 1
    # 'b' (1 code unit) -> starts at pos 3
    assert handler.get_encoded_position(0) == 0  # 'a'
    assert handler.get_encoded_position(1) == 1  # 🚀 start
    assert handler.get_encoded_position(2) == 3  # 'b' start
