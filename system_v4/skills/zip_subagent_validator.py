import json
import hashlib
import os
import zipfile

# Valid type configurations (from ZIP_PROTOCOL_v2 spec)
VALID_TYPES = {
    "A2_TO_A1_PROPOSAL_ZIP": {"dir": "FORWARD", "src": "A2", "tgt": "A1", "files": ["A2_PROPOSAL.json"]},
    "A1_TO_A0_STRATEGY_ZIP": {"dir": "FORWARD", "src": "A1", "tgt": "A0", "files": ["A1_STRATEGY_v1.json"]},
    "A0_TO_B_EXPORT_BATCH_ZIP": {"dir": "FORWARD", "src": "A0", "tgt": "B", "files": ["EXPORT_BLOCK.txt"]},
    "B_TO_A0_STATE_UPDATE_ZIP": {"dir": "BACKWARD", "src": "B", "tgt": "A0", "files": ["THREAD_S_SAVE_SNAPSHOT_v2.txt"]},
    "SIM_TO_A0_SIM_RESULT_ZIP": {"dir": "BACKWARD", "src": "SIM", "tgt": "A0", "files": ["SIM_EVIDENCE.txt"]},
    "A0_TO_A1_SAVE_ZIP": {"dir": "BACKWARD", "src": "A0", "tgt": "A1", "files": ["A0_SAVE_SUMMARY.json"]},
    "A1_TO_A2_SAVE_ZIP": {"dir": "BACKWARD", "src": "A1", "tgt": "A2", "files": ["A1_SAVE_SUMMARY.json"]},
    "A2_META_SAVE_ZIP": {"dir": "BACKWARD", "src": "A2", "tgt": "A2", "files": ["A2_META_SAVE_SUMMARY.json"]},
}

class ZipSubagentValidator:
    def _compute_bytes_sha256(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _canonicalize_json(self, data: dict) -> bytes:
        json_str = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return (json_str + "\n").encode('utf-8')

    def validate_bundle(self, zip_path: str) -> dict:
        """
        Validates a ZIP bundle according to ZIP_PROTOCOL_v2 strict rules.
        Returns {"status": "OK"|"REJECT", "tag": str, "details": str}
        """
        if not zipfile.is_zipfile(zip_path):
            return {"status": "REJECT", "tag": "NOT_A_ZIP", "details": "File is not a valid zip archive."}
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                filenames = zipf.namelist()
                
                # Check for required protocol files
                required_meta = {"ZIP_HEADER.json", "MANIFEST.json", "HASHES.sha256"}
                if not required_meta.issubset(set(filenames)):
                    return {"status": "REJECT", "tag": "MISSING_HEADER_FIELD", "details": "Missing required meta files."}
                    
                # 1. Validate Header
                try:
                    header_bytes = zipf.read("ZIP_HEADER.json")
                    header = json.loads(header_bytes)
                except Exception:
                    return {"status": "REJECT", "tag": "MISSING_HEADER_FIELD", "details": "Malformed ZIP_HEADER.json"}
                    
                if header.get("zip_protocol") != "ZIP_PROTOCOL_v2":
                    return {"status": "REJECT", "tag": "MISSING_HEADER_FIELD", "details": "Invalid protocol version."}
                    
                ztype = header.get("zip_type")
                if ztype not in VALID_TYPES:
                    return {"status": "REJECT", "tag": "ZIP_TYPE_DIRECTION_MISMATCH", "details": f"Unknown zip_type {ztype}"}
                    
                cfg = VALID_TYPES[ztype]
                if header.get("direction") != cfg["dir"] or header.get("source_layer") != cfg["src"] or header.get("target_layer") != cfg["tgt"]:
                    return {"status": "REJECT", "tag": "ZIP_TYPE_DIRECTION_MISMATCH", "details": "Direction/layer mismatch."}

                if header.get("source_layer") == "A0" and not header.get("compiler_version"):
                    return {"status": "REJECT", "tag": "MISSING_HEADER_FIELD", "details": "compiler_version required for A0."}

                # 2. Validate Manifest Format and Hash
                try:
                    manifest_bytes = zipf.read("MANIFEST.json")
                    manifest = json.loads(manifest_bytes)
                except Exception:
                    return {"status": "REJECT", "tag": "MANIFEST_HASH_MISMATCH", "details": "Malformed MANIFEST.json"}
                
                canonical_manifest = self._canonicalize_json(manifest)
                computed_manifest_hash = self._compute_bytes_sha256(canonical_manifest)
                
                if computed_manifest_hash != header.get("manifest_sha256"):
                    return {"status": "REJECT", "tag": "MANIFEST_HASH_MISMATCH", "details": "Header manifest_sha256 mismatch."}
                    
                # 3. Validate Payload Allowlist
                expected_payloads = set(cfg["files"])
                actual_payloads = {entry["rel_path"] for entry in manifest}
                
                if expected_payloads != actual_payloads:
                    return {"status": "REJECT", "tag": "FORBIDDEN_FILE_PRESENT", "details": "Payload files do not match zip_type expected files."}

                # 4. Validate exact bytes and hashes
                try:
                    hashes_content = zipf.read("HASHES.sha256").decode('utf-8')
                except Exception:
                    return {"status": "REJECT", "tag": "HASHES_MISMATCH", "details": "Malformed HASHES.sha256"}
                    
                hash_lines = [line.strip() for line in hashes_content.split('\n') if line.strip()]
                parsed_hashes = {}
                for line in hash_lines:
                    parts = line.split("  ", 1)
                    if len(parts) != 2:
                        return {"status": "REJECT", "tag": "INVALID_HASH_FORMAT", "details": "Malformed hash line."}
                    h_val, f_name = parts
                    parsed_hashes[f_name] = h_val
                
                # Verify header hash inside parsed hashes (chicken/egg boundary check)
                canonical_header = self._canonicalize_json(header)
                if parsed_hashes.get("ZIP_HEADER.json") != self._compute_bytes_sha256(canonical_header):
                     return {"status": "REJECT", "tag": "HASHES_MISMATCH", "details": "ZIP_HEADER hash in HASHES.sha256 invalid."}
                     
                # Verify manifest hash inside parsed hashes
                if parsed_hashes.get("MANIFEST.json") != computed_manifest_hash:
                     return {"status": "REJECT", "tag": "HASHES_MISMATCH", "details": "MANIFEST hash in HASHES.sha256 invalid."}

                # Verify payload files
                for entry in manifest:
                    rel_path = entry["rel_path"]
                    if rel_path not in zipf.namelist():
                        return {"status": "REJECT", "tag": "HASHES_MISMATCH", "details": f"Missing file from archive: {rel_path}"}
                        
                    file_bytes = zipf.read(rel_path)
                    
                    if len(file_bytes) != entry["byte_size"]:
                        return {"status": "REJECT", "tag": "HASHES_MISMATCH", "details": f"Byte size mismatch for {rel_path}"}
                        
                    computed_hash = self._compute_bytes_sha256(file_bytes)
                    
                    if computed_hash != entry["sha256"]:
                        return {"status": "REJECT", "tag": "HASHES_MISMATCH", "details": f"Manifest hash mismatch for {rel_path}"}
                        
                    if parsed_hashes.get(rel_path) != computed_hash:
                        return {"status": "REJECT", "tag": "HASHES_MISMATCH", "details": f"HASHES.sha256 mismatch for {rel_path}"}

                return {"status": "OK", "tag": "VALID", "details": "Bundle is deterministic and valid."}
                
        except Exception as e:
            return {"status": "REJECT", "tag": "UNKNOWN_ERROR", "details": str(e)}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        v = ZipSubagentValidator()
        res = v.validate_bundle(sys.argv[1])
        print(f"[{res['status']}] {res['tag']}: {res['details']}")
