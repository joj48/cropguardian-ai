"""
kb_lookup_audit.py — Focused Knowledge Base Lookup Audit

Traces all six diagnostic points for a given CNN class:
  1. CNN predicted class (input)
  2. get_disease() input (as received)
  3. Mapping resolution (cache index keys checked)
  4. JSON file selected (crop file path)
  5. Disease ID selected (from record)
  6. Exact exception (if any)

Run with:
  venv/Scripts/python.exe scripts/kb_lookup_audit.py <cnn_class>

If no argument is given, pulls the most recent pipeline_response log automatically.
"""

import sys
import os
import json
import glob
from pathlib import Path

# ── Bootstrap sys.path so project imports work ───────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.knowledge_base.kb_loader import KnowledgeBaseLoader
from src.services.knowledge_base.kb_cache import KnowledgeBaseCache
from src.services.knowledge_base.models import DiseaseRecord
from src.services.knowledge_base.exceptions import DiseaseNotFound

DIVIDER = "-" * 72

def audit(cnn_class: str):
    print(f"\n{DIVIDER}")
    print("  KNOWLEDGE BASE LOOKUP AUDIT")
    print(DIVIDER)

    # ── 1. CNN predicted class ────────────────────────────────────────────────
    print(f"\n[1] CNN Predicted Class (raw input)")
    print(f"    Value   : {repr(cnn_class)}")
    print(f"    Type    : {type(cnn_class).__name__}")
    print(f"    Length  : {len(cnn_class)} chars")

    # ── 2. get_disease() input ────────────────────────────────────────────────
    print(f"\n[2] get_disease() input (as received)")
    print(f"    Identical to CNN class: {repr(cnn_class)}")

    # ── 3. Mapping resolution — what the cache index contains ─────────────────
    print(f"\n[3] Mapping Resolution — Cache Index Keys")
    loader = KnowledgeBaseLoader()
    cache  = KnowledgeBaseCache()

    try:
        config = loader.load_config()
        supported_crops = config.get("supported_crops", [])
        print(f"    Supported crops in config : {supported_crops}")
    except Exception as e:
        print(f"    ERROR loading config      : {e}")
        supported_crops = []

    # Load all crops and build the index
    all_index_keys = []
    for crop in supported_crops:
        raw = loader.load_crop_data(crop)
        for record_dict in raw:
            try:
                record = DiseaseRecord(**record_dict)
                cache.set_crop(crop, [record])
                all_index_keys.append(record.model_mapping.cnn_class)
            except Exception as e:
                print(f"    PARSE ERROR in crop '{crop}': {e}")

    print(f"\n    Total entries in cache index : {len(all_index_keys)}")
    print(f"\n    All indexed cnn_class values:")
    for k in sorted(all_index_keys):
        match = "  ← *** MATCH ***" if k == cnn_class else ""
        print(f"      {repr(k)}{match}")

    # Check for near-matches (case / underscore / space differences)
    print(f"\n    Near-match analysis (normalised comparison):")
    cnn_norm = cnn_class.lower().replace(" ", "_")
    for k in sorted(all_index_keys):
        k_norm = k.lower().replace(" ", "_")
        if k_norm == cnn_norm and k != cnn_class:
            print(f"      Near-match (case/space diff): {repr(k)}")
        elif cnn_norm in k_norm or k_norm in cnn_norm:
            print(f"      Substring match             : {repr(k)}")

    # ── 4. JSON file selected ─────────────────────────────────────────────────
    print(f"\n[4] JSON File Selected")
    if "___" in cnn_class:
        crop_name = cnn_class.split("___")[0]
    else:
        crop_name = cnn_class

    filename = f"{crop_name.lower().replace(' ', '_')}.json"
    file_path = loader.root_dir / filename
    print(f"    Derived crop name : {repr(crop_name)}")
    print(f"    Expected filename  : {filename}")
    print(f"    Full path          : {file_path}")
    print(f"    File exists        : {file_path.exists()}")

    if file_path.exists():
        raw = loader.load_crop_data(crop_name)
        print(f"    Records in file    : {len(raw)}")
        print(f"    Disease IDs found  :")
        for r in raw:
            did = r.get("disease_id", "N/A")
            cnn = r.get("model_mapping", {}).get("cnn_class", "N/A")
            aliases = r.get("model_mapping", {}).get("aliases", [])
            print(f"      disease_id={repr(did)}  cnn_class={repr(cnn)}  aliases={aliases}")

    # ── 5. Disease ID selected ────────────────────────────────────────────────
    print(f"\n[5] Disease ID Selected")
    direct = cache.get_disease(cnn_class)
    if direct:
        print(f"    Found via direct cache hit: disease_id={repr(direct.disease_id)}")
        print(f"    Disease name             : {direct.disease_name}")
    else:
        print(f"    Direct cache hit         : NOT FOUND")

    # ── 6. Exact exception ────────────────────────────────────────────────────
    print(f"\n[6] Exact Exception from get_disease()")
    from src.services.knowledge_base.kb_manager import KnowledgeBaseManager
    try:
        mgr = KnowledgeBaseManager(validate_on_startup=False)
        result = mgr.get_disease(cnn_class)
        print(f"    RESULT: SUCCESS")
        print(f"    disease_id   : {result.disease_id}")
        print(f"    disease_name : {result.disease_name}")
    except DiseaseNotFound as e:
        print(f"    EXCEPTION: DiseaseNotFound")
        print(f"    Message     : {e}")
    except Exception as e:
        print(f"    EXCEPTION: {type(e).__name__}")
        print(f"    Message     : {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{DIVIDER}\n")


def get_cnn_class_from_latest_log() -> str:
    """Reads the most recent response JSON from logs/responses/ and extracts the disease class."""
    log_dir = PROJECT_ROOT / "logs" / "responses"
    files = sorted(glob.glob(str(log_dir / "*.json")), reverse=True)
    if not files:
        return None
    latest = files[0]
    print(f"\n  Auto-detected latest response log: {latest}")
    try:
        with open(latest, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Support both new grouped schema and old flat schema
        prediction = data.get("prediction") or data.get("result") or {}
        return prediction.get("disease")
    except Exception as e:
        print(f"  Could not read log: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cnn_class = sys.argv[1]
    else:
        cnn_class = get_cnn_class_from_latest_log()
        if not cnn_class:
            print("Usage: venv\\Scripts\\python.exe scripts\\kb_lookup_audit.py <cnn_class>")
            print("  OR run without arguments to auto-read the latest response log.")
            sys.exit(1)

    audit(cnn_class)
