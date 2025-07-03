#!/usr/bin/env python3
"""
HEIC to AVIF Conversion Microservice
Production-ready FastAPI service for converting HEIC images to AVIF format
"""

import os
import tempfile
import logging
from typing import Optional
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import pillow_heif
from heic_to_avif import convert_heic_to_avif
from jpeg_to_avif import convert_jpeg_to_avif

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Register HEIF and AVIF support
pillow_heif.register_heif_opener()
try:
    import pillow_avif
    logger.info("✅ AVIF support enabled")
except ImportError:
    logger.error("❌ pillow-avif-plugin not available")
    raise

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
QUALITY = 80  # Fixed quality for web + archival
ALLOWED_EXTENSIONS = {'.heic', '.heif', '.HEIC', '.HEIF', '.jpg', '.jpeg', '.JPG', '.JPEG'}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 HEIC to AVIF converter service starting...")
    
    # Test AVIF encoding on startup
    try:
        test_img = Image.new('RGB', (100, 100), color='red')
        with tempfile.NamedTemporaryFile(suffix='.avif', delete=True) as tmp:
            test_img.save(tmp.name, format='AVIF', quality=QUALITY)
        logger.info("✅ AVIF encoding test successful")
    except Exception as e:
        logger.error(f"❌ AVIF encoding test failed: {e}")
        raise
    
    yield
    logger.info("🛑 Service shutting down...")

app = FastAPI(
    title="HEIC to AVIF Converter",
    description="Convert HEIC images to AVIF format with metadata preservation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def validate_heic_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

def convert_heic_to_avif_bytes(heic_data: bytes, original_filename: str) -> dict:
    """
    Convert HEIC bytes to AVIF bytes with full and thumbnail variants
    Returns: dict with 'full' and 'thumbnail' variants
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as input_tmp:
            input_tmp.write(heic_data)
            input_tmp.flush()
            
            variants = {}
            temp_files_to_cleanup = [input_tmp.name]
            
            try:
                # Open and process the image
                with Image.open(input_tmp.name) as img:
                    logger.info(f"Processing {img.size[0]}x{img.size[1]} image, mode: {img.mode}")
                    
                    # Convert to RGB if necessary
                    if img.mode not in ('RGB', 'RGBA'):
                        logger.info(f"Converting from {img.mode} to RGB")
                        img = img.convert('RGB')
                    
                    input_name = Path(original_filename).stem
                    
                    # Create full-size variant
                    with tempfile.NamedTemporaryFile(suffix='.avif', delete=False) as full_tmp:
                        temp_files_to_cleanup.append(full_tmp.name)
                        img.save(
                            full_tmp.name,
                            format='AVIF',
                            quality=QUALITY,
                            speed=6  # Encoding speed (0-10, 6 is good balance)
                        )
                        
                        with open(full_tmp.name, 'rb') as f:
                            full_data = f.read()
                        
                        variants['full'] = {
                            'data': full_data,
                            'filename': f"{input_name}.avif",
                            'size': len(full_data)
                        }
                    
                    # Create thumbnail variant (max 300px on longest side)
                    thumbnail_img = img.copy()
                    thumbnail_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    
                    with tempfile.NamedTemporaryFile(suffix='.avif', delete=False) as thumb_tmp:
                        temp_files_to_cleanup.append(thumb_tmp.name)
                        thumbnail_img.save(
                            thumb_tmp.name,
                            format='AVIF',
                            quality=QUALITY,
                            speed=6
                        )
                        
                        with open(thumb_tmp.name, 'rb') as f:
                            thumb_data = f.read()
                        
                        variants['thumbnail'] = {
                            'data': thumb_data,
                            'filename': f"{input_name}_thumb.avif",
                            'size': len(thumb_data)
                        }
                        
                    # Log compression stats
                    input_size = len(heic_data)
                    full_size = variants['full']['size']
                    thumb_size = variants['thumbnail']['size']
                    compression_ratio = (1 - full_size / input_size) * 100
                    
                    logger.info(f"Conversion successful: {input_size/1024/1024:.2f}MB → Full: {full_size/1024/1024:.2f}MB, Thumb: {thumb_size/1024:.2f}KB ({compression_ratio:.1f}% reduction)")
                    
                    return variants
                        
            finally:
                # Cleanup temp files
                for temp_file in temp_files_to_cleanup:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                    
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )

def validate_jpeg_file(file: UploadFile):
    """Validate uploaded JPEG file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in {'.jpg', '.jpeg'}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected JPEG file, got {file_ext}"
        )
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

def convert_jpeg_to_avif_bytes(jpeg_data: bytes, filename: str) -> dict:
    """
    Convert JPEG bytes to AVIF bytes with full and thumbnail variants
    
    Args:
        jpeg_data: Input JPEG file data
        filename: Original filename
        
    Returns:
        Dict with 'full' and 'thumbnail' variants
    """
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_input:
        temp_input.write(jpeg_data)
        temp_input.flush()
        
        variants = {}
        temp_files_to_cleanup = [temp_input.name]
        
        try:
            # Open and process the image
            with Image.open(temp_input.name) as img:
                logger.info(f"Processing JPEG {img.size[0]}x{img.size[1]} image, mode: {img.mode}")
                
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    logger.info(f"Converting from {img.mode} to RGB")
                    img = img.convert('RGB')
                
                input_name = Path(filename).stem
                
                # Create full-size variant
                with tempfile.NamedTemporaryFile(suffix='.avif', delete=False) as full_tmp:
                    temp_files_to_cleanup.append(full_tmp.name)
                    img.save(
                        full_tmp.name,
                        format='AVIF',
                        quality=QUALITY,
                        speed=6
                    )
                    
                    with open(full_tmp.name, 'rb') as f:
                        full_data = f.read()
                    
                    variants['full'] = {
                        'data': full_data,
                        'filename': f"{input_name}.avif",
                        'size': len(full_data)
                    }
                
                # Create thumbnail variant (max 300px on longest side)
                thumbnail_img = img.copy()
                thumbnail_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                with tempfile.NamedTemporaryFile(suffix='.avif', delete=False) as thumb_tmp:
                    temp_files_to_cleanup.append(thumb_tmp.name)
                    thumbnail_img.save(
                        thumb_tmp.name,
                        format='AVIF',
                        quality=QUALITY,
                        speed=6
                    )
                    
                    with open(thumb_tmp.name, 'rb') as f:
                        thumb_data = f.read()
                    
                    variants['thumbnail'] = {
                        'data': thumb_data,
                        'filename': f"{input_name}_thumb.avif",
                        'size': len(thumb_data)
                    }
                    
                # Log compression stats
                input_size = len(jpeg_data)
                full_size = variants['full']['size']
                thumb_size = variants['thumbnail']['size']
                compression_ratio = (1 - full_size / input_size) * 100
                
                logger.info(f"JPEG conversion successful: {input_size/1024/1024:.2f}MB → Full: {full_size/1024/1024:.2f}MB, Thumb: {thumb_size/1024:.2f}KB ({compression_ratio:.1f}% reduction)")
                
                return variants
                
        finally:
            # Clean up temp files
            for temp_file in temp_files_to_cleanup:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "HEIC/JPEG to AVIF Converter",
        "status": "healthy",
        "version": "1.0.0",
        "quality": QUALITY,
        "max_file_size_mb": MAX_FILE_SIZE // 1024 // 1024,
        "supported_formats": ["HEIC", "HEIF", "JPEG", "JPG"]
    }

@app.get("/health")
async def health():
    """Kubernetes health check"""
    return {"status": "healthy"}

@app.post("/convert")
async def convert_image(
    file: UploadFile = File(..., description="HEIC image file to convert")
):
    """
    Convert HEIC image to AVIF format with full and thumbnail variants
    
    - **file**: HEIC image file (max 50MB)
    - Returns JSON with both full and thumbnail AVIF variants
    """
    logger.info(f"Conversion request: {file.filename} ({file.size} bytes)")
    
    # Validate file
    validate_heic_file(file)
    
    try:
        # Read file content
        heic_data = await file.read()
        
        # Convert to AVIF variants
        variants = convert_heic_to_avif_bytes(heic_data, file.filename or "image")
        
        # Return JSON response with both variants
        response_data = {
            "success": True,
            "original_filename": file.filename,
            "variants": []
        }
        
        for variant_name, variant_data in variants.items():
            import base64
            response_data["variants"].append({
                "variant": variant_name,
                "filename": variant_data["filename"],
                "content": base64.b64encode(variant_data["data"]).decode('utf-8'),
                "size": variant_data["size"],
                "mimetype": "image/avif"
            })
        
        logger.info(f"Conversion response: {len(response_data['variants'])} variants for {file.filename}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/convert-stream")
async def convert_image_stream(
    file: UploadFile = File(..., description="HEIC image file to convert")
):
    """
    Convert HEIC image to AVIF format (streaming response)
    
    - **file**: HEIC image file (max 50MB)
    - Returns AVIF image as streaming response
    """
    logger.info(f"Streaming conversion request: {file.filename} ({file.size} bytes)")
    
    # Validate file
    validate_heic_file(file)
    
    try:
        # Read file content
        heic_data = await file.read()
        
        # Convert to AVIF
        avif_data, output_filename = convert_heic_to_avif_bytes(heic_data, file.filename or "image")
        
        # Create streaming response
        def generate():
            yield avif_data
        
        return StreamingResponse(
            generate(),
            media_type="image/avif",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "Content-Length": str(len(avif_data))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/convert-jpeg")
async def convert_jpeg_image(
    file: UploadFile = File(..., description="JPEG image file to convert")
):
    """
    Convert JPEG image to AVIF format with full and thumbnail variants
    
    - **file**: JPEG image file (max 50MB)
    - Returns JSON with both full and thumbnail AVIF variants
    """
    logger.info(f"JPEG conversion request: {file.filename} ({file.size} bytes)")
    
    # Validate JPEG file
    validate_jpeg_file(file)
    
    try:
        # Read file content
        jpeg_data = await file.read()
        
        # Convert to AVIF variants
        variants = convert_jpeg_to_avif_bytes(jpeg_data, file.filename or "image")
        
        # Return JSON response with both variants
        response_data = {
            "success": True,
            "original_filename": file.filename,
            "variants": []
        }
        
        for variant_name, variant_data in variants.items():
            import base64
            response_data["variants"].append({
                "variant": variant_name,
                "filename": variant_data["filename"],
                "content": base64.b64encode(variant_data["data"]).decode('utf-8'),
                "size": variant_data["size"],
                "mimetype": "image/avif"
            })
        
        logger.info(f"JPEG conversion response: {len(response_data['variants'])} variants for {file.filename}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=3002,
        log_level="info",
        access_log=True
    )
