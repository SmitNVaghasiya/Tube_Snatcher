try:
    from PIL import Image, ImageDraw
    print("Pillow is already installed!")
except ImportError:
    print("Pillow not found. Installing Pillow (modern PIL fork)...")
    import subprocess
    import sys
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pillow'])
        print("Pillow installed successfully!")
        from PIL import Image, ImageDraw
    except subprocess.CalledProcessError:
        print("Failed to install Pillow automatically.")
        print("Please install it manually by running:")
        print("pip install pillow")
        sys.exit(1)

def create_icon(size, filename):
    """Create a simple icon with the specified size"""
    # Create a new image with a dark gray background (#2b2b2b)
    img = Image.new('RGB', (size, size), color='#2b2b2b')
    draw = ImageDraw.Draw(img)
    
    # Add a white download arrow
    arrow_points = [
        (size * 0.3, size * 0.4),  # Top left
        (size * 0.7, size * 0.4),  # Top right
        (size * 0.7, size * 0.6),  # Bottom right
        (size * 0.8, size * 0.6),  # Arrow tip right
        (size * 0.5, size * 0.8),  # Arrow tip bottom
        (size * 0.2, size * 0.6),  # Arrow tip left
        (size * 0.3, size * 0.6),  # Bottom left
    ]
    
    draw.polygon(arrow_points, fill='white')
    
    # Save the icon
    img.save(filename)
    print(f"Created {filename}")

def main():
    """Create all required icon sizes"""
    print("Creating Tube Snatcher extension icons...")
    
    # Create icons in the current directory
    create_icon(16, 'icon16.png')
    create_icon(48, 'icon48.png')
    create_icon(128, 'icon128.png')
    
    print("\n🎉 All icons created successfully!")
    print("📁 Icons saved in the Extension folder:")
    print("   - icon16.png (16x16 pixels)")
    print("   - icon48.png (48x48 pixels)")
    print("   - icon128.png (128x128 pixels)")
    print("\n✅ You can now install the extension in Chrome!")
    print("\n📋 Next steps:")
    print("   1. Open Chrome → chrome://extensions/")
    print("   2. Enable 'Developer mode'")
    print("   3. Click 'Load unpacked'")
    print("   4. Select this Extension folder")

if __name__ == '__main__':
    main()
