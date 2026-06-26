"""
download_rtl.py
================
Downloads open-source RTL (Verilog) designs from multiple public GitHub
repositories:
  • RTLLM      – hkust-zhiyao/RTLLM
  • VTR        – verilog-to-routing/vtr-verilog-to-routing
  • VerilogEval – NVlabs/verilog-eval

Files are saved to  data/rtl/<source>/<filename>.v
Run from the project root:
    python data/scripts/download_rtl.py
"""

import os
import time
import json
import requests

# ── Output directory ──────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RTL_DIR = os.path.join(PROJECT_ROOT, "data", "rtl")

# ── GitHub API helpers ────────────────────────────────────────────────────────
GITHUB_API   = "https://api.github.com"
GITHUB_RAW   = "https://raw.githubusercontent.com"
HEADERS      = {"Accept": "application/vnd.github.v3+json"}
MAX_PER_REPO = 40        # cap per repo to stay under API rate limits
MAX_FILE_KB  = 150       # skip very large files (>150 KB)


def _get(url: str, retries: int = 3) -> requests.Response | None:
    """GET with simple retry / back-off."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r
            if r.status_code == 403:
                print(f"  [!]  Rate-limited (403). Sleeping 60 s ?")
                time.sleep(60)
            else:
                print(f"  [!]  HTTP {r.status_code} for {url}")
                return None
        except requests.RequestException as exc:
            print(f"  [!]  Request error ({exc}). Retrying ?")
            time.sleep(2 ** attempt)
    return None


def list_verilog_files(repo: str, branch: str, path: str, depth: int = 0) -> list[dict]:
    """
    Recursively list .v files under `path` in a GitHub repo.
    Returns list of dicts: {name, download_url, size}.
    """
    if depth > 3:
        return []

    url  = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref={branch}"
    resp = _get(url)
    if resp is None:
        return []

    items = resp.json()
    if not isinstance(items, list):
        return []

    results = []
    for item in items:
        if item.get("type") == "file" and item["name"].endswith(".v"):
            results.append({
                "name":         item["name"],
                "download_url": item.get("download_url") or
                                f"{GITHUB_RAW}/{repo}/{branch}/{item['path']}",
                "size":         item.get("size", 0),
            })
        elif item.get("type") == "dir":
            results.extend(list_verilog_files(repo, branch, item["path"], depth + 1))
    return results


def download_file(url: str, dest_path: str) -> bool:
    """Download a single file. Returns True on success."""
    resp = _get(url)
    if resp is None:
        return False
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8", errors="ignore") as fh:
        fh.write(resp.text)
    return True


# ── Repository definitions ────────────────────────────────────────────────────
REPOS = [
    {
        "label":  "RTLLM",
        "repo":   "hkust-zhiyao/RTLLM",
        "branch": "main",
        "paths":  [""],          # search from root
    },
    {
        "label":  "VTR",
        "repo":   "verilog-to-routing/vtr-verilog-to-routing",
        "branch": "master",
        "paths":  ["vtr_flow/benchmarks/verilog"],
    },
    {
        "label":  "VerilogEval",
        "repo":   "NVlabs/verilog-eval",
        "branch": "main",
        "paths":  ["data/verilog_eval_v2", "data/verilog_eval_v1"],
    },
]

# Curated fallback: direct raw URLs for well-known VTR Verilog benchmarks
VTR_FALLBACK_URLS = {
    "sha.v":         "https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/master/vtr_flow/benchmarks/verilog/sha.v",
    "diffeq1.v":     "https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/master/vtr_flow/benchmarks/verilog/diffeq1.v",
    "diffeq2.v":     "https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/master/vtr_flow/benchmarks/verilog/diffeq2.v",
    "blob_merge.v":  "https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/master/vtr_flow/benchmarks/verilog/blob_merge.v",
    "ch_intrinsics.v": "https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/master/vtr_flow/benchmarks/verilog/ch_intrinsics.v",
    "stereovision0.v": "https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/master/vtr_flow/benchmarks/verilog/stereovision0.v",
    "stereovision1.v": "https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/master/vtr_flow/benchmarks/verilog/stereovision1.v",
}


def download_repo(cfg: dict, out_dir: str) -> int:
    """Download up to MAX_PER_REPO Verilog files from a repo config."""
    label = cfg["label"]
    print(f"\n{'='*60}")
    print(f"  Source: {label}  ({cfg['repo']})")
    print(f"{'='*60}")

    all_files: list[dict] = []
    for path in cfg["paths"]:
        found = list_verilog_files(cfg["repo"], cfg["branch"], path)
        all_files.extend(found)
        if len(all_files) >= MAX_PER_REPO * 2:
            break

    # Filter out huge files
    all_files = [f for f in all_files if f["size"] <= MAX_FILE_KB * 1024]

    # Deduplicate by name
    seen = set()
    unique = []
    for f in all_files:
        if f["name"] not in seen:
            seen.add(f["name"])
            unique.append(f)

    unique = unique[:MAX_PER_REPO]
    print(f"  Found {len(unique)} files to download")

    downloaded = 0
    for info in unique:
        dest = os.path.join(out_dir, label.lower(), info["name"])
        if os.path.exists(dest):
            print(f"  [OK]  (cached) {info['name']}")
            downloaded += 1
            continue
        ok = download_file(info["download_url"], dest)
        if ok:
            print(f"  [OK]  {info['name']}  ({info['size']//1024} KB)")
            downloaded += 1
        else:
            print(f"  [X]  Failed: {info['name']}")
        time.sleep(0.3)   # be polite

    return downloaded


def download_vtr_fallback(out_dir: str) -> int:
    """Download curated VTR benchmark files directly."""
    print(f"\n{'='*60}")
    print(f"  Source: VTR (curated fallback URLs)")
    print(f"{'='*60}")
    sub = os.path.join(out_dir, "vtr")
    downloaded = 0
    for name, url in VTR_FALLBACK_URLS.items():
        dest = os.path.join(sub, name)
        if os.path.exists(dest):
            print(f"  [OK]  (cached) {name}")
            downloaded += 1
            continue
        ok = download_file(url, dest)
        print(f"  {'[OK]' if ok else '[X]'}  {name}")
        if ok:
            downloaded += 1
        time.sleep(0.2)
    return downloaded


def count_rtl(out_dir: str) -> int:
    total = 0
    for root, _, files in os.walk(out_dir):
        total += sum(1 for f in files if f.endswith(".v"))
    return total


def main():
    os.makedirs(RTL_DIR, exist_ok=True)
    print(f"RTL output directory: {RTL_DIR}\n")

    total = 0

    # 1. Try GitHub API for each repo
    for repo_cfg in REPOS:
        n = download_repo(repo_cfg, RTL_DIR)
        total += n

    # 2. Always try curated VTR fallback (fast direct URLs)
    n = download_vtr_fallback(RTL_DIR)
    total += n

    # 3. Summary
    actual = count_rtl(RTL_DIR)
    print(f"\n{'='*60}")
    print(f"  Download complete.")
    print(f"  Total .v files now in data/rtl/: {actual}")
    print(f"{'='*60}")

    if actual < 20:
        print("\n  [!]  Fewer than 20 files downloaded (possible API rate limit).")
        print("  -> Run:  python data/scripts/generate_rtl_local.py")
        print("    to supplement with locally-generated designs.\n")
    else:
        print("\n  [OK] Good ? now run the local generator to add more variety:")
        print("     python data/scripts/generate_rtl_local.py\n")


if __name__ == "__main__":
    main()
