"""Offline provenance and byte-integrity verification; no sample code is run."""
import collections
import hashlib
import json
import sqlite3
import urllib.parse
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git_hash(data, kind):
    return hashlib.sha1(f"{kind} {len(data)}\0".encode() + data).hexdigest()


def verify_tree(snapshot, files):
    children = collections.defaultdict(list)
    expected = {"": snapshot["sha"]}
    for entry in snapshot["tree"]:
        path = PurePosixPath(entry["path"])
        parent = str(path.parent)
        parent = "" if parent == "." else parent
        children[parent].append(entry)
        if entry["type"] == "tree":
            expected[entry["path"]] = entry["sha"]
        else:
            assert entry["type"] == "blob"
            record = files[entry["path"]]
            assert record["git_blob_sha1"] == entry["sha"]
            assert record["mode"] == entry["mode"]
            assert record["size"] == entry["size"]
    def reconstruct(directory):
        entries = children[directory]
        entries.sort(key=lambda e: PurePosixPath(e["path"]).name.encode("utf-8") + (b"/" if e["type"] == "tree" else b""))
        result = bytearray()
        for entry in entries:
            name = PurePosixPath(entry["path"]).name
            sha = reconstruct(entry["path"]) if entry["type"] == "tree" else entry["sha"]
            result += entry["mode"].lstrip("0").encode() + b" " + name.encode("utf-8") + b"\0" + bytes.fromhex(sha)
        actual = git_hash(bytes(result), "tree")
        assert actual == expected[directory], (directory, actual, expected[directory])
        return actual
    reconstruct("")


def main():
    updates = [json.loads(line) for line in (ROOT / "updates.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(updates) == 500, len(updates)
    assert len({(u["repo_full_name"], u["skill_path"]) for u in updates}) == 500
    assert len({(u["old"]["primary"]["git_blob_sha1"], u["new"]["primary"]["git_blob_sha1"]) for u in updates}) == 500
    repo_counts = collections.Counter(u["repo_full_name"] for u in updates)
    canonical_ids = [("/".join(urllib.parse.urlparse(u["commit_url"]).path.strip("/").split("/")[:2]).lower(), u["skill_path"]) for u in updates]
    assert len(set(canonical_ids)) == 500
    assert max(repo_counts.values()) <= 2
    file_count = 0
    byte_count = 0
    snapshots = 0
    timestamps = []
    primary_bytes = 0
    source_db = ROOT / "source/agent_skills_sample.db"
    connection = sqlite3.connect(source_db) if source_db.exists() else None
    for expected_number, update in enumerate(updates, 1):
        assert update["id"] == f"GSU-{expected_number:04d}"
        directory = ROOT / update["local_directory"]
        assert directory.resolve().is_relative_to(ROOT)
        metadata = load(directory / "metadata.json")
        assert metadata == update
        assert all(update[k] is None for k in ("old_security_label", "new_security_label", "update_security_label", "release_version"))
        lineage = load(directory / "lineage.json")
        assert lineage["new_revision"] == update["new_revision"]
        assert lineage["parents"][0] == update["old_revision"]
        assert update["old_revision"] != update["new_revision"]
        if connection:
            row = connection.execute("SELECT file_sha, dedup_primary, history_fetched, commit_count FROM artifacts WHERE repo_full_name=? AND path=?", (update["repo_full_name"], update["skill_path"])).fetchone()
            assert row and row[0] == update["seed"]["file_sha"] and row[1] == 1 and row[2] == 1 and row[3] >= 2
        files = load(directory / "files.json")
        for side in ("old", "new"):
            records = {f["path"]: f for f in files[side]}
            actual_paths = {p.relative_to(directory / side).as_posix() for p in (directory / side).rglob("*") if p.is_file()}
            assert actual_paths == set(records), update["id"]
            for relative, record in records.items():
                path = directory / side / relative
                assert path.resolve().is_relative_to(directory.resolve()) and not path.is_symlink()
                data = path.read_bytes()
                assert len(data) == record["size"]
                assert git_hash(data, "blob") == record["git_blob_sha1"], str(path)
                assert hashlib.sha256(data).hexdigest() == record["sha256"], str(path)
                file_count += 1
                byte_count += len(data)
                if relative == "SKILL.md":
                    primary_bytes += len(data)
            snapshot = load(directory / (side + "_tree.json"))
            assert not snapshot["truncated"] and snapshot["sha"] == update[side]["tree_sha"]
            verify_tree(snapshot, records)
            assert len(records) == update[side]["file_count"]
            snapshots += 1
        old = (directory / "old/SKILL.md").read_bytes().decode("utf-8-sig")
        new = (directory / "new/SKILL.md").read_bytes().decode("utf-8-sig")
        assert old.split() != new.split()
        assert (directory / "SKILL.diff").stat().st_size > 0
        if update.get("diff_sha256"):
            assert hashlib.sha256((directory / "SKILL.diff").read_bytes()).hexdigest() == update["diff_sha256"]
        timestamps.append(update["new_commit_at"])
    if connection:
        connection.close()
    report = {"verified": True, "updates": len(updates), "distinct_skills": 500, "repositories": len(repo_counts), "canonical_repositories": len({r for r,p in canonical_ids}), "canonical_distinct_skills": len(set(canonical_ids)), "maximum_updates_per_repository": max(repo_counts.values()), "complete_directory_snapshots": snapshots, "original_files_verified": file_count, "original_bytes_verified": byte_count, "primary_document_bytes": primary_bytes, "git_tree_hashes_reconstructed": snapshots, "gitskills_membership_verified_against_sqlite": source_db.exists(), "gitskills_snapshot_matches_new_primary": sum(u["gitskills_snapshot_matches_new_primary"] for u in updates), "updates_with_sidecar_files": sum(max(u["old"]["file_count"],u["new"]["file_count"])>1 for u in updates), "earliest_update_at": min(timestamps), "latest_update_at": max(timestamps), "security_labels_assigned": 0}
    manifest = ROOT / "MANIFEST.sha256"
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ",1)
            path = (ROOT / relative).resolve()
            assert path.is_relative_to(ROOT)
            assert hashlib.sha256(path.read_bytes()).hexdigest()==digest, relative
    else:
        (ROOT / "verification_report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
