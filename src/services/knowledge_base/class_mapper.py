from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ResolutionResult:
    canonical_class: Optional[str]
    resolution_type: str  # EXACT, CASE_INSENSITIVE, EXPLICIT_MAPPING, NOT_FOUND

class ClassMapper:
    """
    Central authority for resolving CNN output class names into
    canonical Knowledge Base class names using a deterministic four-stage strategy.
    """
    CANONICAL_CLASS_MAP = {
        "Apple___Black_rot": "Apple___Black_Rot_Frogeye_Leaf_Spot",
        "Cherry_(including_sour)___Powdery_mildew": "Cherry___Cherry_Powdery_Mildew",
        "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "Corn___Gray_Leaf_Spot_Cercospora_Leaf_Spot",
        "Corn_(maize)___Common_rust_": "Corn___Common_Rust",
        "Corn_(maize)___Northern_Leaf_Blight": "Corn___Northern_Corn_Leaf_Blight_NCLB",
        "Grape___Esca_(Black_Measles)": "Grape___Esca_Black_Measles",
        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Grape___Leaf_Blight_Isariopsis_Leaf_Spot",
        "Orange___Haunglongbing_(Citrus_greening)": "Orange___Citrus_Greening_HLB",
        "Pepper,_bell___Bacterial_spot": "Pepper___Bacterial_Spot",
        "Tomato___Spider_mites Two-spotted_spider_mite": "Tomato___Two_Spotted_Spider_Mite",
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus_TYLCV",
        "Tomato___Tomato_mosaic_virus": "Tomato___Tomato_Mosaic_Virus_ToMV",
    }

    def __init__(self, canonical_classes: List[str]):
        self.canonical_classes = canonical_classes
        # Precompute maps for case-insensitive lookups
        self._canonical_lower_map = {c.lower(): c for c in canonical_classes}
        self._explicit_lower_map = {k.lower(): v for k, v in self.CANONICAL_CLASS_MAP.items()}

    def resolve(self, cnn_class: str) -> ResolutionResult:
        """Resolves CNN class using Exact, Case-insensitive, Explicit, and Not Found stages."""
        if not cnn_class:
            return ResolutionResult(canonical_class=None, resolution_type="NOT_FOUND")

        cleaned = cnn_class.strip()

        # Stage 1: Exact Match
        if cleaned in self.canonical_classes:
            return ResolutionResult(canonical_class=cleaned, resolution_type="EXACT")

        cleaned_lower = cleaned.lower()

        # Stage 2: Case-insensitive Match
        if cleaned_lower in self._canonical_lower_map:
            return ResolutionResult(
                canonical_class=self._canonical_lower_map[cleaned_lower],
                resolution_type="CASE_INSENSITIVE"
            )

        # Stage 3: Explicit Mapping Table (Exact and Case-insensitive keys)
        if cleaned in self.CANONICAL_CLASS_MAP:
            return ResolutionResult(
                canonical_class=self.CANONICAL_CLASS_MAP[cleaned],
                resolution_type="EXPLICIT_MAPPING"
            )

        if cleaned_lower in self._explicit_lower_map:
            return ResolutionResult(
                canonical_class=self._explicit_lower_map[cleaned_lower],
                resolution_type="EXPLICIT_MAPPING"
            )

        # Stage 4: Not Found
        return ResolutionResult(canonical_class=None, resolution_type="NOT_FOUND")
