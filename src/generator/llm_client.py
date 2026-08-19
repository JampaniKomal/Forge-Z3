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

        self.system_prompt = f"""
        You are an expert Cyber Range Infrastructure architect.
        Your job is to design a network topology that satisfies the user's attack path requirements.
        
        CRITICAL RULES:
        1. Node 0 MUST ALWAYS be the Attacker.
        2. You must output valid JSON exactly matching this schema:
        {json.dumps(self.topology_schema, indent=2)}
        
        3. You may ONLY use the following CVE IDs for vulnerabilities:
        {json.dumps(self.cve_db, indent=2)}
        
        4. If a CVE requires NETWORK_ACCESS, ensure there is an Edge routing the Attacker to the target's specific Port.
        5. DO NOT output any markdown, markdown code blocks, or text outside the JSON object.
        """

    def upgrade_prompt(self, basic_prompt: str) -> str:
        """
        Tier 1: Chain of Thought Reasoning.
        Uses the LLM to map out the explicit physical connections in plain text,
        so Tier 2 doesn't have to think about spatial reasoning.
        """
        upgrade_system_prompt = f"""
        You are a Cyber Range Architect. Your job is to translate a user's basic request into a highly explicit, strict mapping.
        
        Available CVEs: {json.dumps(self.cve_db)}
        
        Rules for the mapping you must output:
        1. Explicitly list the Nodes. Node 0 MUST be the Attacker. Node 1 is usually the Target.
        2. Explicitly list the Edges. An Edge MUST connect the Attacker to the Target on the correct port if a network vulnerability is used.
        3. Explicitly list the Vulnerabilities, mapping them to the EXACT CVE ID from the list above, and assign it to the Target's Node ID.
        
        Output only the explicit mapping in plain text. Do not output JSON.
        """
        messages = [
            {"role": "system", "content": upgrade_system_prompt},
            {"role": "user", "content": f"Basic Request: {basic_prompt}\n\nProvide the explicit mapping."}
        ]
        
        response = litellm.completion(
            model=self.model_name,
            messages=messages
        )
        return response.choices[0].message.content.strip()

    def generate_topology(self, user_prompt: str, previous_failures: list[str] | None = None) -> Topology:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Design a topology for this scenario: {user_prompt}"}
        ]

        if previous_failures:
            error_msg = "Your previous attempts failed verification in the Z3 SMT solver due to:\n"
            for fail in previous_failures:
                error_msg += f"- {fail}\n"
            error_msg += "Please fix these logical/physical errors in your next JSON output."
            messages.append({"role": "user", "content": error_msg})

        import os
        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"}
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
            raise ValueError(f"LLM produced invalid JSON schema: {str(e)}\n\n--- RAW OUTPUT FROM LLM ---\n{raw_json}\n---------------------------")
