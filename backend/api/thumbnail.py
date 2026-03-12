import os
import io
import zipfile
import threading
from PIL import Image
import olefile
import logging

logger = logging.getLogger(__name__)

def generate_thumbnail(file_path: str, thumbnail_dest: str) -> bool:
    """Attempts to extract or generate a 2D thumbnail for 3D/BIM formats."""
    try:
        if not os.path.exists(file_path):
            return False
            
        ext = file_path.lower().split('.')[-1]
        
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(thumbnail_dest), exist_ok=True)
        
        # 1. SketchUp Extraction
        if ext == 'skp':
            if zipfile.is_zipfile(file_path):
                # SketchUp 2021+ files are valid ZIPs containing thumbnail.png
                with zipfile.ZipFile(file_path, 'r') as z:
                    if 'document/thumbnail.png' in z.namelist():
                        z.extract('document/thumbnail.png', '/tmp/extracted_skp')
                        img = Image.open('/tmp/extracted_skp/document/thumbnail.png')
                        img.thumbnail((512, 512))
                        img.save(thumbnail_dest, "PNG")
                        return True
            # Older SketchUp files have embedded Windows thumbnails, harder to parse directly without OLE/native libs
            return False
            
        # 2. Revit / 3ds Max / Other OLE (Microsoft Compound Document Formats)
        if ext in ['rvt', 'rft', 'rfa', 'max']:
            if olefile.isOleFile(file_path):
                with olefile.OleFileIO(file_path) as ole:
                    targets = [
                        ['RevitPreview4.0'], # Revit
                        ['Thumbnail'],       # 3ds Max
                        ['\x05DocumentSummaryInformation'] 
                    ]
                    for t in targets:
                        if ole.exists(t):
                            stream = ole.openstream(t)
                            data = stream.read()
                            
                            # Searching for PNG magic bytes
                            png_idx = data.find(b'\x89PNG')
                            if png_idx != -1:
                                png_data = data[png_idx:]
                                try:
                                    img = Image.open(io.BytesIO(png_data))
                                    img.thumbnail((512, 512))
                                    img.save(thumbnail_dest, "PNG")
                                    return True
                                except Exception:
                                    pass
                            
                            # Searching for JPEG magic bytes
                            jpg_idx = data.find(b'\xff\xd8\xff')
                            if jpg_idx != -1:
                                jpg_data = data[jpg_idx:]
                                try:
                                    img = Image.open(io.BytesIO(jpg_data))
                                    img.thumbnail((512, 512))
                                    img.save(thumbnail_dest, "PNG")
                                    return True
                                except Exception:
                                    pass
        
        # 3. GLB (Sometimes contain embedded rendered previews, but complex to extract without three.js)
        # For now, rely on Three.js frontend for standard 3D formats
        return False
        
    except Exception as e:
        logger.warning(f"Failed to generate thumbnail for {file_path}: {e}")
        return False
