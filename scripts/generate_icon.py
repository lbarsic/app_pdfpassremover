"""Build assets/app.ico from the CustomTkinter window icon.

Windows Explorer ignores PNG-compressed icons under 256px inside a PE
file, which is why a 256-only .ico shows up as the generic Python icon.
Small sizes are stored as 32-bit BMP; 256px stays PNG.
"""
from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "icon_source.png"
OUT = ASSETS / "app.ico"
SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def _and_mask(width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    """1-bpp AND mask, rows padded to 32 bits, bottom-up. 1 = transparent."""
    row_bytes = ((width + 31) // 32) * 4
    out = bytearray()
    for y in range(height - 1, -1, -1):
        bits = 0
        nbits = 0
        row = bytearray(row_bytes)
        col = 0
        bitpos = 0
        for x in range(width):
            a = pixels[y * width + x][3]
            if a == 0:
                row[col] |= 0x80 >> bitpos
            bitpos += 1
            if bitpos == 8:
                bitpos = 0
                col += 1
        out.extend(row)
    return bytes(out)


def _pixels(im: Image.Image) -> list[tuple[int, int, int, int]]:
    im = im.convert("RGBA")
    raw = im.tobytes()
    out = []
    for i in range(0, len(raw), 4):
        out.append((raw[i], raw[i + 1], raw[i + 2], raw[i + 3]))
    return out


def _dib_icon(im: Image.Image) -> bytes:
    im = im.convert("RGBA")
    w, h = im.size
    pixels = _pixels(im)
    xor = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = pixels[y * w + x]
            xor.extend((b, g, r, a))
    mask = _and_mask(w, h, pixels)
    header = struct.pack(
        "<IiiHHIIiiII",
        40,          # biSize
        w,
        h * 2,       # XOR + AND
        1,           # planes
        32,          # bitcount
        0,           # BI_RGB
        len(xor) + len(mask),
        0, 0, 0, 0,
    )
    return header + xor + mask


def _png_icon(im: Image.Image) -> bytes:
    buf = BytesIO()
    im.convert("RGBA").save(buf, format="PNG")
    return buf.getvalue()


def write_ico(images: list[Image.Image], dest: Path) -> None:
    blobs: list[bytes] = []
    for im in images:
        if im.size[0] >= 256:
            blobs.append(_png_icon(im))
        else:
            blobs.append(_dib_icon(im))

    count = len(images)
    offset = 6 + 16 * count
    entries = bytearray()
    for im, blob in zip(images, blobs):
        w, h = im.size
        entries += struct.pack(
            "<BBBBHHII",
            w if w < 256 else 0,
            h if h < 256 else 0,
            0,
            0,
            1,
            32,
            len(blob),
            offset,
        )
        offset += len(blob)

    dest.write_bytes(b"".join((struct.pack("<HHH", 0, 1, count), entries, *blobs)))


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    src = Image.open(SOURCE).convert("RGBA")
    images = [src.resize((s, s), Image.Resampling.LANCZOS) for s in SIZES]
    write_ico(images, OUT)
    print("wrote", OUT, OUT.stat().st_size, "bytes", "sizes", list(SIZES))


if __name__ == "__main__":
    main()
