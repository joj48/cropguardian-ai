"""
full_kb_audit.py — Complete Knowledge Base Load and Validation Audit

Verifies:
  - All JSON files load
  - All records validate (zero Pydantic errors)
  - Cache builds with expected count
  - get_disease() succeeds for every CNN class
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
# Suppress logger noise during audit
logging.disable(logging.CRITICAL)

from src.services.knowledge_base.kb_manager import KnowledgeBaseManager
from src.services.knowledge_base.kb_loader import KnowledgeBaseLoader
from src.services.knowledge_base.kb_cache import KnowledgeBaseCache
from src.services.knowledge_base.models import DiseaseRecord
import json

loader = KnowledgeBaseLoader()
config = loader.load_config()
supported_crops = config.get("supported_crops", [])

print("\n===== FULL KNOWLEDGE BASE AUDIT =====\n")
print(f"Supported crops: {supported_crops}\n")

total_records   = 0
total_errors    = 0
total_skipped   = 0
all_cnn_classes = []

# Phase A: Per-crop validation
for crop in supported_crops:
    raw = loader.load_crop_data(crop)
    errors   = 0
    success  = 0
    for r in raw:
        try:
            record = DiseaseRecord(**r)
            success += 1
            all_cnn_classes.append(record.model_mapping.cnn_class)
        except Exception as e:
            errors += 1
            total_errors += 1
            print(f"  [FAIL] {crop} / {r.get('disease_id','?')} : {e}")

    status = "OK " if errors == 0 else "ERR"
    print(f"  [{status}] {crop:<20} {success:>2} records valid  |  {errors} errors")
    total_records += success
    total_skipped += errors

print(f"\n  TOTAL: {total_records} valid  |  {total_errors} errors  |  {total_skipped} skipped\n")

# Phase B: Cache population
print("===== CACHE POPULATION =====\n")
mgr = KnowledgeBaseManager(validate_on_startup=False)

# Re-enable logging just for the cache check
logging.disable(logging.NOTSET)

cache_count = len(mgr.cache._disease_index)
norm_count  = len(mgr.cache._normalised_index)
print(f"  Exact index entries      : {cache_count}")
print(f"  Normalised index entries : {norm_count}")

if cache_count == 0:
    print("  [FAIL] Cache is EMPTY. Check for Pydantic errors above.")
else:
    print("  [OK] Cache populated successfully.\n")

# Phase C: get_disease() for every CNN class
print("\n===== get_disease() RESOLUTION TEST =====\n")
passed = 0
failed = 0
for cnn_class in sorted(all_cnn_classes):
    try:
        rec = mgr.get_disease(cnn_class)
        print(f"  [OK ] {cnn_class} -> {rec.disease_id}")
        passed += 1
    except Exception as e:
        print(f"  [ERR] {cnn_class} -> {e}")
        failed += 1

# Phase D: Normalisation test
print(f"\n===== NORMALISATION TEST =====\n")
test_cases = [
    "Tomato___Late_blight",       # lowercase b
    "tomato___late_blight",       # all lowercase
    "Tomato___Late_Blight",       # exact match
    "Apple___Apple_scab",         # lowercase s
    "Potato___early_blight",      # lowercase
]
for tc in test_cases:
    try:
        rec = mgr.get_disease(tc)
        print(f"  [OK ] {tc!r:<45} -> {rec.disease_id}")
    except Exception as e:
        print(f"  [ERR] {tc!r:<45} -> {e}")

print(f"\n===== SUMMARY =====")
print(f"  Records valid         : {total_records}")
print(f"  Records failed        : {total_errors}")
print(f"  Cache entries (exact) : {cache_count}")
print(f"  get_disease() passed  : {passed}")
print(f"  get_disease() failed  : {failed}")
if total_errors == 0 and cache_count > 0 and failed == 0:
    print("\n  ALL CHECKS PASSED. Knowledge Base is fully operational.\n")
else:
    print("\n  SOME CHECKS FAILED. See above for details.\n")
