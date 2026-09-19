"""Script to generate all UI icons and app.ico using Pillow."""
import math
from pathlib import Path
from PIL import Image, ImageDraw

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)


def draw_circle(draw, center, radius, fill=None, outline=None, width=1):
    cx, cy = center
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill, outline=outline, width=width)


def create_app_icon():
    # 256x256 app icon: stylized camera/canvas with transparent checkerboard cutout and wand
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Base rounded rect in modern indigo/cyan gradient background
    margin = 16
    draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=48, fill=(28, 32, 48, 255), outline=(70, 85, 130, 255), width=4)

    # Checkerboard inside a rounded container
    inner_box = [48, 48, 208, 208]
    draw.rounded_rectangle(inner_box, radius=24, fill=(40, 44, 60, 255))
    
    # Draw checkerboard pattern inside inner box
    cb_size = 20
    for y in range(54, 202, cb_size):
        for x in range(54, 202, cb_size):
            if ((x // cb_size) + (y // cb_size)) % 2 == 0:
                draw.rectangle([x, y, min(x + cb_size, 202), min(y + cb_size, 202)], fill=(75, 80, 105, 255))
            else:
                draw.rectangle([x, y, min(x + cb_size, 202), min(y + cb_size, 202)], fill=(120, 125, 155, 255))

    # Wand / Dropper diagonal across
    # Wand body
    draw.line([(70, 186), (160, 96)], fill=(230, 235, 255, 255), width=10)
    # Wand tip glowing cyan
    draw.ellipse([58, 174, 82, 198], fill=(0, 210, 255, 255), outline=(255, 255, 255, 255), width=3)
    # Magic sparkle stars
    sparkles = [(175, 75), (195, 105), (145, 55), (180, 125)]
    for sx, sy in sparkles:
        draw.line([(sx - 8, sy), (sx + 8, sy)], fill=(255, 220, 100, 255), width=3)
        draw.line([(sx, sy - 8), (sx, sy + 8)], fill=(255, 220, 100, 255), width=3)

    img.save(ICONS_DIR / "app.png", "PNG")
    
    # Generate app.ico with multiple resolutions
    img.save(ICONS_DIR / "app.ico", format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def create_eyedropper_icon():
    for sz in [24, 48]:
        scale = sz / 24.0
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Dropper pipette at 45 degree angle
        tip = (4 * scale, 20 * scale)
        p1 = (8 * scale, 16 * scale)
        p2 = (16 * scale, 8 * scale)
        bulb = (19 * scale, 5 * scale)
        
        # Bulb
        draw_circle(draw, bulb, 3.5 * scale, fill=(90, 180, 255, 255), outline=(240, 240, 255, 255), width=int(1.5 * scale))
        # Body
        draw.line([(7 * scale, 17 * scale), (16 * scale, 8 * scale)], fill=(220, 230, 250, 255), width=int(3 * scale))
        # Tip point
        draw.line([tip, (8 * scale, 16 * scale)], fill=(0, 210, 255, 255), width=int(2 * scale))
        # Drop at tip
        draw.point(tip, fill=(0, 230, 255, 255))
        
        filename = f"eyedropper_{sz}.png" if sz != 24 else "eyedropper.png"
        img.save(ICONS_DIR / filename, "PNG")


def create_brush_icon():
    for sz in [24, 48]:
        scale = sz / 24.0
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Paint brush angled
        # Handle
        draw.line([(18 * scale, 4 * scale), (10 * scale, 14 * scale)], fill=(180, 140, 90, 255), width=int(3.5 * scale))
        # Ferrule
        draw.line([(10 * scale, 14 * scale), (8 * scale, 16 * scale)], fill=(200, 200, 210, 255), width=int(4 * scale))
        # Bristles & tip
        draw.polygon([(8 * scale, 16 * scale), (4 * scale, 20 * scale), (7 * scale, 20 * scale)], fill=(0, 200, 240, 255))
        
        filename = f"brush_{sz}.png" if sz != 24 else "brush.png"
        img.save(ICONS_DIR / filename, "PNG")


def create_eraser_icon():
    for sz in [24, 48]:
        scale = sz / 24.0
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Angled rectangle for eraser
        pts = [
            (6 * scale, 18 * scale),
            (14 * scale, 21 * scale),
            (20 * scale, 8 * scale),
            (12 * scale, 5 * scale),
        ]
        draw.polygon(pts, fill=(240, 110, 140, 255), outline=(255, 220, 230, 255))
        # Eraser sleeve
        sleeve_pts = [
            (10 * scale, 11.5 * scale),
            (17 * scale, 14.5 * scale),
            (20 * scale, 8 * scale),
            (12 * scale, 5 * scale),
        ]
        draw.polygon(sleeve_pts, fill=(90, 130, 220, 255), outline=(220, 240, 255, 255))
        
        filename = f"eraser_{sz}.png" if sz != 24 else "eraser.png"
        img.save(ICONS_DIR / filename, "PNG")


def create_pan_icon():
    for sz in [24, 48]:
        scale = sz / 24.0
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Open hand / pan icon
        # Palm and fingers simplified clean geometric icon
        draw.rounded_rectangle([7 * scale, 9 * scale, 17 * scale, 19 * scale], radius=int(3 * scale), fill=(230, 235, 245, 255))
        # Fingers
        fingers_x = [8, 10.5, 13, 15.5]
        for fx in fingers_x:
            draw.rounded_rectangle([fx * scale, 4 * scale, (fx + 1.8) * scale, 11 * scale], radius=int(1 * scale), fill=(230, 235, 245, 255))
        # Thumb
        draw.polygon([(7 * scale, 12 * scale), (3 * scale, 14 * scale), (5 * scale, 17 * scale), (8 * scale, 16 * scale)], fill=(230, 235, 245, 255))

        filename = f"pan_{sz}.png" if sz != 24 else "pan.png"
        img.save(ICONS_DIR / filename, "PNG")


def create_utility_icons():
    sz = 24
    # Zoom in (+)
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_circle(draw, (10, 10), 6, outline=(220, 225, 240, 255), width=2)
    draw.line([(14, 14), (20, 20)], fill=(220, 225, 240, 255), width=2)
    draw.line([(7, 10), (13, 10)], fill=(220, 225, 240, 255), width=2)
    draw.line([(10, 7), (10, 13)], fill=(220, 225, 240, 255), width=2)
    img.save(ICONS_DIR / "zoom_in.png", "PNG")

    # Zoom out (-)
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_circle(draw, (10, 10), 6, outline=(220, 225, 240, 255), width=2)
    draw.line([(14, 14), (20, 20)], fill=(220, 225, 240, 255), width=2)
    draw.line([(7, 10), (13, 10)], fill=(220, 225, 240, 255), width=2)
    img.save(ICONS_DIR / "zoom_out.png", "PNG")

    # Fit to window
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 4, 20, 20], outline=(220, 225, 240, 255), width=2)
    # 4 inner corner triangles
    draw.polygon([(6, 6), (10, 6), (6, 10)], fill=(0, 210, 255, 255))
    draw.polygon([(18, 6), (14, 6), (18, 10)], fill=(0, 210, 255, 255))
    draw.polygon([(6, 18), (10, 18), (6, 14)], fill=(0, 210, 255, 255))
    draw.polygon([(18, 18), (14, 18), (18, 14)], fill=(0, 210, 255, 255))
    img.save(ICONS_DIR / "fit.png", "PNG")

    # 100% (1:1)
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([3, 4, 21, 20], outline=(180, 190, 210, 255), width=2)
    # text '1:1' lines
    draw.line([(7, 9), (7, 15)], fill=(0, 210, 255, 255), width=2)
    draw.point((12, 10), fill=(255, 255, 255, 255))
    draw.point((12, 14), fill=(255, 255, 255, 255))
    draw.line([(17, 9), (17, 15)], fill=(0, 210, 255, 255), width=2)
    img.save(ICONS_DIR / "actual_size.png", "PNG")

    # Overlay / highlight
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 4, 20, 20], outline=(220, 225, 240, 255), width=2)
    draw.rectangle([7, 7, 17, 17], fill=(255, 70, 70, 200))
    img.save(ICONS_DIR / "overlay.png", "PNG")

    # Settings gear
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = (12, 12)
    draw_circle(draw, center, 7, outline=(220, 225, 240, 255), width=2)
    draw_circle(draw, center, 3, fill=(220, 225, 240, 255))
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = center[0] + 6 * math.cos(rad)
        y1 = center[1] + 6 * math.sin(rad)
        x2 = center[0] + 9 * math.cos(rad)
        y2 = center[1] + 9 * math.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill=(220, 225, 240, 255), width=2)
    img.save(ICONS_DIR / "settings.png", "PNG")

    # Undo
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.arc([5, 6, 19, 18], start=180, end=360, fill=(220, 225, 240, 255), width=2)
    draw.polygon([(4, 12), (9, 7), (9, 17)], fill=(220, 225, 240, 255))
    img.save(ICONS_DIR / "undo.png", "PNG")

    # Redo
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.arc([5, 6, 19, 18], start=180, end=360, fill=(220, 225, 240, 255), width=2)
    draw.polygon([(20, 12), (15, 7), (15, 17)], fill=(220, 225, 240, 255))
    img.save(ICONS_DIR / "redo.png", "PNG")


if __name__ == "__main__":
    create_app_icon()
    create_eyedropper_icon()
    create_brush_icon()
    create_eraser_icon()
    create_pan_icon()
    create_utility_icons()
    print("All icons successfully generated in", ICONS_DIR)
