"""Generate the M2CIDSmile app icon — blue rounded square with 'M2' text."""
from PIL import Image, ImageDraw, ImageFont
import os

SIZES = [16, 24, 32, 48, 64, 128, 256]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")


def draw_icon(size):
    """Draw one icon frame at the given pixel size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Blue rounded-square background (#6366f1 = indigo-500)
    margin = max(1, size // 16)
    radius = max(2, size // 4)
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=radius,
        fill=(99, 102, 241, 255),  # #6366f1
    )

    # White "M2" text centered
    font_size = int(size * 0.42)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    text = "M2"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    return img


def main():
    frames = [draw_icon(s) for s in SIZES]
    frames[0].save(OUT, format="ICO", sizes=[(s, s) for s in SIZES],
                   append_images=frames[1:])
    print(f"Icon saved: {OUT}  ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()
