#!/usr/bin/env python3

from UTF8000 import UTF8000IncrementalDecoder

def main() -> None:
    decoder = UTF8000IncrementalDecoder()

    b = bytes([
        0b11111111,  0b10_111111, 0b10_110000, 0b10_010000,
        0b10_000000, 0b10_000000, 0b10_000000, 0b10_000000,
    ])
    decoder.feed(b)
    for utf_8000_int in decoder:
        print(utf_8000_int.debug_str()) # nothing

    b = bytes([
        0b10_000000, 0b10_000000, 0b10_000000, 0b10_000000,
        0b10_000000, 0b10_000000, 0b10_000000, 0b10_000001,
    ])
    decoder.feed(b)
    for utf_8000_int in decoder:
        print(utf_8000_int.debug_str()) # single UTF-8000 int
        print(int(utf_8000_int))        # a big big number

if __name__ == "__main__":
    main()
