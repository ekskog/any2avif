# HEIC to AVIF Converter

A simple Python script to convert HEIC images (iPhone photos) to AVIF format.

## Installation

1. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python heic_to_avif.py
```

The script will:
1. Ask for the path to your HEIC file (you can drag and drop the file)
2. Ask for quality setting (1-100, default 80)
3. Optionally ask for output path (or auto-generate one)
4. Convert the image and show compression statistics

## Testing with iPhone Photos

This script is specifically designed to handle complex HEIC files from iPhones, including:
- Multi-layer HEIC files
- iPhone 14+ Portrait mode photos
- Live Photos (HEIC component)
- High resolution images

## Next Steps

Once you verify this works with your iPhone photos, we can build the production microservice with:
- FastAPI HTTP interface
- Docker containerization
- Kubernetes deployment manifests
- Proper error handling and monitoring
