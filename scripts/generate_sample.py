"""Generate a sample image with a solid colorful background and clean foreground graphics."""
from pathlib import Path
from PIL import Image, ImageDraw

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "assets" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

size = (400, 400)
img = Image.new("RGB", size, (30, 144, 255))  # DodgerBlue background
draw = ImageDraw.Draw(img)

# White badge with drop shadow
draw.rounded_rectangle([70, 70, 330, 330], radius=40, fill=(255, 255, 255))
# Inner colorful star/shield
draw.ellipse([110, 110, 290, 290], fill=(255, 107, 107))
draw.polygon([(200, 130), (220, 185), (280, 185), (230, 220), (250, 275), (200, 240), (150, 275), (170, 220), (120, 185), (180, 185)], fill=(255, 217, 61))

img.save(SAMPLES_DIR / "sample_badge.jpg", "JPEG", quality=95)
img.save(SAMPLES_DIR / "sample_badge.png", "PNG")
print("Generated sample badge in", SAMPLES_DIR)
