from backend.api.url_validator import validate_url
import trimesh
import logging
import urllib.request
import urllib.parse
import tempfile
import os
from typing import Optional, Dict

logger = logging.getLogger(__name__)

def extract_3d_metadata(file_path_or_url: str) -> Optional[Dict]:
    """Extracts Bounding Box dimensions, Vertex Count, and Material Count from a 3D file."""
    temp_file = None
    try:
        # Check if it's a URL
        if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
            # Validate external URL to prevent SSRF
            validate_url(file_path_or_url)

            suffix = os.path.splitext(urllib.parse.urlparse(file_path_or_url).path)[1]
            if not suffix:
                suffix = ".glb" # Default
            fd, temp_file = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            urllib.request.urlretrieve(file_path_or_url, temp_file)
            load_path = temp_file
        else:
            load_path = file_path_or_url

        if not os.path.exists(load_path):
            logger.error(f"File not found for metadata extraction: {load_path}")
            return None

        # Try loading scene or mesh
        scene = trimesh.load(load_path, force="scene")

        # Bounding box dimensions
        extents = scene.extents.tolist() if scene.extents is not None else [0.0, 0.0, 0.0]

        # Vertex count
        vertex_count = sum(len(g.vertices) for g in scene.geometry.values()) if scene.geometry else 0

        # Material count
        material_count = 0
        if hasattr(scene, 'geometry') and scene.geometry:
            materials = set()
            for g in scene.geometry.values():
                if hasattr(g, 'visual') and hasattr(g.visual, 'material'):
                    # To unique materials, we might just count them or hash them
                    materials.add(id(g.visual.material))
            material_count = len(materials)

        return {
            "bounding_box": extents,
            "vertex_count": vertex_count,
            "material_count": material_count
        }

    except Exception as e:
        logger.error(f"Failed to extract 3D metadata from {file_path_or_url}: {e}")
        return None
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
