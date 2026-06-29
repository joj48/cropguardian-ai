import os
import time
import datetime
import json
from typing import Dict, Any, Optional

from src.utils.logger import get_logger, pipeline_run_id_var
from src.services.knowledge_base.kb_manager import KnowledgeBaseManager
from src.services.knowledge_base.models import DiseaseRecord

logger = get_logger("adk_coordinator", "adk.log")
performance_logger = get_logger("performance", "performance.log")
pipeline_logger = get_logger("pipeline_runs", "pipeline_runs.log")

try:
    from google.adk import Agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

from agents.adk_workflow.tools import detect_disease_tool, analyze_severity_tool, generate_advice_tool, get_weather_tool, assess_risk_tool
from agents.coordinator_agent.coordinator_agent import CoordinatorAgent

try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from pydantic import BaseModel, Field

    class AdvisoryState(BaseModel):
        disease_data: Dict[str, Any] = Field(default_factory=dict)
        weather_data: Dict[str, Any] = Field(default_factory=dict)
        severity_data: Dict[str, Any] = Field(default_factory=dict)
        risk_data: Dict[str, Any] = Field(default_factory=dict)
        knowledge_context: Dict[str, Any] = Field(default_factory=dict)

except ImportError:
    pass


class ADKCoordinatorAgent:
    def __init__(self):
        self.legacy_coordinator = CoordinatorAgent()
        self.kb_manager = KnowledgeBaseManager()
        self.workflow_version = "v2.1-adk"

        if ADK_AVAILABLE:
            self.disease_agent = Agent(
                name="disease_agent",
                model="gemini-2.5-flash",
                instruction="You are a Disease Detection Agent. You must invoke the detect_disease_tool.",
                tools=[detect_disease_tool]
            )
            self.weather_agent = Agent(
                name="weather_agent",
                model="gemini-2.5-flash",
                instruction="You are a Weather Agent. You retrieve weather data for farm locations.",
                tools=[get_weather_tool]
            )
            self.severity_agent = Agent(
                name="severity_agent",
                model="gemini-2.5-flash",
                instruction="You are a Severity Agent. You assess disease severity based on the disease_class and confidence.",
                tools=[analyze_severity_tool]
            )
            self.risk_agent = Agent(
                name="risk_agent",
                model="gemini-2.5-flash",
                instruction="You are an Environmental Risk Agent. You assess the likelihood of disease spread based on weather data.",
                tools=[assess_risk_tool]
            )
            self.advisory_agent = Agent(
                name="advisory_agent",
                model="gemini-2.5-flash",
                instruction="You are an Advisory Agent. Read the context from the state and use the generate_advice_tool to generate agricultural advice.",
                tools=[generate_advice_tool],
                state_schema=AdvisoryState
            )

            logger.info("Initializing ADK InMemorySessionService.")
            self.session_service = InMemorySessionService()

    def process_image(self, image_path: str, location_input: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Executes the ADK multi-agent workflow.
        Produces a grouped response schema: prediction / environment / knowledge / ai / diagnostics.
        DiseaseRecord is kept as a Pydantic model internally and serialized only at _build_response().
        If ADK is unavailable or fails, falls back cleanly to the Legacy Coordinator,
        which independently owns its full response contract — no post-processing needed.
        """
        logger.info(f"Pipeline execution started. Workflow: Google ADK Workflow. Location: {location_input}")
        start_time = time.time()

        _diag = {
            "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "workflow_version": self.workflow_version,
            "workflow_engine": "google_adk",
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

        # ─── Early fallback: ADK unavailable ──────────────────────────────────
        # The Legacy Coordinator independently owns its full response contract.
        if not ADK_AVAILABLE or not os.getenv("GEMINI_API_KEY"):
            reason = "Missing GEMINI_API_KEY" if ADK_AVAILABLE else "google-adk package unavailable"
            logger.warning(f"ADK Workflow unavailable ({reason}). Executing mandatory fallback to Legacy Coordinator.")
            legacy_resp = self.legacy_coordinator.process_image(image_path, location_input, lat, lon)
            legacy_resp["diagnostics"]["warnings"].append(
                f"ADK Workflow initialization failed ({reason}) -> Switched to Legacy Coordinator."
            )
            return legacy_resp

        # ─── Internal state ────────────────────────────────────────────────────
        prediction_result: Optional[Dict] = None
        weather_data: Optional[Dict] = None
        severity_result: Optional[Dict] = None
        risk_data: Optional[Dict] = None
        knowledge_record: Optional[DiseaseRecord] = None  # Pydantic model, serialized at _build_response()

        try:
            # 1. Disease Agent Execution
            t0 = time.time()
            _diag["agent_trace"].append("DiseaseAgent")
            prediction_result = detect_disease_tool(image_path)
            t1 = time.time()
            if "error" in prediction_result:
                raise Exception(f"Disease detection failed: {prediction_result['error']}")

            _diag["execution_summary"].append({
                "agent": "DiseaseAgent", "status": "success",
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["successful_agents"] += 1
            disease_class = prediction_result["disease"]
            confidence = prediction_result["confidence"]

            # 2. Knowledge Base Retrieval
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
            prediction_result["crop"] = crop_val or "Unknown"
            logger.debug(f"Prediction crop resolved: {prediction_result['crop']}")

            # 3. Weather Agent Execution
            t0 = time.time()
            if location_input or (lat and lon):
                _diag["agent_trace"].append("WeatherAgent")
                weather_data = get_weather_tool(location_input, lat, lon)
                t1 = time.time()
                if weather_data.get("status") in ["unavailable", "timeout"] or "error" in weather_data:
                    status = weather_data.get("status", "failed")
                    if status == "unavailable": status = "failed"
                    _diag["agent_trace"][-1] = "WeatherAgent (Timeout)" if status == "timeout" else "WeatherAgent (Failed)"
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
                    _diag["execution_summary"].append({
                        "agent": "WeatherAgent", "status": "success",
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["successful_agents"] += 1

            # 4. Severity Agent Execution
            t0 = time.time()
            _diag["agent_trace"].append("SeverityAgent")
            severity_result = analyze_severity_tool(image_path, disease_class, confidence)
            t1 = time.time()
            if "error" in severity_result:
                _diag["status"] = "partial_success"
                _diag["pipeline_summary"]["overall_status"] = "partial_success"
                _diag["warnings"].append(f"Severity analysis failed: {severity_result['error']}")
                _diag["execution_summary"].append({
                    "agent": "SeverityAgent", "status": "failed", "reason": severity_result["error"],
                    "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                    "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                    "execution_time_ms": int((t1 - t0) * 1000)
                })
                _diag["pipeline_summary"]["failed_agents"] += 1
            else:
                _diag["execution_summary"].append({
                    "agent": "SeverityAgent", "status": "success",
                    "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                    "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                    "execution_time_ms": int((t1 - t0) * 1000)
                })
                _diag["pipeline_summary"]["successful_agents"] += 1

            # 5. Environmental Risk Agent Execution
            t0 = time.time()
            if weather_data:
                _diag["agent_trace"].append("EnvironmentalRiskAgent")
                risk_data = assess_risk_tool(disease_class, weather_data)
                t1 = time.time()

                if risk_data.get("status") == "skipped":
                    _diag["agent_trace"][-1] = "EnvironmentalRiskAgent (Skipped)"
                    _diag["execution_summary"].append({
                        "agent": "EnvironmentalRiskAgent", "status": "skipped",
                        "reason": risk_data.get("reason", "Weather unavailable"),
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["skipped_agents"] += 1
                elif "error" in risk_data:
                    _diag["agent_trace"][-1] = "EnvironmentalRiskAgent (Failed)"
                    _diag["warnings"].append(f"Risk assessment failed: {risk_data['error']}")
                    _diag["execution_summary"].append({
                        "agent": "EnvironmentalRiskAgent", "status": "failed", "reason": risk_data["error"],
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["failed_agents"] += 1
                else:
                    _diag["execution_summary"].append({
                        "agent": "EnvironmentalRiskAgent", "status": "success",
                        "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                        "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                        "execution_time_ms": int((t1 - t0) * 1000)
                    })
                    _diag["pipeline_summary"]["successful_agents"] += 1

            # 6. Advisory Agent Execution via ADK Runner
            # knowledge_record serialized to dict HERE for the ADK tool call payload
            knowledge_data = knowledge_record.model_dump() if knowledge_record else {}

            t0 = time.time()
            _diag["agent_trace"].append("AdvisoryAgent")

            run_id = pipeline_run_id_var.get() if pipeline_run_id_var.get() else "default_session"

            logger.info(f"Creating ADK Runner for advisory_agent. Session ID: {run_id}")
            runner = Runner(
                app_name="CropGuardian",
                agent=self.advisory_agent,
                session_service=self.session_service,
                auto_create_session=True
            )

            state_payload = {
                "disease_data": prediction_result if prediction_result else {},
                "weather_data": weather_data if weather_data else {},
                "severity_data": severity_result if severity_result else {},
                "risk_data": risk_data if risk_data else {},
                "knowledge_context": knowledge_data
            }

            logger.info(f"Invoking ADK Agent. Session reuse ID: {run_id}")
            prompt_text = (
                "Read the following context and execute the generate_advice_tool to produce the advisory report.\n"
                f"Context: {json.dumps(state_payload, indent=2)}"
            )
            events = runner.run(
                user_id="user_1",
                session_id=run_id,
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)]),
                state_delta=state_payload
            )

            advice_result = None
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            logger.info(f"ADK Event: Tool invocation detected: {part.function_call.name}")
                        if hasattr(part, "function_response") and part.function_response:
                            logger.info(f"ADK Event: Tool return detected: {part.function_response.name}")
                            try:
                                advice_result = part.function_response.response
                                if isinstance(advice_result, dict) and "generate_advice_tool_response" in advice_result:
                                    advice_result = advice_result["generate_advice_tool_response"]
                                logger.info("ADK Event: Successfully extracted JSON payload from FunctionResponse.")
                            except Exception as e:
                                logger.error(f"Failed to parse ADK FunctionResponse: {e}")
                                advice_result = {"error": f"Failed to parse output: {str(e)}"}

            t1 = time.time()
            logger.info(f"ADK Runner execution completed in {round(t1 - t0, 2)}s")

            if not advice_result:
                advice_result = {"error": "No output from ADK Runner"}

            if "error" in advice_result:
                raise Exception(f"ADK Runner failed to generate advice: {advice_result['error']}")

            _diag["execution_summary"].append({
                "agent": "AdvisoryAgent", "status": "success",
                "started_at": datetime.datetime.fromtimestamp(t0).isoformat(),
                "finished_at": datetime.datetime.fromtimestamp(t1).isoformat(),
                "execution_time_ms": int((t1 - t0) * 1000)
            })
            _diag["pipeline_summary"]["successful_agents"] += 1

            _diag["execution_time_ms"] = int((time.time() - start_time) * 1000)
            _diag["pipeline_summary"]["total_execution_time_ms"] = _diag["execution_time_ms"]

            self._log_timeline(_diag)
            logger.info(f"Pipeline execution finished. Status: {_diag['status']}. Total Time: {_diag['execution_time_ms']}ms")

            return self._build_response(prediction_result, weather_data, severity_result, risk_data, knowledge_record, _diag, advice_result)

        except Exception as e:
            # Mandatory fallback: The Legacy Coordinator independently owns its full response contract.
            # No post-processing or knowledge injection needed — it produces the correct schema itself.
            logger.error(f"ADK Workflow execution failed: {e}. Executing mandatory fallback.", exc_info=True)
            legacy_resp = self.legacy_coordinator.process_image(image_path, location_input, lat, lon)
            legacy_resp["diagnostics"]["warnings"].append(
                f"ADK Workflow failed ({e}) -> Switched to Legacy Coordinator."
            )
            return legacy_resp

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

    def _log_timeline(self, diag: Dict) -> None:
        """Builds and logs the ASCII pipeline timeline."""
        timeline_str = f"\n{diag['timestamp']}\nPipeline Started\n|\n"
        perf_str = "Run Summary:\n"

        for idx, step in enumerate(diag["execution_summary"]):
            timeline_str += f"{step['agent']}\n{step['execution_time_ms']} ms\n"
            if step["status"] != "success":
                timeline_str += f"Status: {step['status']}\n"
            if idx < len(diag["execution_summary"]) - 1:
                timeline_str += "|\n"
            perf_str += f"{step['agent']}: {step['execution_time_ms']} ms\n"

        timeline_str += f"|\nPipeline Finished\nTotal\n{diag['execution_time_ms']} ms"
        perf_str += f"Total: {diag['execution_time_ms']} ms"

        pipeline_logger.info(timeline_str)
        performance_logger.info(perf_str)
