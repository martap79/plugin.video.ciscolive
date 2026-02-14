#!/usr/bin/env python3
"""
Generate icon.png and fanart.jpg for the Cisco Live Kodi plugin.
Professional, dark theme with Cisco-inspired teal/blue accents.
"""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "resources/media"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Color palette - Cisco-inspired
CISCO_BLUE = (0, 147, 202)      # #0093CA
CISCO_TEAL = (0, 188, 212)      # #00BCD4
DARK_BG = (18, 18, 24)          # #121218
DARKER_BG = (12, 12, 16)        # #0C0C10
ACCENT_LIGHT = (100, 220, 255)  # Light blue accent
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 180, 190)


def create_icon():
    """Create 256x256 icon.png"""
    size = 256
    img = Image.new('RGB', (size, size), DARK_BG)
    draw = ImageDraw.Draw(img)
    
    # Draw a play button-style icon with modern gradient effect
    # Outer rounded square border
    margin = 20
    border_width = 3
    
    # Draw rounded rectangle background
    draw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=30,
        fill=DARKER_BG,
        outline=CISCO_TEAL,
        width=border_width
    )
    
    # Draw a stylized play triangle in the center
    center_x, center_y = size // 2, size // 2
    play_size = 70
    
    # Triangle points (play button pointing right)
    triangle = [
        (center_x - play_size//2, center_y - play_size),
        (center_x - play_size//2, center_y + play_size),
        (center_x + play_size, center_y)
    ]
    
    draw.polygon(triangle, fill=CISCO_BLUE)
    
    # Add a small highlight effect on the triangle
    highlight_triangle = [
        (center_x - play_size//2 + 8, center_y - play_size + 15),
        (center_x - play_size//2 + 8, center_y - play_size//3),
        (center_x + play_size//2, center_y - play_size//2)
    ]
    draw.polygon(highlight_triangle, fill=ACCENT_LIGHT)
    
    # Add signal wave bars on the left side (representing "Live" broadcast)
    bar_x = margin + 30
    bar_heights = [30, 45, 60, 50, 35]
    bar_width = 6
    bar_spacing = 10
    
    for i, h in enumerate(bar_heights):
        x = bar_x + i * (bar_width + bar_spacing)
        y_top = center_y - h // 2
        y_bottom = center_y + h // 2
        
        # Create gradient effect by alpha
        color = CISCO_TEAL if i % 2 == 0 else CISCO_BLUE
        draw.rounded_rectangle(
            [(x, y_top), (x + bar_width, y_bottom)],
            radius=3,
            fill=color
        )
    
    img.save(os.path.join(OUTPUT_DIR, "icon.png"), "PNG", optimize=True)
    print(f"✓ Created icon.png (256x256)")


def create_fanart():
    """Create 1920x1080 fanart.jpg"""
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height), DARKER_BG)
    draw = ImageDraw.Draw(img)
    
    # Create a modern gradient background
    for y in range(height):
        # Gradient from dark blue at top to darker at bottom
        ratio = y / height
        r = int(DARKER_BG[0] + (DARK_BG[0] - DARKER_BG[0]) * (1 - ratio))
        g = int(DARKER_BG[1] + (DARK_BG[1] - DARKER_BG[1]) * (1 - ratio))
        b = int(DARKER_BG[2] + (DARK_BG[2] - DARKER_BG[2]) * (1 - ratio))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw abstract geometric design
    # Large circles (like conference bubbles/sessions)
    circles = [
        (300, 200, 180, CISCO_BLUE, 0.15),
        (1600, 300, 220, CISCO_TEAL, 0.12),
        (500, 800, 160, ACCENT_LIGHT, 0.1),
        (1400, 850, 200, CISCO_BLUE, 0.13),
    ]
    
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    for x, y, radius, color, opacity in circles:
        alpha = int(255 * opacity)
        overlay_draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=color + (alpha,)
        )
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Draw network connection lines between circles
    line_color = CISCO_TEAL + (80,)
    overlay2 = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw2 = ImageDraw.Draw(overlay2)
    
    connections = [
        (circles[0][:2], circles[1][:2]),
        (circles[1][:2], circles[3][:2]),
        (circles[0][:2], circles[2][:2]),
    ]
    
    for (x1, y1), (x2, y2) in connections:
        overlay_draw2.line([(x1, y1), (x2, y2)], fill=line_color, width=2)
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay2).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Add central focus with play icon
    center_x, center_y = width // 2, height // 2 - 50
    
    # Large semi-transparent circle behind play button
    circle_radius = 150
    overlay3 = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw3 = ImageDraw.Draw(overlay3)
    overlay_draw3.ellipse(
        [(center_x - circle_radius, center_y - circle_radius),
         (center_x + circle_radius, center_y + circle_radius)],
        fill=DARK_BG + (120,)
    )
    img = Image.alpha_composite(img.convert('RGBA'), overlay3).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Large play button
    play_size = 100
    triangle = [
        (center_x - play_size//2, center_y - play_size),
        (center_x - play_size//2, center_y + play_size),
        (center_x + play_size + 20, center_y)
    ]
    draw.polygon(triangle, fill=CISCO_TEAL)
    
    # Try to add text (Cisco Live)
    try:
        # Try to use a system font, fall back to default if not available
        font_size = 72
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            except:
                font = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # "CISCO LIVE" text
        text1 = "CISCO LIVE"
        text2 = "ON-DEMAND"
        
        # Get text bounding boxes
        bbox1 = draw.textbbox((0, 0), text1, font=font)
        bbox2 = draw.textbbox((0, 0), text2, font=font_small)
        
        text1_width = bbox1[2] - bbox1[0]
        text2_width = bbox2[2] - bbox2[0]
        
        text1_x = (width - text1_width) // 2
        text1_y = height - 250
        
        text2_x = (width - text2_width) // 2
        text2_y = text1_y + 85
        
        # Draw text with subtle shadow
        shadow_offset = 3
        draw.text((text1_x + shadow_offset, text1_y + shadow_offset), text1, 
                  fill=(0, 0, 0, 180), font=font)
        draw.text((text1_x, text1_y), text1, fill=TEXT_WHITE, font=font)
        
        draw.text((text2_x + shadow_offset, text2_y + shadow_offset), text2,
                  fill=(0, 0, 0, 180), font=font_small)
        draw.text((text2_x, text2_y), text2, fill=CISCO_TEAL, font=font_small)
        
    except Exception as e:
        print(f"Note: Could not add text to fanart: {e}")
    
    img.save(os.path.join(OUTPUT_DIR, "fanart.jpg"), "JPEG", quality=95, optimize=True)
    print(f"✓ Created fanart.jpg (1920x1080)")


if __name__ == "__main__":
    create_icon()
    create_fanart()
    print("\n✓ All assets created successfully!")
    print(f"  - {OUTPUT_DIR}/icon.png")
    print(f"  - {OUTPUT_DIR}/fanart.jpg")
