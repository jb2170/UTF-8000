# UTF-8000

Unlimited UTF-8!

ASCII ⊆ UTF-8 ⊆ UTF-8000

## TLDR

An example 10-byte (51 content bit) UTF-8000 encoded integer is given below

```
# 10-byte UTF-8000
11111111 10110xxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx
```

Observe the completely filled first start byte, and the `0`-terminated start sequence of `1`s continues into the second byte, which maintains its continuation byte prefix. The remaining 51 free bits of encodable information are denoted by `x`s.

## The Quick Rundown

UTF-8 is the beautiful encoding scheme of Unicode Codepoints (read 'integers') that perfectly extends 7-bit ASCII embedded within the lower bits of 8-bit bytes (`0xxxxxxx`) into a multi-byte encoding, by recognising that one can turn the leading `0` of ASCII into a prefix-free code.

| prefix | example-byte | usage |
| -      | -            | -                                          |
| 0      | `0xxxxxxx`   | 1 byte (ASCII)                             |
| 10     | `10xxxxxx`   | continuation byte for non-ASCII codepoints |
| 110    | `110xxxxx`   | start byte of 2-byte codepoints            |
| 1110   | `1110xxxx`   | start byte of 3-byte codepoints            |
| 11110  | `11110xxx`   | start byte of 4-byte codepoints            |

For an example 3-byte UTF-8 encoding, the Sinhalese letter 'ඞ' (U+0D9E), codepoint number (0x0D9E hex, 3486 decimal, 0b0000110110011110 binary) is encoded as `11100000 10110110 10011110`.

Annotating the codepoint and its UTF-8 encoding respectively, this is `0b0000|110110|011110` mapped to `1110|0000 10|110110 10|011110` in the clear segmented-inclusion-mapping way. There are a few observations.

- We can uniquely tell what class a byte belongs to by inspecting how many 1s it starts with. This is because of the prefix-free design of the start sequences of UTF-8 bytes, as previously mentioned
- The number of `1`s in the start sequence for non-ASCII codepoints is equal to the number of bytes expected
- This codepoint could not be encoded with less than three bytes
- This codepoint could be encoded with more than three bytes, eg as `11110000 10000000 10110110 10011110`, but UTF-8 purposely forbids these 'overlong' encodings. One reason is the unnecessary redundancy, another is a security reason, which at best could cause a segfault, but at worst could be a really nasty CVE:

    - \> be me, a poorly implemented UTF-8 parser
    - \> passed the bytes `01001000 01101001 00100001 11000000 10000000` for decoding
    - \> decode it as "Hi!\0"
    - \> oh boy, the string ends in a null *character*!
    - \> I don't need to append a null *byte* `00000000` of my own
    - \> I'm going to pass `01001000 01101001 00100001 11000000 10000000` directly to `strcat(3)`
    - \> That was easy-Segmentation fault (core dumped)

- If we received a corrupted sequence of UTF-8 bytes, say missing or extra continuation bytes, or an invalid start byte, we can read-and-discard from the sequence until the next start byte, which we can continue with unimpaired. Similarly if we randomly `fseek(3)`-ed to an offset in a file / sequence of bytes, we can read-and-discard until we reach the next start byte. This is known as 'self-synchronization'; we do not need knowledge of absolute position or knowledge of all previous bytes to continue working.

### UTF-16 rant

Unicode's codepoint range stops at U+10FFFF (1114111 decimal) since this is the maximum codepoint encodable by all three of UTF-{8,16,32}. It is the abomination of UTF-16, a multi-16-bit encoding, which sets this lower bound. UTF-16 is inflexible and inextensible, and denies the encoding of the ranges 0xDC00-0xDFFF and 0xD800-0xDBFF, because it uses these to clunkily tack-on more than 64k codepoints. Oh, and UTF-16 is endianness dependent, thus it introduces a special BOM, yuck!

UTF-8 >>>> UTF-16 is one of the many instances where a couple of legendary individuals (Ken Thompson, Rob Pike) achieve more, in a simpler way, than any bureaucratic ISO organisation ever could.

UTF-8 is a peak example of the UNIX philosophy: extensibility, and simplicity.

### UTF-8000

UTF-8 is only artificially limited by UTF-16's upper bounds. Let's investigate how to expand it infinitely, trying to keep the important properties we observed earlier.

We could clearly expand the 4-byte sequences to go all the way up to `11110111 10111111 10111111 10111111` (2 ** 21 - 1, 0x1FFFFF).

We could even expand past 4-byte sequences in the obvious way, all the way up to 7-byte UTF-8. This would have 36 bits of encodable information (which we will refer to as 'content bits' from here on out), and would look like the following:

```
# 7-byte UTF-8
11111110 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx
```

The first byte is now completely filled with the start sequence. How could we implement 8-byte UTF-8? One conjecture may be to just swap the final `0` in the start byte for a `1`, and add another continuation byte on. This would gain us another 6 content bits in the last continuation byte, however this short-sighted approach closes off any natural avenues to a UTF-8 beyond 8 bytes. Those *6* bits gained also breaks a pattern; Observe that for each continuation byte added in non-ASCII UTF-8 sequences, eg from 2-byte to 3-byte, or 3-byte to 4-byte, or 4-byte to 5-byte etc, we gain 6 bits from the continuation byte, but lose one bit in the start byte, meaning we only gain *5* content bits each time we add on another continuation byte.

Therefore lest we introduce more special cases, we stick with our `0`-terminated start sequence and let it roll over into the first continuation byte. 8-byte 'UTF-8' is given as follows:

```
# 8-byte UTF-8
11111111 100xxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx
```

From this point forward, because we wish to extend some terminology, we will start referring to '**UTF-8000**' instead of UTF-8. In UTF-8000 we can have multiple 'start bytes', which are no longer mutually exclusive with UTF-8's concept of 'continuation bytes'. For example in 8-byte UTF-8000 we have two start bytes.

In an n-byte UTF-8000 sequence, with n > 1, the start with a sequence of n `1`s, followed by a `0` is embedded within as many bytes as we need in the by-now obvious way. For example a 23 byte sequence is encoded as:

```
# 23-byte UTF-8000
11111111 10111111 10111111 101110xx 10xxxxxx 10xxxxxx ... 10xxxxxx
```

### UTF-8000's Properties

Let's check how this definition of UTF-8000 holds up.

- UTF-8000 preserves the property of self-synchronization we observed in UTF-8: if we encounter an error, keep reading-and-discarding until we reach a non-continuation byte (ie the *first* start byte of a UTF-8000 sequence)
- By definition we preserve the property of a start sequence of n `1`s followed by a `0` telling us we expect n bytes. This eclipses / supersedes / extends UTF-8's ability to distinguish between byte 'classes' by inspecting a single byte's prefix

The only thing to really define now is the method of checking against overlong encodings. To do so, one first observes that the number of encoded bits in n-byte UTF-8000 is expressed easily:

| how many bytes of UTF-8000 | how many content bits | how many content bits gained |
| -                          | -                     | -                            |
| n = 1 (ASCII)              | 7                     | -                            |
| n = 2                      | 5n + 1 ( = 11)        | 4                            |
| n > 2                      | 5n + 1                | 5                            |

As if it wasn't obvious at this point, the '5n + 1' formula here hints that we can store arbitrarily large integers with UTF-8000! Now, back to anti-overlong checking:

ASCII does not have a concept of overlong encoding.

Two byte UTF-8000 (`110xxxxx 10xxxxxx`) needs to check for 'activity' (not all zeros) within its first four content bits, lest that be an overlong encoding of an ASCII codepoint. Fun fact: it is for this reason that one will never ever see the bytes 0xC0 or 0xC1 in a valid UTF-8 or UTF-8000 stream!

For all other n > 2 we need to check for activity in the first five content bits. After some doodling on paper writing out the first few bytes of each of 3 to 20 byte UTF-8000, one notices that $5 - ((n - 2) \text{ mod } 6)$ content bits exist in the final start byte, and $(n - 2) \text{ mod } 6$ in the next byte that we need to check for activity. That might look ugly but it turns out to be easy to program in our UTF-8000 decoder.

### Success!

And with that I'm happy with UTF-8000's definition! To me this passes the UNIX philosophy check: it is a simple extension of UTF-8 with no more special cases introduced, and is *infinitely* extensible! It is better than [other](https://www.youtube.com/watch?v=tAMDtH9uq1Y) suggested alternative(s) which fail to preserve the self synchronization property.

### The Incremental Decoder

Honestly just check out my [UTF8000IncrementalDecoder](./src/UTF8000/UTF8000IncrementalDecoder.py) file, in particular the `_utf_8000_parse_single` method. It's documented code which is easy to follow.

The most remarkable thing about the code is my newfound love for Python's `yield from`. [I went through a number of variations](https://www.youtube.com/watch?v=C7o5kWrbJJE&t=205s), including yielding decoded values if complete, else yielding `None`, and sending more bytes to the decoder with Python's `.send()` method of generators. I ended up managing to simplify the code down using `yield from`'s ability to receive a returned value, otherwise 'passing yields' through the (co)stack for us. I employed this to use `yield` and `.send()` solely for 'waking up' the generator. The code ends up very asyncio-ish, coroutine-like. [PEP 380](https://peps.python.org/pep-0380/) which added this behaviour was designed well!

I plan to make a separate '[GeneratorIO](https://github.com/jb2170/GeneratorIO/)' codebase for a generator-like asyncio. Reinventing the wheel I know, but in doing so I seek to learn the reason for some of asyncio's behaviour and naming conventions.
