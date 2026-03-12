from backend.api.url_validator import validate_url
import trimesh
import logging
import urllib.request
import urllib.parse
import tempfile
import os
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

def extract_bim_metadata(file_path: str, suffix: str) -> Optional[Dict]:
    """Extracts metadata from BIM files (.ifc, .dwg, .rfa)."""
    suffix = suffix.lower()
    metadata = {
        "element_counts": {},
        "parameters": {},
        "format_specific_data": {}
    }

    try:
        if suffix == ".ifc":
            try:
                import ifcopenshell
                ifc_file = ifcopenshell.open(file_path)

                # Basic counting
                metadata["element_counts"]["IfcWall"] = len(ifc_file.by_type("IfcWall"))
                metadata["element_counts"]["IfcDoor"] = len(ifc_file.by_type("IfcDoor"))
                metadata["element_counts"]["IfcWindow"] = len(ifc_file.by_type("IfcWindow"))
                metadata["element_counts"]["IfcSlab"] = len(ifc_file.by_type("IfcSlab"))

                # Format specific: Project name
                projects = ifc_file.by_type("IfcProject")
                if projects:
                    metadata["format_specific_data"]["project_name"] = projects[0].Name

                return metadata
            except ImportError:
                logger.warning("ifcopenshell not installed. Skipping IFC extraction.")
                return None
            except Exception as e:
                logger.error(f"Error extracting IFC metadata: {e}")
                return None

        elif suffix == ".dwg":
            try:
                import ezdxf
                # Note: ezdxf primarily supports DXF, but can read some basic DWG info or requires conversion
                # For DWG we might only be able to extract basic info without a full DWG library like ODA
                # We will stub it for now or rely on ezdxf if it's actually a DXF disguised as DWG

                try:
                    doc = ezdxf.readfile(file_path)
                    metadata["element_counts"]["layers"] = len(doc.layers)
                    metadata["element_counts"]["blocks"] = len(doc.blocks)
                    return metadata
                except ezdxf.DXFStructureError:
                    logger.warning(f"File {file_path} is not a valid DXF/DWG supported by ezdxf.")
                    return None
            except ImportError:
                logger.warning("ezdxf not installed. Skipping DWG extraction.")
                return None
            except Exception as e:
                logger.error(f"Error extracting DWG metadata: {e}")
                return None

        elif suffix == ".rfa":
            try:
                import olefile
                if olefile.isOleFile(file_path):
                    with olefile.OleFileIO(file_path) as ole:
                        # RFA files store basic info in the "BasicFileInfo" stream
                        if ole.exists('BasicFileInfo'):
                            stream = ole.openstream('BasicFileInfo')
                            data = stream.read().decode('utf-16-le', errors='ignore')

                            # Parse out some basic key-value pairs if possible
                            # The exact format is undocumented but often contains "Format: 202X", etc.
                            metadata["format_specific_data"]["raw_basic_info"] = data[:500] # store first 500 chars safely
                            return metadata
                return None
            except ImportError:
                logger.warning("olefile not installed. Skipping RFA extraction.")
                return None
            except Exception as e:
                logger.error(f"Error extracting RFA metadata: {e}")
                return None

        return None
    except Exception as e:
        logger.error(f"Failed to extract BIM metadata: {e}")
        return None

def extract_3d_metadata(file_path_or_url: str) -> Tuple[Optional[Dict], Optional[Dict]]:
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

        meta3d = {
            "bounding_box": extents,
            "vertex_count": vertex_count,
            "material_count": material_count
        }

        # BIM Extraction
        suffix = os.path.splitext(load_path)[1]
        metabim = extract_bim_metadata(load_path, suffix)

        return meta3d, metabim

    except Exception as e:
        logger.error(f"Failed to extract 3D metadata from {file_path_or_url}: {e}")
        # Even if 3D fails (e.g. trimesh can't parse rfa), try BIM fallback
        if load_path:
            suffix = os.path.splitext(load_path)[1]
            metabim = extract_bim_metadata(load_path, suffix)
            return None, metabim
        return None, None
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
