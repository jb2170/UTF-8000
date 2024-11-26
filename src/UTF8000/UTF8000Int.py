from .UTF8000Byte import UTF8000Byte

class UTF8000Int:
    def __init__(self, utf_8000_bytes: list[UTF8000Byte]) -> None:
        # No validation is done; we're assuming these come from `UTF8000IncrementalDecoder`
        self.utf_8000_bytes = utf_8000_bytes

    def __str__(self) -> str:
        return " ".join(str(b) for b in self.utf_8000_bytes)

    def debug_str(self) -> str:
        return " ".join(b.debug_str() for b in self.utf_8000_bytes)

    def __int__(self) -> int:
        ret = 0
        content_bytes = (b for b in self.utf_8000_bytes if b.is_content_byte)
        for content_byte in content_bytes:
            ret <<= content_byte.n_content_bits
            ret += content_byte.content
        return ret

    @property
    def n_bytes(self) -> int:
        return len(self.utf_8000_bytes)

    @property
    def n_bits_capacity(self) -> int:
        if self.n_bytes == 1:
            return 7
        else:
            return 1 + 5 * self.n_bytes
