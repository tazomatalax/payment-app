#!/usr/bin/env python3
"""Small no-dependency QR SVG generator for short text payloads.

This implementation supports byte-mode QR codes using error correction level L.
That is enough for a hosted page URL and a compact plain-text backup payload.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionInfo:
    version: int
    data_codewords: int
    ecc_codewords_per_block: int
    group_1_blocks: int
    group_1_data_codewords: int
    group_2_blocks: int
    group_2_data_codewords: int
    alignment_positions: tuple[int, ...]


VERSION_INFO = {
    1: VersionInfo(1, 19, 7, 1, 19, 0, 0, ()),
    2: VersionInfo(2, 34, 10, 1, 34, 0, 0, (6, 18)),
    3: VersionInfo(3, 55, 15, 1, 55, 0, 0, (6, 22)),
    4: VersionInfo(4, 80, 20, 1, 80, 0, 0, (6, 26)),
    5: VersionInfo(5, 108, 26, 1, 108, 0, 0, (6, 30)),
    6: VersionInfo(6, 136, 18, 2, 68, 0, 0, (6, 34)),
    7: VersionInfo(7, 156, 20, 2, 78, 0, 0, (6, 22, 38)),
    8: VersionInfo(8, 194, 24, 2, 97, 0, 0, (6, 24, 42)),
    9: VersionInfo(9, 232, 30, 2, 116, 0, 0, (6, 26, 46)),
    10: VersionInfo(10, 274, 18, 2, 68, 2, 69, (6, 28, 50)),
    11: VersionInfo(11, 324, 20, 4, 81, 0, 0, (6, 30, 54)),
    12: VersionInfo(12, 370, 24, 2, 92, 2, 93, (6, 32, 58)),
    13: VersionInfo(13, 428, 26, 4, 107, 0, 0, (6, 34, 62)),
    14: VersionInfo(14, 461, 30, 3, 115, 1, 116, (6, 26, 46, 66)),
    15: VersionInfo(15, 523, 22, 5, 87, 1, 88, (6, 26, 48, 70)),
    16: VersionInfo(16, 589, 24, 5, 98, 1, 99, (6, 26, 50, 74)),
    17: VersionInfo(17, 647, 28, 1, 107, 5, 108, (6, 30, 54, 78)),
    18: VersionInfo(18, 721, 30, 5, 120, 1, 121, (6, 30, 56, 82)),
    19: VersionInfo(19, 795, 28, 3, 113, 4, 114, (6, 30, 58, 86)),
    20: VersionInfo(20, 861, 28, 3, 107, 5, 108, (6, 34, 62, 90)),
    21: VersionInfo(21, 932, 28, 4, 116, 4, 117, (6, 28, 50, 72, 94)),
    22: VersionInfo(22, 1006, 28, 2, 111, 7, 112, (6, 26, 50, 74, 98)),
    23: VersionInfo(23, 1094, 30, 4, 121, 5, 122, (6, 30, 54, 78, 102)),
    24: VersionInfo(24, 1174, 30, 6, 117, 4, 118, (6, 28, 54, 80, 106)),
    25: VersionInfo(25, 1276, 26, 8, 106, 4, 107, (6, 32, 58, 84, 110)),
    26: VersionInfo(26, 1370, 28, 10, 114, 2, 115, (6, 30, 58, 86, 114)),
    27: VersionInfo(27, 1468, 30, 8, 122, 4, 123, (6, 34, 62, 90, 118)),
    28: VersionInfo(28, 1531, 30, 3, 117, 10, 118, (6, 26, 50, 74, 98, 122)),
    29: VersionInfo(29, 1631, 30, 7, 116, 7, 117, (6, 30, 54, 78, 102, 126)),
    30: VersionInfo(30, 1735, 30, 5, 115, 10, 116, (6, 26, 52, 78, 104, 130)),
    31: VersionInfo(31, 1843, 30, 13, 115, 3, 116, (6, 30, 56, 82, 108, 134)),
    32: VersionInfo(32, 1955, 30, 17, 115, 0, 0, (6, 34, 60, 86, 112, 138)),
    33: VersionInfo(33, 2071, 30, 17, 115, 1, 116, (6, 30, 58, 86, 114, 142)),
    34: VersionInfo(34, 2191, 30, 13, 115, 6, 116, (6, 34, 62, 90, 118, 146)),
    35: VersionInfo(35, 2306, 30, 12, 121, 7, 122, (6, 30, 54, 78, 102, 126, 150)),
    36: VersionInfo(36, 2434, 30, 6, 121, 14, 122, (6, 24, 50, 76, 102, 128, 154)),
    37: VersionInfo(37, 2566, 30, 17, 122, 4, 123, (6, 28, 54, 80, 106, 132, 158)),
    38: VersionInfo(38, 2702, 30, 4, 122, 18, 123, (6, 32, 58, 84, 110, 136, 162)),
    39: VersionInfo(39, 2812, 30, 20, 117, 4, 118, (6, 26, 54, 82, 110, 138, 166)),
    40: VersionInfo(40, 2956, 30, 19, 118, 6, 119, (6, 30, 58, 86, 114, 142, 170)),
}

ECC_LEVEL_BITS = 0b01


def make_gf_tables() -> tuple[list[int], list[int]]:
    exp = [0] * 512
    log = [0] * 256
    value = 1
    for i in range(255):
        exp[i] = value
        log[value] = i
        value <<= 1
        if value & 0x100:
            value ^= 0x11D
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log


GF_EXP, GF_LOG = make_gf_tables()


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]


def rs_generator(degree: int) -> list[int]:
    poly = [1]
    for i in range(degree):
        next_poly = [0] * (len(poly) + 1)
        for j, coefficient in enumerate(poly):
            next_poly[j] ^= coefficient
            next_poly[j + 1] ^= gf_mul(coefficient, GF_EXP[i])
        poly = next_poly
    return poly


class BitBuffer:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def append(self, value: int, length: int) -> None:
        for i in range(length - 1, -1, -1):
            self.bits.append((value >> i) & 1)

    def to_codewords(self) -> list[int]:
        return [sum(self.bits[i + j] << (7 - j) for j in range(8)) for i in range(0, len(self.bits), 8)]


def size_for(version: int) -> int:
    return version * 4 + 17


def choose_version(payload: bytes) -> VersionInfo:
    for version in range(1, 41):
        info = VERSION_INFO[version]
        count_bits = 8 if version <= 9 else 16
        if 4 + count_bits + len(payload) * 8 <= info.data_codewords * 8:
            return info
    raise ValueError("Payload is too large for version 40-L QR encoding.")


def make_data_codewords(payload: bytes, info: VersionInfo) -> list[int]:
    buffer = BitBuffer()
    buffer.append(0b0100, 4)
    buffer.append(len(payload), 8 if info.version <= 9 else 16)
    for byte in payload:
        buffer.append(byte, 8)

    remaining = info.data_codewords * 8 - len(buffer.bits)
    buffer.append(0, min(4, remaining))
    while len(buffer.bits) % 8:
        buffer.append(0, 1)

    codewords = buffer.to_codewords()
    pad = [0xEC, 0x11]
    while len(codewords) < info.data_codewords:
        codewords.append(pad[len(codewords) % 2])
    return codewords


def rs_ecc(data: list[int], degree: int) -> list[int]:
    generator = rs_generator(degree)
    result = [0] * degree
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        for i, coefficient in enumerate(generator[1:]):
            result[i] ^= gf_mul(coefficient, factor)
    return result


def make_blocks(data_codewords: list[int], info: VersionInfo) -> tuple[list[list[int]], list[list[int]]]:
    blocks: list[list[int]] = []
    offset = 0
    for _ in range(info.group_1_blocks):
        blocks.append(data_codewords[offset : offset + info.group_1_data_codewords])
        offset += info.group_1_data_codewords
    for _ in range(info.group_2_blocks):
        blocks.append(data_codewords[offset : offset + info.group_2_data_codewords])
        offset += info.group_2_data_codewords
    ecc_blocks = [rs_ecc(block, info.ecc_codewords_per_block) for block in blocks]
    return blocks, ecc_blocks


def interleave(blocks: list[list[int]], ecc_blocks: list[list[int]], ecc_codewords_per_block: int) -> list[int]:
    result: list[int] = []
    max_data_len = max(len(block) for block in blocks)
    for i in range(max_data_len):
        for block in blocks:
            if i < len(block):
                result.append(block[i])
    for i in range(ecc_codewords_per_block):
        for block in ecc_blocks:
            result.append(block[i])
    return result


def bch_remainder(value: int, polynomial: int) -> int:
    while value.bit_length() >= polynomial.bit_length():
        value ^= polynomial << (value.bit_length() - polynomial.bit_length())
    return value


def format_bits(mask: int) -> int:
    data = (ECC_LEVEL_BITS << 3) | mask
    return ((data << 10) | bch_remainder(data << 10, 0x537)) ^ 0x5412


def version_bits(version: int) -> int:
    return (version << 12) | bch_remainder(version << 12, 0x1F25)


def empty_matrix(size: int) -> tuple[list[list[bool]], list[list[bool]]]:
    modules = [[False] * size for _ in range(size)]
    function = [[False] * size for _ in range(size)]
    return modules, function


def set_module(modules: list[list[bool]], function: list[list[bool]], row: int, col: int, dark: bool, is_function: bool = True) -> None:
    size = len(modules)
    if 0 <= row < size and 0 <= col < size:
        modules[row][col] = dark
        if is_function:
            function[row][col] = True


def place_finder(modules: list[list[bool]], function: list[list[bool]], row: int, col: int) -> None:
    size = len(modules)
    for r in range(row - 1, row + 8):
        for c in range(col - 1, col + 8):
            if 0 <= r < size and 0 <= c < size:
                is_inside = row <= r < row + 7 and col <= c < col + 7
                if not is_inside:
                    set_module(modules, function, r, c, False)
    for r in range(7):
        for c in range(7):
            dark = r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4)
            set_module(modules, function, row + r, col + c, dark)


def place_alignment(modules: list[list[bool]], function: list[list[bool]], center_row: int, center_col: int) -> None:
    if function[center_row][center_col]:
        return
    for r in range(-2, 3):
        for c in range(-2, 3):
            dark = max(abs(r), abs(c)) != 1
            set_module(modules, function, center_row + r, center_col + c, dark)


def place_function_patterns(modules: list[list[bool]], function: list[list[bool]], info: VersionInfo) -> None:
    size = len(modules)
    place_finder(modules, function, 0, 0)
    place_finder(modules, function, 0, size - 7)
    place_finder(modules, function, size - 7, 0)

    for i in range(8, size - 8):
        dark = i % 2 == 0
        set_module(modules, function, 6, i, dark)
        set_module(modules, function, i, 6, dark)

    for row in info.alignment_positions:
        for col in info.alignment_positions:
            if (row <= 8 and col <= 8) or (row <= 8 and col >= size - 9) or (row >= size - 9 and col <= 8):
                continue
            place_alignment(modules, function, row, col)

    set_module(modules, function, 4 * info.version + 9, 8, True)

    for i in range(9):
        if i != 6:
            set_module(modules, function, 8, i, False)
            set_module(modules, function, i, 8, False)
    for i in range(8):
        set_module(modules, function, 8, size - 1 - i, False)
        set_module(modules, function, size - 1 - i, 8, False)

    if info.version >= 7:
        for r in range(6):
            for c in range(3):
                set_module(modules, function, r, size - 11 + c, False)
                set_module(modules, function, size - 11 + c, r, False)


def place_version_info(modules: list[list[bool]], version: int) -> None:
    if version < 7:
        return
    size = len(modules)
    bits = version_bits(version)
    for i in range(18):
        bit = ((bits >> i) & 1) == 1
        modules[i // 3][size - 11 + (i % 3)] = bit
        modules[size - 11 + (i % 3)][i // 3] = bit


def mask_condition(mask: int, row: int, col: int) -> bool:
    if mask == 0:
        return (row + col) % 2 == 0
    if mask == 1:
        return row % 2 == 0
    if mask == 2:
        return col % 3 == 0
    if mask == 3:
        return (row + col) % 3 == 0
    if mask == 4:
        return (row // 2 + col // 3) % 2 == 0
    if mask == 5:
        return ((row * col) % 2 + (row * col) % 3) == 0
    if mask == 6:
        return (((row * col) % 2 + (row * col) % 3) % 2) == 0
    if mask == 7:
        return (((row + col) % 2 + (row * col) % 3) % 2) == 0
    raise ValueError(mask)


def place_data(modules: list[list[bool]], function: list[list[bool]], codewords: list[int]) -> None:
    size = len(modules)
    bits = [(byte >> i) & 1 for byte in codewords for i in range(7, -1, -1)]
    index = 0
    upward = True
    col = size - 1
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for current_col in (col, col - 1):
                if not function[row][current_col]:
                    modules[row][current_col] = bool(bits[index]) if index < len(bits) else False
                    index += 1
        upward = not upward
        col -= 2


def apply_mask(source: list[list[bool]], function: list[list[bool]], mask: int) -> list[list[bool]]:
    size = len(source)
    result = [row[:] for row in source]
    for r in range(size):
        for c in range(size):
            if not function[r][c] and mask_condition(mask, r, c):
                result[r][c] = not result[r][c]
    return result


def place_format_info(modules: list[list[bool]], mask: int) -> None:
    size = len(modules)
    bits = format_bits(mask)
    for i in range(6):
        modules[8][i] = ((bits >> i) & 1) == 1
    modules[8][7] = ((bits >> 6) & 1) == 1
    modules[8][8] = ((bits >> 7) & 1) == 1
    modules[7][8] = ((bits >> 8) & 1) == 1
    for i in range(9, 15):
        modules[14 - i][8] = ((bits >> i) & 1) == 1

    for i in range(8):
        modules[size - 1 - i][8] = ((bits >> i) & 1) == 1
    for i in range(8, 15):
        modules[8][size - 15 + i] = ((bits >> i) & 1) == 1


def penalty(modules: list[list[bool]]) -> int:
    size = len(modules)
    score = 0

    for rows in (modules, list(map(list, zip(*modules)))):
        for row in rows:
            run_color = row[0]
            run_len = 1
            for value in row[1:]:
                if value == run_color:
                    run_len += 1
                else:
                    if run_len >= 5:
                        score += 3 + (run_len - 5)
                    run_color = value
                    run_len = 1
            if run_len >= 5:
                score += 3 + (run_len - 5)

    for r in range(size - 1):
        for c in range(size - 1):
            color = modules[r][c]
            if modules[r + 1][c] == color and modules[r][c + 1] == color and modules[r + 1][c + 1] == color:
                score += 3

    pattern = [True, False, True, True, True, False, True]
    for rows in (modules, list(map(list, zip(*modules)))):
        for row in rows:
            for i in range(size - 6):
                if row[i : i + 7] == pattern:
                    before = i >= 4 and not any(row[i - 4 : i])
                    after = i + 11 <= size and not any(row[i + 7 : i + 11])
                    if before or after:
                        score += 40

    dark = sum(1 for row in modules for value in row if value)
    total = size * size
    score += int(abs(dark * 100 / total - 50) // 5) * 10
    return score


def svg(modules: list[list[bool]], scale: int = 4, border: int = 4, label: str = "QR code") -> str:
    size = len(modules)
    dimension = (size + border * 2) * scale
    rects = []
    for r, row in enumerate(modules):
        for c, dark in enumerate(row):
            if dark:
                rects.append(f'<rect x="{(c + border) * scale}" y="{(r + border) * scale}" width="{scale}" height="{scale}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {dimension} {dimension}" width="{dimension}" height="{dimension}" role="img" aria-label="{label}">\n'
        f'<rect width="100%" height="100%" fill="#fff"/>\n'
        f'<g fill="#000">\n' + "\n".join(rects) + "\n</g>\n</svg>\n"
    )


def make_svg(payload_text: str, scale: int = 4, border: int = 4, label: str = "QR code") -> str:
    payload = payload_text.encode("utf-8")
    info = choose_version(payload)

    data_codewords = make_data_codewords(payload, info)
    blocks, ecc_blocks = make_blocks(data_codewords, info)
    codewords = interleave(blocks, ecc_blocks, info.ecc_codewords_per_block)

    size = size_for(info.version)
    modules, function = empty_matrix(size)
    place_function_patterns(modules, function, info)
    place_version_info(modules, info.version)
    place_data(modules, function, codewords)

    best_modules: list[list[bool]] | None = None
    best_score: int | None = None
    for mask in range(8):
        candidate = apply_mask(modules, function, mask)
        place_format_info(candidate, mask)
        current_score = penalty(candidate)
        if best_score is None or current_score < best_score:
            best_score = current_score
            best_modules = candidate

    assert best_modules is not None
    return svg(best_modules, scale=scale, border=border, label=label)
