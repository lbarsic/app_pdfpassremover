"""Generate assets/app.ico and assets/app.png — blue tile + white padlock."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
BLUE = (37, 99, 235, 255)
WHITE = (255, 255, 255, 255)


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = max(1, round(size * 0.06))
    radius = max(2, round((size - 2 * m) * 0.24))
    d.rounded_rectangle([m, m, size - 1 - m, size - 1 - m], radius=radius, fill=BLUE)

    cx = (size - 1) / 2.0
    inner = size - 2 * m
    bw = inner * 0.44
    bh = inner * 0.36
    body_top = m + inner * 0.50
    body = [cx - bw / 2, body_top, cx + bw / 2, body_top + bh]
    br = max(1, round(size * 0.08))
    stroke = max(2, round(size * 0.09))
    sw_outer = bw * 0.70
    sh_outer = inner * 0.46
    ox0, ox1 = cx - sw_outer / 2, cx + sw_outer / 2
    oy1 = body_top + bh * 0.22
    oy0 = body_top - sh_outer + stroke * 0.35

    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    outer_r = (ox1 - ox0) / 2.0
    md.rounded_rectangle([ox0, oy0, ox1, oy1], radius=outer_r, fill=255)
    md.rounded_rectangle(
        [ox0 + stroke, oy0 + stroke, ox1 - stroke, oy1 - stroke],
        radius=max(0.5, outer_r - stroke),
        fill=0,
    )
    md.rectangle([0, body_top + max(2, stroke * 0.4), size, size], fill=0)
    img.paste(Image.new("RGBA", (size, size), WHITE), (0, 0), mask)
    d.rounded_rectangle(body, radius=br, fill=WHITE)

    if size >= 20:
        kx, ky = cx, body_top + bh * 0.40
        kr = max(1.2, size * 0.048)
        d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=BLUE)
        slot_w = max(1.2, size * 0.038)
        slot_h = max(2, bh * 0.30)
        d.polygon(
            [
                (kx - slot_w / 2, ky),
                (kx + slot_w / 2, ky),
                (kx + slot_w * 0.35, ky + slot_h),
                (kx - slot_w * 0.35, ky + slot_h),
            ],
            fill=BLUE,
        )
    return img


def aa_render(size: int) -> Image.Image:
    if size <= 16:
        return render(size)
    return render(size * 4).resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    images = [aa_render(s) for s in sizes]
    images[sizes.index(256)].save(OUT / "app.png")
    images[-1].save(
        OUT / "app.ico",
        format="ICO",
        sizes=[(im.width, im.height) for im in images],
        append_images=images[:-1],
    )
    print("wrote", OUT / "app.ico")
    print("wrote", OUT / "app.png")


if __name__ == "__main__":
    main()
