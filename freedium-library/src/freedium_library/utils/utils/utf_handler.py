from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from typing import List

from loguru import logger

from freedium_library.utils.utils.mutable_string import MutableString


class UTFEncoding(Enum):
    UTF8 = auto()
    UTF16 = auto()
    UTF32 = auto()

    @property
    def encoding_name(self) -> str:
        return {
            UTFEncoding.UTF8: "utf-8",
            UTFEncoding.UTF16: "utf-16-le",
            UTFEncoding.UTF32: "utf-32-le",
        }[self]


@dataclass
class CharacterMapping:
    char: str
    original_pos: int
    original_encoded_pos: int
    current_pos: int
    encoded_pos: int
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


class UTFHandler(ABC):
    def __init__(self, string: str, encoding: UTFEncoding):
        logger.debug(
            f"Initializing UTFHandler with string: '{string}' and encoding: {encoding}"
        )
        logger.trace(f"String length: {len(string)}")
        logger.trace(f"Encoding: {encoding}")

        self._string = MutableString(string)
        self._encoding = encoding
        self._position_mappings: List[CharacterMapping] = []
        self._original_positions: List[int] = []

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
        encoded_bytes = len(self._string.encode(self._encoding.encoding_name))
        logger.trace(f"Encoded bytes: {encoded_bytes}")
        encoded_len = encoded_bytes // self._get_encoding_unit_size()
        logger.trace(f"Encoded length: {encoded_len}")
        return encoded_len

    def _get_encoding_unit_size(self) -> int:
        unit_size = {UTFEncoding.UTF8: 1, UTFEncoding.UTF16: 2, UTFEncoding.UTF32: 4}[
            self._encoding
        ]
        logger.trace(f"Encoding unit size for {self._encoding}: {unit_size}")
        return unit_size

    def _initialize_mappings(self) -> None:
        logger.debug("Starting character mappings initialization")
        current_pos = 0
        encoded_pos = 0

        for i in range(len(self._string)):
            char = self._string[i]
            char_len = (
                len(char.encode(self._encoding.encoding_name))
                // self._get_encoding_unit_size()
            )
            logger.trace(
                f"Processing char '{char}' at position {i} with encoded length {char_len}"
            )

            if char_len > 1:
                logger.debug(f"Found multi-byte character '{char}' at position {i}")
                logger.trace("Creating CharacterMapping with:")
                logger.trace(f"  original_pos={i}")
                logger.trace(f"  current_pos={current_pos}")
                logger.trace(f"  encoded_pos={encoded_pos}")
                logger.trace(f"  char_length={char_len}")
                logger.trace(f"  original_encoded_pos={encoded_pos}")
                logger.trace(f"  char='{char}'")

                self._position_mappings.append(
                    CharacterMapping(
                        original_pos=i,
                        current_pos=current_pos,
                        encoded_pos=encoded_pos,
                        char_length=char_len,
                        original_encoded_pos=encoded_pos,
                        char=char,
                    )
                )

            current_pos += 1
            encoded_pos += char_len

        logger.debug(
            f"Finished initialization. Found {len(self._position_mappings)} multi-byte characters"
        )
        logger.trace(f"Position mappings: {self._position_mappings}")

    def get_encoded_position(self, original_pos: int) -> int:
        logger.debug(f"Converting original position {original_pos} to encoded position")
        encoded_pos = original_pos

        for mapping in self._position_mappings:
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

        for mapping in self._position_mappings:
            if mapping.encoded_pos < encoded_pos:
                original_pos -= mapping.char_length - 1
                logger.trace(f"Adjusting original position: {original_pos}")
            else:
                break

        logger.debug(f"Final original position: {original_pos}")
        return original_pos

    @property
    def original_string(self) -> str:
        logger.trace("Retrieving original string")
        return str(self._string)

    @property
    def position_mappings(self) -> List[CharacterMapping]:
        logger.trace("Retrieving position mappings")
        return self._position_mappings.copy()

    def insert(self, position: int, string_to_insert: str) -> None:
        logger.info(f"Inserting '{string_to_insert}' at position {position}")
        encoding_name = self._encoding.encoding_name
        encoded_position = self.get_encoded_position(position)
        insert_encoded_len = (
            len(string_to_insert.encode(encoding_name))
            // self._get_encoding_unit_size()
        )
        logger.debug(
            f"Encoded insertion position: {encoded_position}, encoded length: {insert_encoded_len}"
        )

        for mapping in self._position_mappings:
            if mapping.original_pos >= position:
                old_pos = mapping.current_pos
                old_encoded = mapping.encoded_pos
                mapping.shift_positions(len(string_to_insert), insert_encoded_len)
                logger.trace(
                    f"Shifted mapping: {old_pos}->{mapping.current_pos}, {old_encoded}->{mapping.encoded_pos}"
                )

        self._add_new_mappings(string_to_insert, position, encoded_position)
        self._string.insert(encoded_position, string_to_insert)
        logger.debug(f"Insert complete. New string: '{self._string}'")

    def _add_new_mappings(
        self, string_to_insert: str, start_pos: int, start_encoded_pos: int
    ) -> None:
        logger.debug("Adding new mappings for inserted string")
        logger.trace(
            f"Start position: {start_pos}, Start encoded position: {start_encoded_pos}"
        )
        current_pos = start_pos
        encoded_pos = start_encoded_pos

        for char in string_to_insert:
            char_len = (
                len(char.encode(self._encoding.encoding_name))
                // self._get_encoding_unit_size()
            )
            logger.trace(f"Processing char '{char}' with length {char_len}")

            if char_len > 1:
                logger.debug(f"Found multi-byte character '{char}'")
                new_mapping = CharacterMapping(
                    original_pos=current_pos,
                    current_pos=current_pos,
                    encoded_pos=encoded_pos,
                    char_length=char_len,
                    original_encoded_pos=encoded_pos,
                    char=char,
                )

                insert_idx = next(
                    (
                        i
                        for i, m in enumerate(self._position_mappings)
                        if m.current_pos > new_mapping.current_pos
                    ),
                    len(self._position_mappings),
                )

                logger.trace(f"Inserting new mapping at index {insert_idx}")
                self._position_mappings.insert(insert_idx, new_mapping)

            current_pos += 1
            encoded_pos += char_len

        logger.debug(f"New position mappings: {self._position_mappings}")

    def delete(self, start: int, length: int) -> None:
        logger.info(f"Deleting {length} characters starting at position {start}")
        start_encoded = self.get_encoded_position(start)
        end_encoded = self.get_encoded_position(start + length)
        encoded_length = end_encoded - start_encoded
        logger.debug(
            f"Encoded deletion range: {start_encoded} to {end_encoded} (length: {encoded_length})"
        )

        original_mapping_count = len(self._position_mappings)
        self._position_mappings = [
            mapping
            for mapping in self._position_mappings
            if not (start <= mapping.original_pos < start + length)
        ]
        logger.debug(
            f"Removed {original_mapping_count - len(self._position_mappings)} mappings"
        )

        for mapping in self._position_mappings:
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
        return self.original_string

    def __repr__(self) -> str:
        logger.trace("Getting detailed string representation")
        return f"{self.__class__.__name__}(string='{self.original_string}', encoding={self._encoding.name})"
