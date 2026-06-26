import sys
import os
from pathlib import Path
from typing import List, Dict, Any

from src.utils.logger import get_logger
from .exceptions import ValidationError

logger = get_logger("knowledge_base", "knowledge_base.log")

# We dynamically import the existing validation script to reuse its logic
# without duplicating code.
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from knowledge_base.tools.validate_knowledge_base import validate_record
except ImportError:
    validate_record = None
    logger.warning("Could not import existing validation script.")

class KnowledgeBaseValidator:
    """Provides runtime validation using existing validation logic."""
    
    @staticmethod
    def validate_crop_data(crop_name: str, records: List[Dict[str, Any]]):
        """Validates loaded crop data against the expected schema."""
        from pydantic import ValidationError as PydanticValidationError
        from .models import DiseaseRecord

        errors = []
        file_name = f"{crop_name.lower().replace(' ', '_')}.json"

        for index, record in enumerate(records):
            # 1. Run legacy JSON checks if available
            if validate_record:
                issues = validate_record(record, file_name, index)
                if issues:
                    for issue in issues:
                        log_msg = f"Legacy Validation Issue in {file_name} | Record {index} | {issue}"
                        logger.error(log_msg)
                        errors.append(log_msg)

            # 2. Run canonical Pydantic model validation
            try:
                DiseaseRecord(**record)
            except PydanticValidationError as e:
                disease_id = record.get("disease_id", "Unknown ID")
                cnn_class = record.get("model_mapping", {}).get("cnn_class", "Unknown Class")
                
                for error in e.errors():
                    field_name = " -> ".join(str(loc) for loc in error["loc"])
                    msg = error["msg"]
                    log_msg = (
                        f"Validation Failure in {file_name} | "
                        f"Disease ID: {disease_id} | "
                        f"CNN Class: {cnn_class} | "
                        f"Field: {field_name} | "
                        f"Error: {msg}"
                    )
                    logger.error(log_msg)
                    errors.append(log_msg)

        if errors:
            err_msg = f"Validation failed for {file_name}: {len(errors)} issues found."
            raise ValidationError(err_msg)
