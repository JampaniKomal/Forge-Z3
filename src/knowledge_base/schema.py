"""
Pydantic schemas for the Forge-Z3 CVE Knowledge Base.

This defines the rigorous structure required for any vulnerability
to be reasoned about by the Z3 SMT solver.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PrivilegeLevel(str, Enum):
    """
    Defines the levels of access an attacker can have or gain.
    These map directly to Datalog states in the Z3 engine.
    """
    NONE = "NONE"
    NETWORK_ACCESS = "NETWORK_ACCESS"  # Can reach the port over the network
    USER = "USER"                      # Has low-privilege shell/execution
    ROOT = "ROOT"                      # Has full administrative control


class ExploitType(str, Enum):
    """Categorizes the nature of the vulnerability."""
    RCE = "RCE"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    INFO_DISCLOSURE = "INFO_DISCLOSURE"
    AUTHENTICATION_BYPASS = "AUTHENTICATION_BYPASS"


class CVEDefinition(BaseModel):
    """
    A mathematical model of a vulnerability, defining its prerequisites
    and post-exploitation state changes (the 'physics' of the attack).
    """
    cve_id: str = Field(..., description="The unique CVE identifier (or WEAK_CREDS)")
    description: str = Field(..., description="Brief description of the vulnerability")
    software_target: str = Field(..., description="The service or software affected")
    port: int = Field(..., description="The default network port this service runs on", ge=0, le=65535)
    
    exploit_type: ExploitType
    
    pre_privilege: PrivilegeLevel = Field(
        ..., 
        description="The minimum privilege required *before* the exploit can be triggered."
    )
    post_privilege: PrivilegeLevel = Field(
        ..., 
        description="The privilege gained *after* successful exploitation."
    )

    @field_validator("post_privilege")
    @classmethod
    def check_escalation(cls, post: PrivilegeLevel, info) -> PrivilegeLevel:
        """Ensure that the vulnerability actually escalates privileges."""
        pre = info.data.get("pre_privilege")
        if pre and post:
            # We enforce that ROOT cannot be a pre-privilege (no point escalating from ROOT)
            if pre == PrivilegeLevel.ROOT:
                raise ValueError(f"pre_privilege cannot be ROOT for {info.data.get('cve_id')}")
            
            # If pre == post, it must be something like Lateral Movement (e.g. Network -> Network on a new host)
            # For a single host, it usually implies Info Disclosure. We allow it, but flag it as suspicious if it's supposed to be RCE.
            if pre == post and info.data.get("exploit_type") in [ExploitType.RCE, ExploitType.PRIVILEGE_ESCALATION]:
                raise ValueError(f"RCE/PrivEsc must result in higher privilege for {info.data.get('cve_id')}")
        return post


class KnowledgeBase(BaseModel):
    """The root schema for the cve_database.json file."""
    cves: List[CVEDefinition]

    @field_validator("cves")
    @classmethod
    def check_unique_cves(cls, cves: List[CVEDefinition]) -> List[CVEDefinition]:
        """Ensure there are no duplicate CVE IDs in the database."""
        seen = set()
        for cve in cves:
            if cve.cve_id in seen:
                raise ValueError(f"Duplicate CVE ID found: {cve.cve_id}")
            seen.add(cve.cve_id)
        return cves
