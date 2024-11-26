from typing import Generator

from .UTF8000Byte import UTF8000Byte, byte_is_continuation, byte_idx_0, byte_continuation_content_idx_0
from .UTF8000Int import UTF8000Int

class UTF8000IncrementalDecoder:
    def __init__(self) -> None:
        self._results:      list[UTF8000Int] = []
        self._bytes_buffer: bytes            = b""

        self._generator = self._utf_8000_parse_forever()
        self._wakeup()

    def __iter__(self) -> Generator[UTF8000Int, None, None]:
        # queue
        while self._results:
            yield self._results.pop(0)

    def feed(self, utf_8000_bytes: bytes) -> None:
        self._bytes_buffer += utf_8000_bytes
        self._wakeup()

    def _wakeup(self) -> None:
        self._generator.send(None)

    def _await_bytes(self, n_bytes: int) -> Generator[None, None, bytes]:
        while len(self._bytes_buffer) < n_bytes:
            yield

        ret                = self._bytes_buffer[:n_bytes]
        self._bytes_buffer = self._bytes_buffer[n_bytes:]

        return ret

    def _await_byte(self) -> Generator[None, None, int]:
        return (yield from self._await_bytes(1))[0]

    def _await_continuation_byte(self) -> Generator[None, None, int]:
        ret = yield from self._await_byte()
        if not byte_is_continuation(ret):
            self._on_error_invalid_continuation_byte()
        return ret

    def _on_error(self, error_message: str) -> UTF8000Byte:
        raise ValueError(error_message)

    def _on_error_invalid_start_byte(self) -> None:
        # XXX TODO 101: read all following continuation bytes to skip them
        self._on_error("Invalid start byte: continuation byte detected")

    def _on_error_invalid_continuation_byte(self) -> None:
        # XXX TODO 101: should we un-pop this (start) byte so further decodings can continue, and return a replacement character?
        self._on_error("Not a continuation byte prefix")

    def _on_error_overlong(self) -> None:
        # XXX TODO 101: read all following continuation bytes to skip them
        self._on_error("Overlong encoding")

    def _utf_8000_parse_single(self) -> Generator[None, None, UTF8000Int]:
        parsed_bytes: list[UTF8000Byte] = []

        start_byte = yield from self._await_byte()
        idx_0 = byte_idx_0(start_byte)

        if idx_0 == 1:
            self._on_error_invalid_start_byte()
        elif idx_0 == 0:
            n_bytes_expected = 1
        else:
            n_bytes_expected = idx_0
            # when idx_0 == 8, this is 8 *so far!*

        is_content_byte = idx_0 < 7
        parsed_bytes.append(UTF8000Byte(start_byte, is_start_byte = True, is_continuation_byte = False, is_content_byte = is_content_byte))

        # multiple start bytes, the power of UTF-8000!
        if idx_0 == 8:
            while True:
                start_byte = yield from self._await_continuation_byte()
                idx_0_content = byte_continuation_content_idx_0(start_byte)
                n_bytes_expected += idx_0_content

                is_content_byte = idx_0_content < 5
                parsed_bytes.append(UTF8000Byte(start_byte, is_start_byte = True, is_continuation_byte = True, is_content_byte = is_content_byte))

                if idx_0_content != 6:
                    break

        # overlong checking for non-ASCII
        if idx_0 != 0:
            if idx_0 == 2:
                # special case: we're only checking for activity in the first *4* content bits gained from 1-byte (ASCII) to a 2-byte sequence,
                # whereas every other n-byte sequence checks the first *5* content bits, since 5 bits are gained for every additional continuation byte
                anti_overlong_check_mask_start        = 0b00011110
                anti_overlong_check_mask_continuation = 0b00000000 # unused
            else:
                n_bits_overlong_check_continuation = divmod(n_bytes_expected - 2, 6)[1]
                n_bits_overlong_check_start        = 5 - n_bits_overlong_check_continuation
                # lower bits of start byte contents
                anti_overlong_check_mask_start        = (1 << n_bits_overlong_check_start) - 1
                # upper bits of continuation byte contents
                anti_overlong_check_mask_continuation = ((1 << n_bits_overlong_check_continuation) - 1) << (6 - n_bits_overlong_check_continuation)

            continuation_byte = yield from self._await_continuation_byte()

            # at this point `start_byte` is the last start byte
            if not (start_byte & anti_overlong_check_mask_start or continuation_byte & anti_overlong_check_mask_continuation):
                self._on_error_overlong()

            parsed_bytes.append(UTF8000Byte(continuation_byte, is_start_byte = False, is_continuation_byte = True, is_content_byte = True))

        # the rest of the continuation bytes
        while len(parsed_bytes) < n_bytes_expected:
            continuation_byte = yield from self._await_continuation_byte()
            parsed_bytes.append(UTF8000Byte(continuation_byte, is_start_byte = False, is_continuation_byte = True, is_content_byte = True))

        return UTF8000Int(parsed_bytes)

    def _utf_8000_parse_forever(self) -> Generator[None, None, None]:
        while True:
            self._results.append((yield from self._utf_8000_parse_single()))
