# crop_utils.py - Shared Business Utilities for Crop Name Inference

def infer_crop_from_disease(disease_name: str) -> str:
    """
    Infer crop name from a raw disease class identifier or a formatted disease name.
    """
    if not disease_name:
        return "Unknown"

    disease_name = disease_name.strip()

    # Split by PlantVillage delimiter first, or separator
    if "___" in disease_name:
        crop = disease_name.split("___")[0]
    elif " — " in disease_name:
        crop = disease_name.split(" — ")[0]
    elif " - " in disease_name:
        crop = disease_name.split(" - ")[0]
    else:
        crop = disease_name

    # Normalize spelling and formatting: replace underscores and commas
    crop = crop.replace("_", " ")
    crop = crop.replace(",", "")
    crop = " ".join(crop.split())  # Normalize spaces
    crop = crop.strip().title()

    known_crops = [
        "Tomato",
        "Potato",
        "Pepper Bell",
        "Pepper",
        "Apple",
        "Corn",
        "Grape",
        "Cherry",
        "Peach",
        "Orange",
        "Soybean",
        "Strawberry",
        "Blueberry",
        "Raspberry",
        "Squash"
    ]

    # Match against known crops to map e.g. "Pepper Bell" -> "Pepper" or keep it formatted
    for kc in known_crops:
        if kc.lower() in crop.lower():
            return kc

    if crop:
        return crop

    return "Unknown"
