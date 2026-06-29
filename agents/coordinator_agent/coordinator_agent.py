import os
import time
import datetime
from typing import Dict, Any, Optional

from src.utils.logger import get_logger
from src.services.knowledge_base.kb_manager import KnowledgeBaseManager
from src.services.knowledge_base.models import AdvisoryContext, DiseaseRecord

logger = get_logger("coordinator", "coordinator.log")
performance_logger = get_logger("legacy_performance", "performance.log")
pipeline_logger = get_logger("legacy_pipeline_runs", "pipeline_runs.log")

from agents.disease_detection_agent.disease_detection_agent import DiseaseDetectionAgent
from agents.severity_agent.severity_agent import SeverityAgent
from agents.weather_agent.weather_agent import WeatherAgent
from agents.environmental_risk_agent.environmental_risk_agent import EnvironmentalRiskAgent
from agents.advisory_agent.advisory_agent import AdvisoryAgent


class CoordinatorAgent:
    def __init__(self):
        self.disease_agent = DiseaseDetectionAgent()
        self.severity_agent = SeverityAgent()
        self.weather_agent = WeatherAgent()
        self.risk_agent = EnvironmentalRiskAgent()
        self.advisory_agent = AdvisoryAgent()
        self.kb_manager = KnowledgeBaseManager()
        self.workflow_version = "v1.1"

    def process_image(self, image_path: str, location_input: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Orchestrates the entire inference pipeline: Disease -> KB -> Weather -> Severity -> EnvRisk -> Advisory.
        Produces a grouped response schema: prediction / environment / knowledge / ai / diagnostics.
        Both knowledge_context and ai advice are always populated independently.
        """
        logger.info(f"Pipeline execution started. Workflow: Legacy Coordinator. Location: {location_input}")
        start_time = time.time()

        # Internal bookkeeping (promoted to diagnostics at the end)
        _diag = {
            "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "workflow_version": self.workflow_version,
            "workflow_engine": "legacy_coordinator",
            "status": "success",
            "warnings": [],
            "agent_trace": [],
            "execution_summary": [],
            "pipeline_summary": {
                "overall_status": "success",
                "total_execution_time_ms": 0,
                "successful_agents": 0,
                "failed_agents": 0,
                "skipped_agents": 0
            },
            "execution_time_ms": 0
        }

        # ─── Internal state ────────────────────────────────────────────────────
        weather_data: Optional[Dict] = None
        severity: Optional[Dict] = None
        risk_data: Optional[Dict] = None
        knowledge_record: Optional[DiseaseRecord] = None  # Stays Pydantic until response assembly

        # ─── Validate image ────────────────────────────────────────────────────
        if not os.path.exists(image_path):
            _diag["status"] = "error"
            _diag["pipeline_summary"]["overall_status"] = "error"
            _diag["warnings"].append(f"Image not found at path: {image_path}")
            _diag["execution_time_ms"] = int((time.time() - start_time) * 1000)
            _diag["pipeline_summary"]["total_execution_time_ms"] = _diag["execution_time_ms"]
            return self._build_response(None, None, None, None, knowledge_record, _diag)

        # ─── Step 1: Disease Detection ─────────────────────────────────────────
        t0 = time.time()
        try:
            prediction = self.disease_agent.predict(image_path)
            t1 = time.time()
            _diag["agent_trace"].append("DiseaseDetectionAgent")
            _diag["execution_summary"].append({
                "agent": "DiseaseDetectionAgent", "status": "success",
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["successful_agents"] += 1
            disease_class = prediction["disease"]
        except Exception as e:
            t1 = time.time()
            _diag["status"] = "error"
            _diag["pipeline_summary"]["overall_status"] = "error"
            _diag["warnings"].append(f"Disease detection failed: {e}")
            _diag["execution_summary"].append({
                "agent": "DiseaseDetectionAgent", "status": "failed", "reason": str(e),
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["failed_agents"] += 1
            _diag["execution_time_ms"] = int((time.time() - start_time) * 1000)
            _diag["pipeline_summary"]["total_execution_time_ms"] = _diag["execution_time_ms"]
            return self._build_response(None, None, None, None, knowledge_record, _diag)

        # ─── Step 2: Knowledge Base Retrieval ──────────────────────────────────
        # DiseaseRecord stays as Pydantic model until _build_response() serializes it.
        if "healthy" not in disease_class.lower():
            try:
                knowledge_record = self.kb_manager.get_disease(disease_class)
                logger.info(f"KB record retrieved for: {disease_class} ({knowledge_record.disease_name})")
            except Exception as e:
                logger.warning(f"KB lookup failed for '{disease_class}': {e}")
                _diag["warnings"].append(f"Knowledge Base lookup failed: {e}")

        # Resolve crop name
        from app.utils.crop_utils import infer_crop_from_disease
        crop_val = getattr(knowledge_record, "crop", None) if knowledge_record else None
        if not crop_val:
            crop_val = infer_crop_from_disease(disease_class)
        prediction["crop"] = crop_val or "Unknown"
        logger.debug(f"Prediction crop resolved: {prediction['crop']}")

        # ─── Step 3: Weather Retrieval ─────────────────────────────────────────
        t0 = time.time()
        if location_input or (lat and lon):
            try:
                weather_data = self.weather_agent.get_weather(location_input, lat, lon)
                t1 = time.time()
                if weather_data.get("status") in ["unavailable", "timeout"] or "error" in weather_data:
                    status = weather_data.get("status", "failed")
                    if status == "unavailable": status = "failed"
                    err_msg = weather_data.get("error", "Unknown error")
                    _diag["warnings"].append(f"Weather retrieval failed: {err_msg}")
                    _diag["execution_summary"].append({
                        "agent": "WeatherAgent", "status": status, "reason": err_msg,
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["failed_agents"] += 1
                else:
                    _diag["agent_trace"].append("WeatherAgent")
                    _diag["execution_summary"].append({
                        "agent": "WeatherAgent", "status": "success",
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["successful_agents"] += 1
            except Exception as e:
                t1 = time.time()
                _diag["warnings"].append(f"Weather retrieval failed: {e}")
                _diag["execution_summary"].append({
                    "agent": "WeatherAgent", "status": "failed", "reason": str(e),
                    "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                    "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                    "execution_time_ms": int((t1 - t0) * 1000)
                })
                _diag["pipeline_summary"]["failed_agents"] += 1

        # ─── Step 4: Severity Analysis ─────────────────────────────────────────
        t0 = time.time()
        try:
            severity = self.severity_agent.analyze_severity(
                image_path=image_path, disease_class=disease_class,
                confidence=prediction["confidence"]
            )
            t1 = time.time()
            _diag["agent_trace"].append("SeverityAgent")
            _diag["execution_summary"].append({
                "agent": "SeverityAgent", "status": "success",
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["successful_agents"] += 1
        except Exception as e:
            t1 = time.time()
            _diag["status"] = "partial_success"
            _diag["pipeline_summary"]["overall_status"] = "partial_success"
            _diag["warnings"].append(f"Severity analysis failed: {e}")
            _diag["execution_summary"].append({
                "agent": "SeverityAgent", "status": "failed", "reason": str(e),
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["failed_agents"] += 1

        # ─── Step 5: Environmental Risk Analysis ───────────────────────────────
        t0 = time.time()
        if weather_data:
            try:
                risk_data = self.risk_agent.assess_risk(disease_class, weather_data)
                t1 = time.time()
                if risk_data.get("status") == "skipped":
                    _diag["execution_summary"].append({
                        "agent": "EnvironmentalRiskAgent", "status": "skipped",
                        "reason": risk_data.get("reason", "Weather unavailable"),
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["skipped_agents"] += 1
                elif "error" in risk_data:
                    _diag["warnings"].append(f"Risk assessment failed: {risk_data['error']}")
                    _diag["execution_summary"].append({
                        "agent": "EnvironmentalRiskAgent", "status": "failed",
                        "reason": risk_data["error"],
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["failed_agents"] += 1
                else:
                    _diag["agent_trace"].append("EnvironmentalRiskAgent")
                    _diag["execution_summary"].append({
                        "agent": "EnvironmentalRiskAgent", "status": "success",
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["successful_agents"] += 1
            except Exception as e:
                t1 = time.time()
                _diag["warnings"].append(f"Environmental risk assessment failed: {e}")
                _diag["execution_summary"].append({
                    "agent": "EnvironmentalRiskAgent", "status": "failed", "reason": str(e),
                    "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                    "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                    "execution_time_ms": int((t1 - t0) * 1000)
                })
                _diag["pipeline_summary"]["failed_agents"] += 1

        # ─── Step 6: Advisory Generation ──────────────────────────────────────
        # knowledge_record passed as Pydantic model — only serialized in _build_response()
        advice = None
        t0 = time.time()
        try:
            severity_str = severity["severity"] if severity else "Unknown"
            context = AdvisoryContext(
                disease_data={"disease": disease_class, "confidence": prediction["confidence"]},
                severity_data={"severity": severity_str},
                weather_data=weather_data if weather_data else {},
                risk_data=risk_data if risk_data else {},
                knowledge_context=knowledge_record   # Pydantic model — not a dict
            )
            advice = self.advisory_agent.generate_advice(context)
            t1 = time.time()
            _diag["agent_trace"].append("AdvisoryAgent")
            _diag["execution_summary"].append({
                "agent": "AdvisoryAgent", "status": "success",
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["successful_agents"] += 1
        except Exception as e:
            t1 = time.time()
            _diag["status"] = "partial_success"
            _diag["pipeline_summary"]["overall_status"] = "partial_success"
            _diag["warnings"].append(f"Advisory generation failed: {e}")
            _diag["execution_summary"].append({
                "agent": "AdvisoryAgent", "status": "failed", "reason": str(e),
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["failed_agents"] += 1

        _diag["execution_time_ms"] = int((time.time() - start_time) * 1000)
        _diag["pipeline_summary"]["total_execution_time_ms"] = _diag["execution_time_ms"]

        # Build timeline logs
        timeline_str = f"\n{_diag['timestamp']}\nPipeline Started\n|\n"
        perf_str = "Run Summary:\n"
        for idx, step in enumerate(_diag["execution_summary"]):
            timeline_str += f"{step['agent']}\n{step['execution_time_ms']} ms\n"
            if step["status"] != "success":
                timeline_str += f"Status: {step['status']}\n"
            if idx < len(_diag["execution_summary"]) - 1:
                timeline_str += "|\n"
            perf_str += f"{step['agent']}: {step['execution_time_ms']} ms\n"
        timeline_str += f"|\nPipeline Finished\nTotal\n{_diag['execution_time_ms']} ms"
        perf_str += f"Total: {_diag['execution_time_ms']} ms"

        pipeline_logger.info(timeline_str)
        performance_logger.info(perf_str)
        logger.info(f"Pipeline execution finished. Status: {_diag['status']}. Total Time: {_diag['execution_time_ms']}ms")

        return self._build_response(prediction, weather_data, severity, risk_data, knowledge_record, _diag, advice)

    def _build_response(
        self,
        prediction: Optional[Dict],
        weather_data: Optional[Dict],
        severity: Optional[Dict],
        risk_data: Optional[Dict],
        knowledge_record: Optional[DiseaseRecord],  # Pydantic model serialized HERE
        diag: Dict,
        advice: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Assembles the final grouped response contract.
        This is the ONLY place where DiseaseRecord is converted to a dict.
        """
        return {
            "prediction": prediction,
            "environment": {
                "weather": weather_data,
                "risk": risk_data,
                "severity": severity
            },
            "knowledge": {
                "context": knowledge_record.model_dump() if knowledge_record else None,
                "source": "knowledge_base" if knowledge_record else None
            },
            "ai": {
                "advice": advice,
                "source": advice.get("source", "unknown") if advice else None
            },
            "diagnostics": diag
        }
