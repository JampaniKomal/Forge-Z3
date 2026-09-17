"""
LLM Client for Neural Generation.
This wraps LiteLLM to support universal API integration (Gemini, Groq, OpenAI)
and strictly enforces our Pydantic Topologies using JSON schema prompts.
"""

import json

import litellm
from pydantic import ValidationError

from src.knowledge_base.physics import get_cve_map
from src.z3_engine.schema import Topology

litellm.set_verbose = False


class LLMGenerator:
    def __init__(self, model_name: str = "gemini/gemini-2.5-pro"):
        """
        model_name standardizes around LiteLLM syntax.
        Requires the appropriate API key environment variable (e.g., GEMINI_API_KEY).
        """
        self.model_name = model_name
        self.topology_schema = Topology.model_json_schema()
        self.cve_db = list(get_cve_map().keys())

        # Build detailed CVE reference for Tier 2
        cve_details = get_cve_map()
        cve_reference_lines = []
        for cve_id, cve_def in cve_details.items():
            cve_reference_lines.append(
                f"  - {cve_id}: port={cve_def.port}, "
                f"pre={cve_def.pre_privilege.value} → post={cve_def.post_privilege.value}, "
                f"type={cve_def.exploit_type.value}"
            )
        cve_reference = "\n".join(cve_reference_lines)

        self.system_prompt = (
            "You are a strict JSON formatter. Your ONLY job is to convert the user's "
            "explicit architectural plan into a JSON object.\n\n"
            'The output MUST be a single JSON object with exactly three arrays: "nodes", '
            '"edges", and "vulnerabilities".\n\n'
            "VALID CVE DATABASE — you may ONLY use these exact CVE IDs:\n"
            f"{cve_reference}\n\n"
            "EXAMPLE OUTPUT FORMAT:\n"
            "{\n"
            '  "nodes": [\n'
            '    {"node_id": 0, "name": "Attacker"},\n'
            '    {"node_id": 1, "name": "WebServer"}\n'
            "  ],\n"
            '  "edges": [\n'
            '    {"source_id": 0, "target_id": 1, "port": 8080}\n'
            "  ],\n"
            '  "vulnerabilities": [\n'
            '    {"node_id": 1, "cve_id": "CVE-2021-44228"}\n'
            "  ]\n"
            "}\n\n"
            "CRITICAL RULES:\n"
            "1. ONLY use CVE IDs from the list above. Any other CVE ID will be silently "
            "ignored by the verifier.\n"
            "2. Each CVE has a required port — the edge connecting to that node MUST "
            "use that exact port.\n"
            "3. If a CVE only gives USER privilege, you MUST also add a local privilege "
            "escalation CVE (port=0, pre=USER→post=ROOT) on that same node to achieve "
            "ROOT.\n"
            "4. Node 0 MUST ALWAYS be the Attacker.\n"
            "5. Map the user's exact plan into this JSON format.\n"
            "6. DO NOT output JSON schema definitions like $defs or $ref. Just output the "
            "raw data arrays.\n"
            "7. DO NOT output any markdown, markdown code blocks, or text outside the "
            "JSON object."
        )

    def upgrade_prompt(self, basic_prompt: str) -> str:
        """
        Tier 1: Chain of Thought Reasoning.
        Uses the LLM to map out the explicit physical connections in plain text,
        so Tier 2 doesn't have to think about spatial reasoning.
        """
        upgrade_system_prompt = (
            "You are a Cyber Range Architect. Your job is to translate a user's basic "
            "request into a highly explicit, strict mapping.\n\n"
            f"Available CVEs: {json.dumps(self.cve_db)}\n\n"
            "Rules for the mapping you must output:\n"
            "1. Explicitly list the Nodes. Node 0 MUST be the Attacker. Node 1 is "
            "usually the Target.\n"
            "2. Explicitly list the Edges. An Edge MUST connect the Attacker to the "
            "Target on the correct port if a network vulnerability is used.\n"
            "3. Explicitly list the Vulnerabilities, mapping them to the EXACT CVE ID "
            "from the list above, and assign it to the Target's Node ID.\n\n"
            "Output only the explicit mapping in plain text. Do not output JSON."
        )
        messages = [
            {"role": "system", "content": upgrade_system_prompt},
            {
                "role": "user",
                "content": f"Basic Request: {basic_prompt}\n\nProvide the explicit mapping.",
            },
        ]

        response = litellm.completion(model=self.model_name, messages=messages)
        return response.choices[0].message.content.strip()

    def generate_topology(
        self, user_prompt: str, previous_failures: list[str] | None = None
    ) -> Topology:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Design a topology for this scenario: {user_prompt}"},
        ]

        if previous_failures:
            error_msg = "Your previous attempts failed verification in the Z3 SMT solver due to:\n"
            for fail in previous_failures:
                error_msg += f"- {fail}\n"
            error_msg += "Please fix these logical/physical errors in your next JSON output."
            messages.append({"role": "user", "content": error_msg})

        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"},
        )

        raw_json = response.choices[0].message.content.strip()

        # Strip markdown code blocks if the LLM hallucinated them despite instructions
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]

        try:
            data = json.loads(raw_json)
            return Topology(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(
                f"LLM produced invalid JSON schema: {str(e)}\n\n"
                f"--- RAW OUTPUT FROM LLM ---\n{raw_json}\n---------------------------"
            ) from e
