import threading
from typing import Dict, List, Optional
from .models import DiseaseRecord

class KnowledgeBaseCache:
    """Thread-safe cache for parsed DiseaseRecord objects."""

    def __init__(self):
        self._lock = threading.RLock()
        # Stores lists of records keyed by crop name
        self._crops_cache: Dict[str, List[DiseaseRecord]] = {}
        # Exact cnn_class index for O(1) lookups
        self._disease_index: Dict[str, DiseaseRecord] = {}
        # Normalised index for case-insensitive lookups
        # key = cnn_class.lower().replace(' ', '_')
        self._normalised_index: Dict[str, DiseaseRecord] = {}

    def get_crop(self, crop_name: str) -> Optional[List[DiseaseRecord]]:
        with self._lock:
            return self._crops_cache.get(crop_name)

    def set_crop(self, crop_name: str, records: List[DiseaseRecord]):
        with self._lock:
            self._crops_cache[crop_name] = records
            for record in records:
                cnn_class = record.model_mapping.cnn_class
                self._disease_index[cnn_class] = record
                # Also index under normalised key for case-insensitive lookup
                normalised = cnn_class.lower().replace(" ", "_")
                self._normalised_index[normalised] = record

    def get_disease(self, cnn_class: str) -> Optional[DiseaseRecord]:
        with self._lock:
            # 1. Exact match first
            record = self._disease_index.get(cnn_class)
            if record:
                return record
            # 2. Normalised fallback (handles case differences: Late_blight vs Late_Blight)
            normalised = cnn_class.lower().replace(" ", "_")
            return self._normalised_index.get(normalised)

    def clear(self):
        with self._lock:
            self._crops_cache.clear()
            self._disease_index.clear()
            self._normalised_index.clear()
