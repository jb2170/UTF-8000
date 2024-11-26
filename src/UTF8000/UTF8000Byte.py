# size_t counting num of bytes; this is the only machine limitation
# big bittian ordered (128, 64, 32, 16, 8, 4, 2, 1)

ZERO               = 0b00000000

ASCII_PREFIX       = 0b00000000
ASCII_PREFIX_MASK  = 0b10000000
ASCII_CONTENT_MASK = 0b01111111

CONTINUATION_PREFIX       = 0b10000000
CONTINUATION_PREFIX_MASK  = 0b11000000
CONTINUATION_CONTENT_MASK = 0b00111111
CONTINUATION_FILLED       = CONTINUATION_PREFIX + 0b00111111

def byte_is_ascii(c: int) -> bool:
    return c & ASCII_PREFIX_MASK == ASCII_PREFIX

def byte_is_continuation(c: int) -> bool:
    return c & CONTINUATION_PREFIX_MASK == CONTINUATION_PREFIX

def byte_idx_0(c: int) -> int:
    return next((
        idx
        for idx, bit in
        enumerate(c & (1 << (8 - 1 - t)) for t in range(8))
        if not bit
    ), 8)

def byte_continuation_content_idx_0(c: int) -> int:
    # could be made part of _byte_idx_0 but whatever
    return next((
        idx
        for idx, bit in
        enumerate(c & (1 << (6 - 1 - t)) for t in range(6))
        if not bit
    ), 6)

class UTF8000Byte:
    def __init__(self, c: int, *,
            is_start_byte:        bool,
            is_continuation_byte: bool,
            is_content_byte:      bool,
        ) -> None:
        self.c = c
        self.is_start_byte        = is_start_byte
        self.is_continuation_byte = is_continuation_byte
        self.is_content_byte      = is_content_byte

    def __str__(self) -> str:
        return f"0b{self.c:08b}"

    def debug_str(self) -> str:
        if self.is_continuation_byte:
            n_continuation_prefix_bits = 2
        else:
            n_continuation_prefix_bits = 0

        if self.is_content_byte:
            n_content_bits = self.n_content_bits
        else:
            n_content_bits = 0

        RESET = "\x1b[0m"
        RED   = "\x1b[31m"
        GREEN = "\x1b[32m"
        BLUE  = "\x1b[34m"
        s = str(self)
        binary_prefix = s[:2]
        continuation_prefix = GREEN + s[2:2+n_continuation_prefix_bits] + RESET
        start_bits          = RED   + s[2+n_continuation_prefix_bits:10 - n_content_bits] + RESET
        content_bits        = BLUE  + s[10 - n_content_bits:] + RESET

        return binary_prefix + continuation_prefix + start_bits + content_bits

    @property
    def is_ascii(self) -> bool:
        return byte_is_ascii(self.c)

    @property
    def n_content_bits(self) -> int:
        if not self.is_content_byte:
            raise ValueError

        if not self.is_continuation_byte:
            idx_0 = byte_idx_0(self.c)
            return (8 - 1 - idx_0)
        elif not self.is_start_byte:
            return 6
        else:
            idx_0_content = byte_continuation_content_idx_0(self.c)
            return (6 - 1 - idx_0_content)

    @property
    def content(self) -> int:
        content_mask = (1 << self.n_content_bits) - 1

        return self.c & content_mask
