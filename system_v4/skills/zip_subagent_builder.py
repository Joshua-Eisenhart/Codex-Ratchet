import json
import hashlib
import os
import shutil
import zipfile
from datetime import datetime, timezone

class ZipSubagentBuilder:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def _compute_sha256(self, filepath: str) -> str:
        """Computes the SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _compute_bytes_sha256(self, data: bytes) -> str:
        """Computes the SHA-256 hash of bytes."""
        return hashlib.sha256(data).hexdigest()

    def _canonicalize_json(self, data: dict) -> bytes:
        """Canonicalize JSON per rules: UTF-8, LF, sorted keys, stable separators, trailing newline."""
        json_str = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return (json_str + "\n").encode('utf-8')

    def build_bundle(self, 
                     output_zip_path: str,
                     zip_type: str, 
                     direction: str, 
                     source_layer: str, 
                     target_layer: str,
                     run_id: str,
                     sequence: int,
                     payload_files: dict,
                     compiler_version: str = "") -> bool:
        """
        Builds a compliant ZIP_PROTOCOL_v2 bundle.
        payload_files: dict mapping rel_path -> absolute_path on disk
        """
        
        # 1. Create a temporary staging directory
        staging_dir = output_zip_path + "_staging"
        os.makedirs(staging_dir, exist_ok=True)
        
        try:
            manifest_entries = []
            hashes = {}
            
            # 2. Process payload files
            for rel_path, abs_path in payload_files.items():
                if not os.path.exists(abs_path):
                    print(f"Error: Payload file missing: {abs_path}")
                    return False
                
                # Copy to staging
                target_path = os.path.join(staging_dir, rel_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(abs_path, target_path)
                
                # Compute sizes and hashes
                size = os.path.getsize(target_path)
                sha256 = self._compute_sha256(target_path)
                
                manifest_entries.append({
                    "rel_path": rel_path,
                    "byte_size": size,
                    "sha256": sha256
                })
                hashes[rel_path] = sha256
                
            # 3. Create canonical MANIFEST.json
            manifest_entries.sort(key=lambda x: x["rel_path"])
            manifest_bytes = self._canonicalize_json(manifest_entries)
            manifest_sha256 = self._compute_bytes_sha256(manifest_bytes)
            
            with open(os.path.join(staging_dir, "MANIFEST.json"), "wb") as f:
                f.write(manifest_bytes)
            hashes["MANIFEST.json"] = manifest_sha256
            
            # 4. Create ZIP_HEADER.json
            created_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            header_data = {
                "zip_protocol": "ZIP_PROTOCOL_v2",
                "zip_type": zip_type,
                "direction": direction,
                "source_layer": source_layer,
                "target_layer": target_layer,
                "run_id": run_id,
                "sequence": sequence,
                "created_utc": created_utc,
                "compiler_version": compiler_version,
                "manifest_sha256": manifest_sha256
            }
            header_bytes = self._canonicalize_json(header_data)
            header_sha256 = self._compute_bytes_sha256(header_bytes)
            
            with open(os.path.join(staging_dir, "ZIP_HEADER.json"), "wb") as f:
                f.write(header_bytes)
            hashes["ZIP_HEADER.json"] = header_sha256
            
            # 5. Create HASHES.sha256
            hash_lines = []
            for filepath in sorted(hashes.keys()):
                hash_lines.append(f"{hashes[filepath]}  {filepath}")
            
            hashes_content = "\n".join(hash_lines) + "\n"
            with open(os.path.join(staging_dir, "HASHES.sha256"), "w", encoding="utf-8", newline='\n') as f:
                f.write(hashes_content)
                
            # 6. Build the actual ZIP file (deterministic order)
            all_files = list(payload_files.keys()) + ["MANIFEST.json", "ZIP_HEADER.json", "HASHES.sha256"]
            all_files.sort()
            
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for rel_path in all_files:
                    abs_path = os.path.join(staging_dir, rel_path)
                    zipf.write(abs_path, arcname=rel_path)
                    
            print(f"Successfully built ZIP bundle at {output_zip_path}")
            return True
            
        finally:
            # Cleanup staging
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir)

if __name__ == "__main__":
    print("zip_subagent_builder.py loaded.")
