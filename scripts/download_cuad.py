"""Download CUAD v1 (public, CC BY 4.0) into data/cuad/.

Usage: python scripts/download_cuad.py
"""

import shutil
import urllib.request
import zipfile
from pathlib import Path

URL = "https://zenodo.org/records/4595826/files/CUAD_v1.zip?download=1"
DATA = Path(__file__).resolve().parent.parent / "data" / "cuad"


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    archive = DATA / "CUAD_v1.zip"
    if not archive.exists():
        print(f"Downloading {URL} (~100 MB)...")
        with urllib.request.urlopen(URL) as r, open(archive, "wb") as f:
            shutil.copyfileobj(r, f)

    extract_dir = DATA / "extracted"
    if not extract_dir.exists():
        with zipfile.ZipFile(archive) as z:
            z.extractall(extract_dir)

    # CUAD mixes .pdf and .PDF, and glob case-sensitivity differs by OS
    pdfs = [p for p in extract_dir.rglob("*") if p.suffix.lower() == ".pdf"]
    print(f"{len(pdfs)} PDFs under {extract_dir}")
    print("Labels: master_clauses.csv and CUAD_v1.json in the same folder.")


if __name__ == "__main__":
    main()
