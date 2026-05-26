"""
Extract all .rar files in data/clips/ to their respective class folders.

This script handles .rar extraction on Windows/Linux/Mac.
Requires either:
  - WinRAR/7-Zip installed with CLI tools
  - Python rarfile package (install via: pip install rarfile)

Usage:
    python scripts/extract_rar_files.py
    python scripts/extract_rar_files.py --force  # re-extract existing files
"""

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLIPS_DIR = PROJECT_ROOT / "data" / "clips"


def find_rar_tool() -> str | None:
    """Find available RAR extraction tool on system."""
    # Check for common RAR tools on PATH
    tools = ["unrar", "7z", "rar"]
    for tool in tools:
        try:
            result = subprocess.run(
                [tool, "-?"],
                capture_output=True,
                timeout=2,
            )
            if result.returncode in [0, 1]:  # Some tools return 1 for help
                return tool
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # If not on PATH, check common Windows install locations for 7z
    common_7z_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]
    for p in common_7z_paths:
        if Path(p).exists():
            return p

    return None


def extract_with_unrar(rar_path: Path, output_dir: Path) -> bool:
    """Extract using unrar command."""
    cmd = ["unrar", "x", "-y", str(rar_path), str(output_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def extract_with_7z(rar_path: Path, output_dir: Path) -> bool:
    """Extract using 7-Zip command."""
    cmd = ["7z", "x", f"-o{output_dir}", str(rar_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def extract_with_rarfile(rar_path: Path, output_dir: Path) -> bool:
    """Extract using Python rarfile package."""
    try:
        import rarfile
        with rarfile.RarFile(str(rar_path)) as rf:
            rf.extractall(path=str(output_dir))
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"    Error with rarfile: {e}")
        return False


def extract_rar(rar_path: Path, output_dir: Path, tool: str | None) -> bool:
    """Extract a single .rar file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try specified tool first
    # If tool is a full path to an executable, call it directly
    if tool and Path(tool).exists():
        exe = str(tool)
        try:
            if exe.lower().endswith("unrar") or exe.lower().endswith("unrar.exe"):
                return subprocess.run([exe, "x", "-y", str(rar_path), str(output_dir)], capture_output=True).returncode == 0
            if exe.lower().endswith("7z.exe") or exe.lower().endswith("7z"):
                return subprocess.run([exe, "x", f"-o{output_dir}", str(rar_path)], capture_output=True).returncode == 0
            if exe.lower().endswith("rar") or exe.lower().endswith("rar.exe"):
                return subprocess.run([exe, "x", "-y", str(rar_path), str(output_dir)], capture_output=True).returncode == 0
        except Exception:
            pass

    if tool == "unrar":
        return extract_with_unrar(rar_path, output_dir)
    elif tool == "7z":
        return extract_with_7z(rar_path, output_dir)

    # Try all available methods
    methods = [
        ("rarfile (Python)", lambda: extract_with_rarfile(rar_path, output_dir)),
        ("unrar", lambda: extract_with_unrar(rar_path, output_dir)),
        ("7z", lambda: extract_with_7z(rar_path, output_dir)),
    ]

    for name, func in methods:
        try:
            if func():
                print(f"    ✓ Extracted using {name}")
                return True
        except Exception as e:
            print(f"    ✗ {name} failed: {e}")
            continue

    return False


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="Re-extract even if folder exists")
    args = ap.parse_args()

    rar_files = sorted(CLIPS_DIR.glob("*.rar"))
    if not rar_files:
        print(f"No .rar files found in {CLIPS_DIR}")
        return

    print(f"Found {len(rar_files)} .rar files\n")

    # Try to find extraction tool
    tool = find_rar_tool()
    if tool:
        print(f"Using extraction tool: {tool}\n")

    extracted = 0
    skipped = 0
    failed = 0

    for rar_path in rar_files:
        # Class name is the .rar filename without extension
        class_name = rar_path.stem
        output_dir = CLIPS_DIR / class_name

        # Check if already extracted
        if output_dir.exists() and list(output_dir.glob("*")) and not args.force:
            print(f"✓ {class_name:25s} (already extracted, use --force to re-extract)")
            skipped += 1
            continue

        print(f"Extracting {class_name:25s} ... ", end="", flush=True)

        if extract_rar(rar_path, output_dir, tool):
            extracted += 1
            print(f"({len(list(output_dir.glob('*')))} items)")
        else:
            failed += 1
            print("FAILED")

    print(f"\n{'='*60}")
    print(f"Extraction summary:")
    print(f"  Extracted: {extracted}")
    print(f"  Skipped:   {skipped}")
    print(f"  Failed:    {failed}")
    print(f"  Total:     {len(rar_files)}")

    if failed > 0:
        print(f"\n⚠️  Failed extractions. Make sure you have:")
        print(f"   - WinRAR (Windows), or")
        print(f"   - 7-Zip (any OS), or")
        print(f"   - Python rarfile: pip install rarfile")
        sys.exit(1)

    print(f"\n✓ All .rar files extracted to {CLIPS_DIR}")
    print(f"\nNext steps:")
    print(f"  1. Run: python scripts/extract_poses.py --device cuda")
    print(f"  2. Run: python scripts/make_splits.py")
    print(f"  3. Run: python src/train.py")


if __name__ == "__main__":
    main()
