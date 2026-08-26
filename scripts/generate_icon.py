"""Build assets/app.ico: SnipCap-style C-frame with a crossed lock in the hole.

Windows Explorer ignores PNG-compressed icons under 256px inside a PE
file. Small sizes are stored as 32-bit BMP; 256px stays PNG.
"""
from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "icon_source.png"
OUT = ASSETS / "app.ico"
FRAME = ASSETS / "c_frame.png"
SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)

CYAN = (2, 156, 255, 255)
NAVY = (15, 23, 42, 255)
RED = (239, 68, 68, 255)


def _and_mask(width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    """1-bpp AND mask, rows padded to 32 bits, bottom-up. 1 = transparent."""
    row_bytes = ((width + 31) // 32) * 4
    out = bytearray()
    for y in range(height - 1, -1, -1):
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
        40, w, h * 2, 1, 32, 0, len(xor) + len(mask), 0, 0, 0, 0,
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
            0, 0, 1, 32, len(blob), offset,
        )
        offset += len(blob)

    dest.write_bytes(b"".join((struct.pack("<HHH", 0, 1, count), entries, *blobs)))


def _r(size: int, v: float) -> int:
    return int(round(v * size / 512.0))


def _hole_mask(frame: Image.Image) -> Image.Image:
    """Opaque mask of the C's inner hole (flood-fill from the center)."""
    px = frame.load()
    w, h = frame.size
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    stack = [(w // 2, h // 2)]
    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or x < 0 or y < 0 or x >= w or y >= h:
            continue
        seen.add((x, y))
        if px[x, y][3] > 32:
            continue
        mp[x, y] = 255
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return mask


def _draw_line(d: ImageDraw.ImageDraw, a, b, width: int, fill) -> None:
    d.line([a, b], fill=fill, width=width)
    r = max(1, width // 2)
    d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=fill)
    d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=fill)


def _draw_crossed_lock(im: Image.Image) -> None:
    """Chunky padlock with a red slash, same visual weight as SnipCap's camera."""
    d = ImageDraw.Draw(im)
    s = im.size[0]

    def p(v):
        return _r(s, v)

    body = [p(190), p(258), p(322), p(368)]
    d.rounded_rectangle(body, radius=p(26), fill=CYAN)

    stroke = p(26)
    ox0, ox1 = p(214), p(298)
    oy0, oy1 = p(172), p(292)
    mask = Image.new("L", (s, s), 0)
    md = ImageDraw.Draw(mask)
    outer_r = (ox1 - ox0) / 2.0
    md.rounded_rectangle([ox0, oy0, ox1, oy1], radius=outer_r, fill=255)
    md.rounded_rectangle(
        [ox0 + stroke, oy0 + stroke, ox1 - stroke, oy1 - stroke],
        radius=max(1, outer_r - stroke),
        fill=0,
    )
    md.rectangle([0, p(268), s, s], fill=0)
    im.paste(Image.new("RGBA", (s, s), CYAN), (0, 0), mask)
    d.rounded_rectangle(body, radius=p(26), fill=CYAN)

    kx, ky = p(256), p(300)
    kr = p(16)
    d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=NAVY)
    slot_w, slot_h = p(12), p(28)
    d.polygon(
        [
            (kx - slot_w / 2, ky),
            (kx + slot_w / 2, ky),
            (kx + slot_w * 0.35, ky + slot_h),
            (kx - slot_w * 0.35, ky + slot_h),
        ],
        fill=NAVY,
    )

    a, b = (p(168), p(188),), (p(344), p(372),)
    _draw_line(d, a, b, p(34), NAVY)
    _draw_line(d, a, b, p(22), RED)


def draw_logo(size: int = 512) -> Image.Image:
    frame = Image.open(FRAME).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    hole = _hole_mask(frame)
    plate = Image.new("RGBA", (size, size), NAVY)
    plate.putalpha(hole)
    lock = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    _draw_crossed_lock(lock)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(plate)
    canvas.alpha_composite(lock)
    canvas.alpha_composite(frame)
    return canvas


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    src = draw_logo(512)
    src.save(SOURCE)
    images = [src.resize((s, s), Image.Resampling.LANCZOS) for s in SIZES]
    write_ico(images, OUT)
    print("wrote", SOURCE)
    print("wrote", OUT, OUT.stat().st_size, "bytes", "sizes", list(SIZES))


if __name__ == "__main__":
    main()
