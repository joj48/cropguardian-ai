# constants.py - CropGuardian AI Global Constants

APP_VERSION = "v1.2.0"
MODEL_VERSION = "crop_disease_mobilenetv2_v1"
SUPPORTED_FORMATS = ["JPG", "JPEG", "PNG"]
THEME_PRIMARY_COLOR = "#2E8B57"

SESSION_DEFAULTS = {
    "session_id": None,
    "uploaded_img_path": "",
    "pipeline_response": None,
    "chat_context": {},
    "chat_messages": [],
    "dev_mode": False,
    "show_feedback_form": False,
    "uploaded_image": None,
    "prediction_result": None,
    "weather_data": None,
    "history_filters": {},
}
