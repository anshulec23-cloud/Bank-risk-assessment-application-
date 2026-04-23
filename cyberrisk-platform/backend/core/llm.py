import httpx
import re
from core.config import settings


def _extract_prompt_value(prompt: str, label: str, default: str = "Unknown") -> str:
    match = re.search(rf"{re.escape(label)}\s*:?\s*(.+)", prompt, re.IGNORECASE)
    if not match:
        return default
    return match.group(1).splitlines()[0].split("|")[0].strip()


def _demo_nist_report(prompt: str) -> str:
    attack_type = _extract_prompt_value(prompt, "Attack Type", "Unknown")
    severity = _extract_prompt_value(prompt, "Severity", "LOW")
    device_id = _extract_prompt_value(prompt, "Device ID", "Unknown")
    location = _extract_prompt_value(prompt, "Location", "Unspecified facility")
    exposure = _extract_prompt_value(prompt, "Total Exposure", "TBD")

    return f"""1. INCIDENT SUMMARY
An anomalous ICS event affecting {device_id} at {location} has been classified as {attack_type} with {severity} severity. Initial triage indicates the event is credible and should be handled as an active cyber-physical security incident.

2. INDICATORS OF COMPROMISE
Observed indicators include abnormal telemetry behavior, an elevated anomaly score, and a rule-based classification consistent with {attack_type}. Analysts should preserve the triggering telemetry, broker logs, and isolation events for forensic validation.

3. IMPACT ASSESSMENT
The incident may disrupt operational continuity for the affected facility and increase the likelihood of service degradation or unsafe process conditions. Current financial exposure from the event is noted in the prompt context as {exposure}.

4. CONTAINMENT ACTIONS TAKEN
Immediate containment should include validating whether {device_id} has been isolated, restricting control-plane access, and confirming telemetry integrity. Operations and security teams should maintain heightened monitoring until readings stabilize.

5. RECOMMENDED NEXT STEPS
Perform root-cause analysis, verify device firmware and network paths, and review adjacent assets for related indicators. Prepare stakeholder communications, update the incident record, and confirm whether manual failover or maintenance actions are required.

6. REGULATORY COMPLIANCE NOTES (NERC CIP / IEC 62443)
Document the detection timeline, response actions, and system impact in a format suitable for audit review under NERC CIP and IEC 62443 control expectations. If customer, grid, or safety obligations are affected, compliance and legal teams should assess reporting thresholds promptly."""


def _demo_credit_brief(prompt: str) -> str:
    attack_type = _extract_prompt_value(prompt, "Attack Type", "Unknown")
    severity = _extract_prompt_value(prompt, "Severity", "LOW")
    exposure = _extract_prompt_value(prompt, "Total Financial Exposure", "an unconfirmed amount")
    facility_type = _extract_prompt_value(prompt, "Facility Type", "industrial facility")
    risk_flag = _extract_prompt_value(prompt, "Credit Risk Flag", "ELEVATED")

    return (
        f"A {attack_type} incident with {severity} severity has been detected at a financed {facility_type}, with current estimated exposure of {exposure}. "
        f"The event supports a {risk_flag} credit posture until operational stability and control integrity are revalidated.\n\n"
        f"From a banking perspective, the primary concern is temporary pressure on cash flow, operating margins, and debt-service coverage if downtime extends or remediation costs escalate. "
        "Lenders should monitor business interruption duration, management responsiveness, and any knock-on effects on contractual performance or regulatory obligations.\n\n"
        "Recommended actions include heightened account monitoring, direct borrower outreach, and a targeted covenant review focused on liquidity, reporting, and resilience commitments. "
        "If the borrower demonstrates rapid containment and recovery, the exposure may remain manageable within normal portfolio surveillance."
    )


async def llm_generate(prompt: str, system: str = "") -> str:
    """
    Direct async call to Ollama /api/generate endpoint.
    Returns the generated text string.
    """
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as e:
            # Fallback: return a templated response so pipeline doesn't break
            return f"[LLM unavailable: {e}] — Rule-based report generated."


def llm_generate_sync(prompt: str, system: str = "") -> str:
    """Synchronous wrapper — used inside LangGraph nodes."""
    import asyncio
    lowered = prompt.lower()

    if settings.DEMO_MODE:
        if "nist" in lowered:
            return _demo_nist_report(prompt)
        if "credit risk" in lowered or "bank" in lowered:
            return _demo_credit_brief(prompt)

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If inside an async context (e.g. FastAPI), use a thread.
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, llm_generate(prompt, system))
                return future.result()

        return asyncio.run(llm_generate(prompt, system))
    except Exception as e:
        return f"[LLM error: {e}]"
