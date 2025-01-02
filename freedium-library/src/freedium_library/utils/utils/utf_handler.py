from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from loguru import logger

from freedium_library.utils.utils.mutable_string import MutableString


class UTFEncoding(Enum):
    UTF8 = auto()
    UTF16 = auto()
    UTF32 = auto()

    @property
    def name(self) -> str:
        logger.trace(f"Getting encoding name for {self}")
        name = {
            UTFEncoding.UTF8: "utf-8",
            UTFEncoding.UTF16: "utf-16-le",
            UTFEncoding.UTF32: "utf-32-le",
        }[self]
        logger.trace(f"Encoding name resolved to {name}")
        return name

    @property
    def unit_size(self) -> int:
        logger.trace(f"Getting unit size for encoding {self}")
        size = {
            UTFEncoding.UTF8: 1,
            UTFEncoding.UTF16: 2,
            UTFEncoding.UTF32: 4,
        }[self]
        logger.trace(f"Unit size resolved to {size}")
        return size


@dataclass
class CharacterMapping:
    char: str
    original_pos: int
    original_encoded_pos: int
    current_pos: int
    encoded_pos: int
    original_char_length: int
    char_length: int

    def __post_init__(self):
        logger.trace(f"Validating CharacterMapping for char '{self.char}'")
        if self.original_pos < 0 or self.current_pos < 0:
            logger.error(
                f"Invalid negative position: original_pos={self.original_pos}, current_pos={self.current_pos}"
            )
            raise ValueError("Positions cannot be negative")
        if self.char_length < 1:
            logger.error(f"Invalid character length: {self.char_length}")
            raise ValueError("Character length must be positive")
        logger.trace("CharacterMapping validation successful")

    def shift_positions(self, offset: int, encoded_offset: int) -> None:
        logger.trace(
            f"Shifting positions for char '{self.char}': offset={offset}, encoded_offset={encoded_offset}"
        )
        logger.debug(
            f"Before shift: current_pos={self.current_pos}, encoded_pos={self.encoded_pos}"
        )
        self.current_pos += offset
        self.encoded_pos += encoded_offset
        logger.debug(
            f"After shift: current_pos={self.current_pos}, encoded_pos={self.encoded_pos}"
        )


@dataclass
class PositionTracker:
    """Tracks and manages character position mappings for UTF encoding.

    Handles the storage, retrieval, and manipulation of character mappings
    between original string positions and their encoded positions.
    """

    _position_mappings: List[CharacterMapping]
    _original_positions: List[int]

    def __init__(self):
        """Initialize empty position tracker."""
        logger.debug("Initializing new PositionTracker")
        self._position_mappings = []
        self._original_positions = []
        logger.trace("PositionTracker initialized with empty mappings")

    def add(self, mapping: CharacterMapping, insert_idx: Optional[int] = None) -> None:
        """Add a new character mapping.

        Args:
            mapping: CharacterMapping object to add
            insert_idx: Optional index to insert at specific position
        """
        logger.debug(
            f"Adding new mapping for char '{mapping.char}' at position {mapping.current_pos}"
        )
        if insert_idx is None:
            logger.trace("Appending mapping to end of list")
            self._position_mappings.append(mapping)
        else:
            logger.trace(f"Inserting mapping at index {insert_idx}")
            self._position_mappings.insert(insert_idx, mapping)
        logger.debug(f"Current mapping count: {len(self._position_mappings)}")

    def get(self) -> List[CharacterMapping]:
        """Get copy of all character mappings.

        Returns:
            List of CharacterMapping objects
        """
        logger.trace("Getting copy of all character mappings")
        logger.debug(f"Returning {len(self._position_mappings)} mappings")
        return self._position_mappings.copy()

    def clear(self, start: int, length: int) -> int:
        """Clear mappings within specified range.

        Args:
            start: Starting position to clear from
            length: Number of positions to clear

        Returns:
            Number of mappings that were cleared
        """
        logger.debug(f"Clearing mappings from position {start} to {start + length}")
        original_count = len(self._position_mappings)
        logger.trace(f"Original mapping count: {original_count}")

        self._position_mappings = [
            mapping
            for mapping in self._position_mappings
            if not (start <= mapping.original_pos < start + length)
        ]

        cleared_count = original_count - len(self._position_mappings)
        logger.debug(f"Cleared {cleared_count} mappings")
        logger.trace(f"Remaining mappings: {len(self._position_mappings)}")
        return cleared_count

    def update(self, start: int, length: int, encoded_length: int) -> None:
        """Update positions of mappings after a modification.

        Args:
            start: Position where modification occurred
            length: Length of original content modified
            encoded_length: Length of new encoded content
        """
        logger.debug(
            f"Updating mappings: start={start}, length={length}, encoded_length={encoded_length}"
        )
        for mapping in self._position_mappings:
            if mapping.original_pos >= start + length:
                logger.trace(f"Updating mapping for char '{mapping.char}'")
                logger.trace(
                    f"Before update: original_pos={mapping.original_pos}, encoded_pos={mapping.encoded_pos}"
                )
                mapping.original_pos -= length
                mapping.encoded_pos -= encoded_length
                logger.trace(
                    f"After update: original_pos={mapping.original_pos}, encoded_pos={mapping.encoded_pos}"
                )


class UTFHandler(ABC):
    __slots__ = ("_string", "_encoding", "_position_tracker")

    def __init__(self, string: str, encoding: UTFEncoding):
        logger.info(f"Initializing UTFHandler with encoding {encoding}")
        logger.debug(f"Input string length: {len(string)}")
        self._string = MutableString(string)
        self._encoding = encoding
        self._position_tracker = PositionTracker()
        logger.debug("Initializing character mappings")
        self._initialize_mappings()
        logger.info("UTFHandler initialization complete")

    def _initialize_mappings(self) -> None:
        logger.debug("Beginning mapping initialization")
        current_pos = 0
        encoded_pos = 0

        for i, char in enumerate(self._string):
            logger.trace(f"Processing character '{char}' at position {i}")
            encoded_bytes = char.encode(self._encoding.name)
            char_len = len(encoded_bytes) // self._encoding.unit_size
            logger.trace(f"Encoded length: {char_len} units")

            if char_len > 1:
                logger.debug(f"Found multi-byte character '{char}' at position {i}")
                mapping = CharacterMapping(
                    char=char,
                    original_pos=i,
                    current_pos=current_pos,
                    encoded_pos=encoded_pos,
                    char_length=char_len,
                    original_char_length=len(char),
                    original_encoded_pos=encoded_pos,
                )
                logger.trace(f"Created mapping: {mapping}")
                self._position_tracker.add(mapping)

            current_pos += 1
            encoded_pos += char_len
            logger.trace(
                f"Updated positions: current={current_pos}, encoded={encoded_pos}"
            )

        logger.debug("Mapping initialization complete")

    def get_encoded_position(self, original_pos: int) -> int:
        encoded_pos = original_pos

        for mapping in self._position_tracker.get():
            if mapping.original_pos < original_pos:
                encoded_pos += mapping.char_length - 1
            elif mapping.original_pos == original_pos:
                return mapping.encoded_pos
            else:
                break

        return encoded_pos

    def get_original_position(self, encoded_pos: int) -> int:
        logger.debug(f"Converting encoded position {encoded_pos} to original position")
        original_pos = encoded_pos

        for mapping in self._position_tracker.get():
            logger.trace(
                f"Checking mapping for char '{mapping.char}' at encoded position {mapping.encoded_pos}"
            )
            if mapping.encoded_pos < encoded_pos:
                logger.trace(
                    f"Adjusting for multi-byte character: -{mapping.char_length + 1}"
                )
                original_pos -= mapping.char_length + 1
            else:
                break

        logger.debug(f"Final original position: {original_pos}")
        return original_pos

    def insert(self, encoded_position: int, string_to_insert: str) -> None:
        logger.info(
            f"Inserting '{string_to_insert}' at encoded position {encoded_position}"
        )

        encoding_name = self._encoding.name
        insert_encoded_len = (
            len(string_to_insert.encode(encoding_name)) // self._encoding.unit_size
        )
        logger.debug(f"Encoded insertion length: {insert_encoded_len}")

        original_position = self.get_original_position(encoded_position)
        logger.debug(f"Corresponding original position: {original_position}")

        logger.debug("Updating existing mappings")
        for mapping in self._position_tracker.get():
            if mapping.encoded_pos >= encoded_position:
                logger.trace(f"Shifting mapping for char '{mapping.char}'")
                mapping.shift_positions(len(string_to_insert), insert_encoded_len)

        logger.debug("Adding mappings for inserted string")
        self._add_new_mappings(string_to_insert, original_position, encoded_position)

        logger.debug(f"Inserting string at position {original_position}")
        self._string.insert(original_position, string_to_insert)
        logger.info(f"Insert complete. New string: '{self._string}'")

    def _add_new_mappings(
        self, string_to_insert: str, original_position: int, encoded_position: int
    ) -> None:
        logger.debug(f"Adding new mappings for string '{string_to_insert}'")
        current_pos = original_position
        encoded_pos = encoded_position

        for char in string_to_insert:
            logger.trace(f"Processing character '{char}'")
            encoded_char_len = (
                len(char.encode(self._encoding.name)) // self._encoding.unit_size
            )
            logger.trace(f"Encoded character length: {encoded_char_len}")

            if encoded_char_len > 1:
                logger.debug(f"Found multi-byte character '{char}'")
                new_mapping = CharacterMapping(
                    original_pos=current_pos,
                    current_pos=current_pos,
                    encoded_pos=encoded_pos,
                    char_length=encoded_char_len,
                    original_char_length=len(char),
                    original_encoded_pos=encoded_pos,
                    char=char,
                )

                insert_idx = next(
                    (
                        i
                        for i, m in enumerate(self._position_tracker.get())
                        if m.encoded_pos > new_mapping.encoded_pos
                    ),
                    len(self._position_tracker.get()),
                )

                logger.debug(f"Inserting new mapping at index {insert_idx}")
                self._position_tracker.add(new_mapping, insert_idx)

            current_pos += 1
            encoded_pos += encoded_char_len
            logger.trace(
                f"Updated positions: current={current_pos}, encoded={encoded_pos}"
            )

        logger.debug("Finished adding new mappings")

    def delete(self, start: int, length: int) -> None:
        logger.debug(f"Entering delete method with start={start}, length={length}")
        logger.info(
            f"Initiating deletion of {length} characters starting at position {start}"
        )

        logger.trace("Calculating encoded positions for deletion")
        start_encoded = self.get_encoded_position(start)
        logger.debug(f"Calculated start encoded position: {start_encoded}")

        end_pos = start + length
        logger.trace(f"Calculated end position: {end_pos}")

        end_encoded = self.get_encoded_position(end_pos)
        logger.debug(f"Calculated end encoded position: {end_encoded}")

        encoded_length = end_encoded - start_encoded
        logger.info(f"Calculated encoded length to delete: {encoded_length}")

        logger.trace("Updating remaining position mappings")
        for mapping in self._position_tracker.get():
            if mapping.original_pos >= end_pos:
                logger.debug(
                    f"Adjusting mapping for character at position {mapping.original_pos}"
                )
                mapping.original_pos -= length
                mapping.current_pos -= length
                mapping.encoded_pos -= encoded_length
                mapping.original_encoded_pos -= encoded_length
                logger.trace(f"Updated mapping: {mapping}")

        logger.debug("Performing deletion on underlying string")
        self._string.delete(start, length)
        logger.info(
            f"Delete operation complete. New string length: {len(self._string)}"
        )
        logger.trace(f"Updated string contents: '{self._string}'")

    def get_string_slice(self, start: int, end: int) -> List[str]:
        logger.debug(f"Getting string slice from {start} to {end}")
        result = list(self._string[start:end])
        logger.trace(f"Slice result: {result}")
        return result

    def __getitem__(self, key: int) -> str:
        logger.debug(f"Getting character at index {key}")
        result = "".join(self._string[key])
        logger.trace(f"Retrieved character: '{result}'")
        return result

    def __str__(self) -> str:
        logger.debug("Converting to string representation")
        result = str(self._string)
        logger.trace(f"String representation: '{result}'")
        return result

    def __repr__(self) -> str:
        logger.debug("Getting detailed string representation")
        result = f"{self.__class__.__name__}(string='{self.__str__()}', encoding={self._encoding.name})"
        logger.trace(f"Detailed representation: {result}")
        return result
        logger.debug("Converting to string representation")
        result = str(self._string)
        logger.trace(f"String representation: '{result}'")
        return result

    def __repr__(self) -> str:
        logger.debug("Getting detailed string representation")
        result = f"{self.__class__.__name__}(string='{self.__str__()}', encoding={self._encoding.name})"
        logger.trace(f"Detailed representation: {result}")
        return result
