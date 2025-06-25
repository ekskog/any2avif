#!/usr/bin/env python3
"""
Simple HEIC to AVIF converter for testing
Requires: pillow-heif and pillow-avif-plugin
Install with: pip install pillow-heif pillow-avif-plugin
"""

import os
import sys
from pathlib import Path
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

# AVIF support should be automatic with pillow-avif-plugin
try:
    import pillow_avif
    # The plugin registers itself automatically when imported
except ImportError:
    print("Warning: pillow-avif-plugin not available")

def convert_heic_to_avif(input_path, output_path=None, quality=80):
    """
    Convert HEIC image to AVIF format
    
    Args:
        input_path: Path to input HEIC file
        output_path: Path for output AVIF file (optional)
        quality: AVIF quality (1-100, default 80)
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Generate output path if not provided
        if output_path is None:
            input_file = Path(input_path)
            output_path = input_file.with_suffix('.avif')
        
        print(f"Converting: {input_path}")
        print(f"Output: {output_path}")
        print(f"Quality: {quality}")
        
        # Open and convert the image
        with Image.open(input_path) as img:
            print(f"Image info: {img.size[0]}x{img.size[1]} pixels, mode: {img.mode}")
            
            # Convert to RGB if necessary (AVIF works best with RGB)
            if img.mode not in ('RGB', 'RGBA'):
                print(f"Converting from {img.mode} to RGB")
                img = img.convert('RGB')
            
            # Save as AVIF
            img.save(
                output_path,
                format='AVIF',
                quality=quality,
                speed=6  # Encoding speed (0-10, 6 is good balance)
            )
        
        # Check output file size
        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        compression_ratio = (1 - output_size / input_size) * 100
        
        print(f"\n✅ Conversion successful!")
        print(f"Input size: {input_size / 1024 / 1024:.2f} MB")
        print(f"Output size: {output_size / 1024 / 1024:.2f} MB")
        print(f"Compression: {compression_ratio:.1f}% reduction")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during conversion: {str(e)}")
        return False

def main():
    print("🔄 HEIC to AVIF Converter")
    print("=" * 40)
    
    # Get input file path
    while True:
        input_path = input("\nEnter path to HEIC file (or 'quit' to exit): ").strip()
        
        if input_path.lower() == 'quit':
            print("Goodbye!")
            sys.exit(0)
        
        # Handle drag-and-drop (remove quotes if present)
        input_path = input_path.strip('"\'')
        
        if os.path.exists(input_path):
            break
        else:
            print(f"❌ File not found: {input_path}")
            print("Tip: You can drag and drop the file into the terminal")
    
    # Fixed quality at 80 for optimal web + archival balance
    quality = 80
    
    # Get output path (optional)
    output_path = input("\nEnter output path (press Enter for auto): ").strip()
    if not output_path:
        output_path = None
    else:
        output_path = output_path.strip('"\'')
    
    # Perform conversion
    print("\n🚀 Starting conversion...")
    success = convert_heic_to_avif(input_path, output_path, quality)
    
    if success:
        # Ask if user wants to convert another file
        while True:
            another = input("\nConvert another file? (y/n): ").strip().lower()
            if another in ['y', 'yes']:
                main()
                return
            elif another in ['n', 'no']:
                print("Goodbye!")
                return
            else:
                print("Please enter 'y' or 'n'")
    else:
        print("\nConversion failed. Please check the error message above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
