import os
import shutil
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable, Optional, Tuple, List, Set
from .base import StorageProvider, StorageRef, StorageItem

class LocalDiskProvider(StorageProvider):
    def __init__(self, root_path: str):
        self._root = Path(root_path).resolve()
        if not self._root.exists():
            self._root.mkdir(parents=True, exist_ok=True)
            
        # Ensure foundational directories
        (self._root / "originals").mkdir(exist_ok=True)
        (self._root / "previews").mkdir(exist_ok=True)
        (self._root / "index").mkdir(exist_ok=True)
        (self._root / "assets").mkdir(exist_ok=True)
        
        self._root_id = self._root.name or "local_root"

    def _resolve(self, ref: StorageRef) -> Path:
        if ref.provider != self.provider_name() or ref.root_id != self._root_id:
            raise ValueError("Invalid StorageRef for LocalDiskProvider")
        
        # Sanitize key to prevent directory traversal
        clean_key = PurePosixPath(ref.key).as_posix()
        if clean_key.startswith("/") or ".." in clean_key:
             raise ValueError("Absolute paths or directory traversal not permitted in keys")
             
        full_path = (self._root / clean_key).resolve()
        
        # Double check containment
        if not full_path.is_relative_to(self._root):
            raise ValueError("Resolved path escapes root directory")
            
        return full_path

    # Identity
    def provider_name(self) -> str:
        return "local_disk"

    def root_id(self) -> str:
        return self._root_id

    # Path helpers
    def join(self, *parts: str) -> str:
        return PurePosixPath(*parts).as_posix()

    def ref(self, key: str) -> StorageRef:
        return StorageRef(provider=self.provider_name(), root_id=self.root_id(), key=key)

    def _make_item(self, path: Path, ref: StorageRef) -> StorageItem:
        stat = path.stat()
        return StorageItem(
            ref=ref,
            name=path.name,
            is_dir=path.is_dir(),
            size_bytes=stat.st_size,
            modified_utc=stat.st_mtime
        )

    # Existence & Listing
    def exists(self, ref: StorageRef) -> bool:
        return self._resolve(ref).exists()

    def stat(self, ref: StorageRef) -> StorageItem:
        path = self._resolve(ref)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {ref.key}")
        return self._make_item(path, ref)

    def listdir(self, ref: StorageRef) -> Iterable[StorageItem]:
        path = self._resolve(ref)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {ref.key}")
            
        for child in path.iterdir():
            child_key = self.join(ref.key, child.name) if ref.key else child.name
            yield self._make_item(child, self.ref(child_key))

    def walk(self, ref: StorageRef, extensions: Optional[Set[str]] = None) -> Iterable[StorageItem]:
        start_path = self._resolve(ref)
        if not start_path.exists() or not start_path.is_dir():
            return
            
        exts = {e.lower() if e.startswith('.') else f".{e.lower()}" for e in extensions} if extensions else None

        for root, dirs, files in os.walk(start_path):
            root_p = Path(root)
            # Calculate posix relative key
            rel_root = root_p.relative_to(self._root).as_posix()
            
            for file in files:
                if exts:
                    ext = Path(file).suffix.lower()
                    if ext not in exts:
                        continue
                
                key = self.join(rel_root, file) if rel_root != "." else file
                yield self._make_item(root_p / file, self.ref(key))

    # IO
    def open_read(self, ref: StorageRef) -> BinaryIO:
        return open(self._resolve(ref), 'rb')

    def open_write(self, ref: StorageRef, overwrite: bool = True) -> BinaryIO:
        path = self._resolve(ref)
        if not overwrite and path.exists():
            raise FileExistsError(f"File already exists: {ref.key}")
        path.parent.mkdir(parents=True, exist_ok=True)
        return open(path, 'wb')

    def put_bytes(self, ref: StorageRef, data: bytes, overwrite: bool = True) -> None:
        with self.open_write(ref, overwrite) as f:
            f.write(data)

    def get_bytes(self, ref: StorageRef, max_bytes: Optional[int] = None) -> bytes:
        with self.open_read(ref) as f:
            return f.read(max_bytes) if max_bytes else f.read()

    # File operations
    def mkdirs(self, ref: StorageRef) -> None:
        self._resolve(ref).mkdir(parents=True, exist_ok=True)

    def delete(self, ref: StorageRef) -> None:
        path = self._resolve(ref)
        if path.exists():
            if path.is_dir():
                # Safety constraint: Only allow deleting files explicitly via this method.
                raise IsADirectoryError("delete() is for files. Avoid recursive deletes directly via API.")
            path.unlink()

    def copy(self, src: StorageRef, dst: StorageRef, overwrite: bool = False) -> None:
        src_path = self._resolve(src)
        dst_path = self._resolve(dst)
        if not overwrite and dst_path.exists():
            raise FileExistsError(f"Destination exists: {dst.key}")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

    def move(self, src: StorageRef, dst: StorageRef, overwrite: bool = False) -> None:
        src_path = self._resolve(src)
        dst_path = self._resolve(dst)
        if not overwrite and dst_path.exists():
            raise FileExistsError(f"Destination exists: {dst.key}")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src_path, dst_path)

    # Local access
    def to_local_path(self, ref: StorageRef) -> Optional[str]:
        return str(self._resolve(ref))

    def ensure_local_cache(self, ref: StorageRef) -> str:
        return str(self._resolve(ref))  # Already local

    # Changes (stubs)
    def get_change_token(self) -> Optional[str]:
        return None

    def poll_changes(self, since_token: Optional[str]) -> Tuple[List[StorageItem], Optional[str]]:
        return [], None
