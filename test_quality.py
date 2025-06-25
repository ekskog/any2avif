#!/usr/bin/env python3
from heic_to_avif import convert_heic_to_avif
import os

original_size = os.path.getsize('IMG_1189.HEIC') / 1024 / 1024

print('🧪 Testing different AVIF quality settings...')
print(f'Original HEIC: {original_size:.2f} MB')
print()

# Test different quality levels
for quality in [50, 60, 70, 80, 90]:
    output_file = f'IMG_1189_q{quality}.avif'
    print(f'Quality {quality}:')
    convert_heic_to_avif('IMG_1189.HEIC', output_file, quality)
    print()
