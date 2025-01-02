from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from typing import List, Optional

from loguru import logger

from freedium_library.utils.utils.mutable_string import MutableString


class UTFEncoding(Enum):
    UTF8 = auto()
    UTF16 = auto()
    UTF32 = auto()

    @property
    def name(self) -> str:
        return {
            UTFEncoding.UTF8: "utf-8",
            UTFEncoding.UTF16: "utf-16-le",
            UTFEncoding.UTF32: "utf-32-le",
        }[self]

    @property
    def unit_size(self) -> int:
        return {
            UTFEncoding.UTF8: 1,
            UTFEncoding.UTF16: 2,
            UTFEncoding.UTF32: 4,
        }[self]


@dataclass
class CharacterMapping:
    char: str
    original_pos: int
    original_encoded_pos: int
    current_pos: int
    encoded_pos: int
    original_char_length: int
    char_length: int

    def shift_positions(self, offset: int, encoded_offset: int) -> None:
        logger.trace(
            f"Shifting positions: offset={offset}, encoded_offset={encoded_offset}"
        )
        logger.trace(
            f"Before shift: current_pos={self.current_pos}, encoded_pos={self.encoded_pos}"
        )
        self.current_pos += offset
        self.encoded_pos += encoded_offset
        logger.trace(
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
        self._position_mappings = []
        self._original_positions = []

    def add(self, mapping: CharacterMapping, insert_idx: Optional[int] = None) -> None:
        """Add a new character mapping.

        Args:
            mapping: CharacterMapping object to add
            insert_idx: Optional index to insert at specific position
        """
        if insert_idx is None:
            self._position_mappings.append(mapping)
        else:
            self._position_mappings.insert(insert_idx, mapping)

    def get(self) -> List[CharacterMapping]:
        """Get copy of all character mappings.

        Returns:
            List of CharacterMapping objects
        """
        return self._position_mappings.copy()

    def clear(self, start: int, length: int) -> int:
        """Clear mappings within specified range.

        Args:
            start: Starting position to clear from
            length: Number of positions to clear

        Returns:
            Number of mappings that were cleared
        """
        original_count = len(self._position_mappings)
        self._position_mappings = [
            mapping
            for mapping in self._position_mappings
            if not (start <= mapping.original_pos < start + length)
        ]
        return original_count - len(self._position_mappings)

    def update(self, start: int, length: int, encoded_length: int) -> None:
        """Update positions of mappings after a modification.

        Args:
            start: Position where modification occurred
            length: Length of original content modified
            encoded_length: Length of new encoded content
        """
        for mapping in self._position_mappings:
            if mapping.original_pos >= start + length:
                mapping.original_pos -= length
                mapping.encoded_pos -= encoded_length


class UTFHandler(ABC):
    def __init__(self, string: str, encoding: UTFEncoding):
        logger.debug(
            f"Initializing UTFHandler with string: '{string}' and encoding: {encoding}"
        )
        logger.trace(f"String length: {len(string)}")
        logger.trace(f"Encoding: {encoding}")

        self._string = MutableString(string)
        self._encoding = encoding
        self._position_tracker = PositionTracker()

        logger.trace("Calling _initialize_mappings()")
        self._initialize_mappings()

    @cached_property
    def _string_len(self) -> int:
        length = len(self._string)
        logger.trace(f"Calculating string length: {length}")
        return length

    @cached_property
    def _encoded_len(self) -> int:
        logger.trace("Calculating encoded length")
        encoded_bytes = len(self._string.encode(self._encoding.name))
        logger.trace(f"Encoded bytes: {encoded_bytes}")
        encoded_len = encoded_bytes // self._encoding.unit_size
        logger.trace(f"Encoded length: {encoded_len}")
        return encoded_len

    def _initialize_mappings(self) -> None:
        logger.debug("Starting character mappings initialization")
        current_pos = 0
        encoded_pos = 0

        for i in range(len(self._string)):
            char = self._string[i]
            char_len = len(char.encode(self._encoding.name)) // self._encoding.unit_size

            if char_len > 1:
                logger.debug(f"Found multi-byte character '{char}' at position {i}")
                mapping = CharacterMapping(
                    original_pos=i,
                    current_pos=current_pos,
                    encoded_pos=encoded_pos,
                    char_length=char_len,
                    original_char_length=len(char),
                    original_encoded_pos=encoded_pos,
                    char=char,
                )
                self._position_tracker.add(mapping)

            current_pos += 1
            encoded_pos += char_len

    def get_encoded_position(self, original_pos: int) -> int:
        logger.debug(f"Converting original position {original_pos} to encoded position")
        encoded_pos = original_pos

        for mapping in self._position_tracker.get():
            if mapping.original_pos < original_pos:
                encoded_pos += mapping.char_length - 1
                logger.trace(
                    f"Adjusting for mapping at {mapping.original_pos}, new encoded_pos: {encoded_pos}"
                )
            elif mapping.original_pos == original_pos:
                encoded_pos = mapping.encoded_pos
                logger.debug(f"Direct mapping found, encoded_pos set to {encoded_pos}")
                break
            else:
                break

        logger.debug(f"Final encoded position: {encoded_pos}")
        return encoded_pos

    def get_original_position(self, encoded_pos: int) -> int:
        logger.debug(f"Converting encoded position {encoded_pos} to original position")
        original_pos = encoded_pos

        for mapping in self._position_tracker.get():
            if mapping.encoded_pos < encoded_pos:
                original_pos -= mapping.char_length + 1
                logger.trace(f"Adjusting original position: {original_pos}")
            else:
                break

        logger.debug(f"Final original position: {original_pos}")
        return original_pos

    @property
    def position_mappings(self) -> List[CharacterMapping]:
        return self._position_tracker.get()

    def insert(self, encoded_position: int, string_to_insert: str) -> None:
        logger.info(
            f"Inserting '{string_to_insert}' at encoded position {encoded_position}"
        )

        encoding_name = self._encoding.name
        insert_encoded_len = (
            len(string_to_insert.encode(encoding_name)) // self._encoding.unit_size
        )
        logger.debug(f"Encoded insertion length: {insert_encoded_len}")

        # Find the original position that corresponds to the encoded position
        original_position = self.get_original_position(encoded_position)

        # Shift existing mappings that are after the insertion point
        for mapping in self._position_tracker.get():
            if mapping.encoded_pos >= encoded_position:
                mapping.shift_positions(len(string_to_insert), insert_encoded_len)

        # Add new mappings for the inserted string
        self._add_new_mappings(string_to_insert, original_position, encoded_position)

        # Insert the string at the correct position
        self._string.insert(original_position, string_to_insert)
        logger.debug(f"Insert complete. New string: '{self._string}'")

    def _add_new_mappings(
        self, string_to_insert: str, original_position: int, encoded_position: int
    ) -> None:
        logger.debug("Adding new mappings for inserted string")
        current_pos = original_position
        encoded_pos = encoded_position

        for char in string_to_insert:
            encoded_char_len = (
                len(char.encode(self._encoding.name)) // self._encoding.unit_size
            )
            logger.trace(f"Processing char '{char}' with length {encoded_char_len}")

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

                # Find the correct position to insert the new mapping
                insert_idx = next(
                    (
                        i
                        for i, m in enumerate(self._position_tracker.get())
                        if m.encoded_pos > new_mapping.encoded_pos
                    ),
                    len(self._position_tracker.get()),
                )

                logger.trace(f"Inserting new mapping at index {insert_idx}")
                self._position_tracker.add(new_mapping, insert_idx)

            current_pos += 1
            encoded_pos += encoded_char_len

        logger.debug(f"New position mappings: {self._position_tracker.get()}")

    def delete(self, start: int, length: int) -> None:
        logger.info(f"Deleting {length} characters starting at position {start}")
        start_encoded = self.get_encoded_position(start)
        end_encoded = self.get_encoded_position(start + length)
        encoded_length = end_encoded - start_encoded
        logger.debug(
            f"Encoded deletion range: {start_encoded} to {end_encoded} (length: {encoded_length})"
        )

        original_mapping_count = len(self._position_tracker.get())
        self._position_tracker.clear(start, length)
        logger.debug(
            f"Removed {original_mapping_count - len(self._position_tracker.get())} mappings"
        )

        for mapping in self._position_tracker.get():
            if mapping.original_pos >= start + length:
                old_pos = mapping.original_pos
                old_encoded = mapping.encoded_pos
                mapping.original_pos -= length
                mapping.encoded_pos -= encoded_length
                logger.trace(
                    f"Updated mapping: {old_pos}->{mapping.original_pos}, {old_encoded}->{mapping.encoded_pos}"
                )

        self._string.delete(start, length)
        logger.debug(f"Delete complete. New string: '{self._string}'")

    def get_string_slice(self, start: int, end: int) -> List[str]:
        logger.trace(f"Getting string slice from {start} to {end}")
        return list(self._string[start:end])

    def __getitem__(self, key: int) -> str:
        logger.trace(f"Getting character at index {key}")
        return "".join(self._string[key])

    @property
    def encoded_length(self) -> int:
        logger.trace("Retrieving encoded length")
        return self._encoded_len

    def __str__(self) -> str:
        logger.trace("Converting to string representation")
        return str(self._string)

    def __repr__(self) -> str:
        logger.trace("Getting detailed string representation")
        return f"{self.__class__.__name__}(string='{self.__str__()}', encoding={self._encoding.name})"
