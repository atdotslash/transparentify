from pathlib import Path
from PIL import Image, ImageDraw

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

sz = 24
img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Info circle 'i'
center = (12, 12)
draw.ellipse([3, 3, 21, 21], outline=(220, 225, 240, 255), width=2)
# dot of 'i'
draw.ellipse([10.5, 6.5, 13.5, 9.5], fill=(0, 210, 255, 255))
# stem of 'i'
draw.line([(12, 11), (12, 17)], fill=(220, 225, 240, 255), width=2)
# bottom serif
draw.line([(10.5, 17), (13.5, 17)], fill=(220, 225, 240, 255), width=2)

img.save(ICONS_DIR / "info.png", "PNG")
print("Generated info.png in", ICONS_DIR)
