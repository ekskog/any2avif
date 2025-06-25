#!/usr/bin/env python3
from PIL import Image
from PIL.ExifTags import TAGS
import pillow_heif

# Register both HEIF and AVIF support
pillow_heif.register_heif_opener()
try:
    import pillow_avif
except ImportError:
    print("Warning: pillow-avif-plugin not available")

print('📸 ORIGINAL HEIC METADATA:')
print('=' * 40)
with Image.open('IMG_1189.HEIC') as img:
    exif = img.getexif()
    if exif:
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            print(f'{tag}: {value}')
    else:
        print('No EXIF data found')

print('\n📸 CONVERTED AVIF METADATA:')
print('=' * 40)
with Image.open('IMG_1189_test.avif') as img:
    exif = img.getexif()
    if exif:
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            print(f'{tag}: {value}')
    else:
        print('No EXIF data found')
