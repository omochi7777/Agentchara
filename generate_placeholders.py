#!/usr/bin/env python3
"""
Generate placeholder GIF animations for avatar overlay testing.
Each state has a different color to make it easy to distinguish.
"""

from PIL import Image, ImageDraw, ImageFont
import os

ASSETS_DIR = "assets"
SIZE = 256
STATES = {
    "idle": ("#4A90A4", "😴"),      # Calm blue
    "thinking": ("#9B59B6", "🤔"),   # Purple
    "typing": ("#27AE60", "⌨️"),     # Green
    "running": ("#E67E22", "🏃"),    # Orange
    "success": ("#2ECC71", "✅"),    # Bright green
    "error": ("#E74C3C", "❌"),      # Red
}

def create_gif(name: str, color: str, emoji: str):
    """Create a simple animated GIF with pulsing effect."""
    frames = []
    
    for i in range(8):
        # Create frame with slight size variation for animation
        scale = 0.85 + 0.15 * (1 + (i / 8 * 3.14159 * 2).__import__('math').sin()) / 2
        
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw circle with pulsing effect
        margin = int((1 - scale) * SIZE / 2)
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        
        # Outer glow
        for offset in range(10, 0, -2):
            alpha = int(50 * (10 - offset) / 10)
            glow_color = (r, g, b, alpha)
            draw.ellipse(
                [margin - offset, margin - offset, SIZE - margin + offset, SIZE - margin + offset],
                fill=glow_color
            )
        
        # Main circle
        draw.ellipse(
            [margin, margin, SIZE - margin, SIZE - margin],
            fill=(r, g, b, 230)
        )
        
        # Draw state name
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        text = name.upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(
            ((SIZE - text_width) / 2, SIZE / 2 - text_height / 2),
            text,
            fill=(255, 255, 255, 255),
            font=font
        )
        
        frames.append(img)
    
    # Save as GIF
    output_path = os.path.join(ASSETS_DIR, f"{name}.gif")
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,  # 100ms per frame
        loop=0,
        disposal=2,
    )
    print(f"Created: {output_path}")

def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # Simpler approach - create frames manually
    import math
    
    for name, (color, emoji) in STATES.items():
        frames = []
        
        for i in range(8):
            scale = 0.85 + 0.15 * math.sin(i / 8 * math.pi * 2)
            
            img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            margin = int((1 - scale) * SIZE / 4)
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            
            # Outer glow
            for offset in range(15, 0, -3):
                alpha = int(40 * (15 - offset) / 15)
                draw.ellipse(
                    [margin - offset, margin - offset, SIZE - margin + offset, SIZE - margin + offset],
                    fill=(r, g, b, alpha)
                )
            
            # Main circle
            draw.ellipse(
                [margin, margin, SIZE - margin, SIZE - margin],
                fill=(r, g, b, 220)
            )
            
            # Draw state name
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            except:
                font = ImageFont.load_default()
            
            text = name.upper()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text(
                ((SIZE - text_width) / 2, SIZE / 2 - text_height / 2),
                text,
                fill=(255, 255, 255, 255),
                font=font
            )
            
            frames.append(img)
        
        # Save as GIF
        output_path = os.path.join(ASSETS_DIR, f"{name}.gif")
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
            disposal=2,
        )
        print(f"Created: {output_path}")

if __name__ == "__main__":
    main()
