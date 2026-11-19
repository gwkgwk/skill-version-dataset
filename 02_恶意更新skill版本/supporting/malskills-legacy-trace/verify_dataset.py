"""Verify dataset bytes and coverage; never execute a Skill artifact."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = root / "MANIFEST.sha256"
file_count = 0
for line in manifest.read_text(encoding="utf-8").splitlines():
    digest, relative = line.split("  ", 1)
    path = (root / relative).resolve()
    assert path.is_relative_to(root), relative
    assert path.is_file(), relative
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative
    file_count += 1
load = lambda name: json.loads((root / name).read_text(encoding="utf-8-sig"))
samples = load("final_200_version_index.json")
pairs = load("candidate_update_pairs_212.json")
assert len(samples) == 200 and len(pairs) == 212
assert sum(s["historical_record_count"] > 0 for s in samples) == 42
assert all(p["update_security_label"] is None for p in pairs)
restored = 0
blocked = 0
for snapshot in load("recovery_results.json"):
    assert snapshot["version_matches"]
    for item in snapshot["files"]:
        path = root / snapshot["local_directory"] / item["name"]
        if item["status"] == "downloaded":
            assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], str(path)
            restored += 1
        elif item["status"] == "blocked_by_host_security":
            assert not path.exists(), str(path)
            blocked += 1
assert restored == 27 and blocked == 3
assert len(load("diff_summary.json")) == 7
print(f"Verified {file_count} files, 200 indexed samples, 212 candidate pairs, 27 recovered files, 3 blocked omissions.")
