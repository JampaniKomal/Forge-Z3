import pytest
from pydantic import ValidationError

from src.knowledge_base.physics import get_cve_map, load_knowledge_base
from src.knowledge_base.schema import CVEDefinition, ExploitType, PrivilegeLevel


def test_load_knowledge_base():
    """Test that the real cve_database.json parses without errors."""
    kb = load_knowledge_base()
    assert len(kb.cves) == 12

    cve_map = get_cve_map()
    assert "CVE-2021-44228" in cve_map
    assert cve_map["CVE-2021-44228"].post_privilege == PrivilegeLevel.ROOT

def test_pydantic_validation_logic():
    """Test that Pydantic properly blocks invalid CVE definitions."""

    # Valid definition
    valid = CVEDefinition(
        cve_id="TEST-1",
        description="Test",
        software_target="Test",
        port=80,
        exploit_type=ExploitType.RCE,
        pre_privilege=PrivilegeLevel.NETWORK_ACCESS,
        post_privilege=PrivilegeLevel.ROOT
    )
    assert valid.cve_id == "TEST-1"

    # Invalid: ROOT -> ROOT (caught by check_escalation)
    with pytest.raises(ValidationError) as exc_info:
        CVEDefinition(
            cve_id="TEST-2",
            description="Test",
            software_target="Test",
            port=80,
            exploit_type=ExploitType.RCE,
            pre_privilege=PrivilegeLevel.ROOT,
            post_privilege=PrivilegeLevel.ROOT
        )
    assert "pre_privilege cannot be ROOT" in str(exc_info.value)

    # Invalid: Negative port
    with pytest.raises(ValidationError):
        CVEDefinition(
            cve_id="TEST-3",
            description="Test",
            software_target="Test",
            port=-1,
            exploit_type=ExploitType.RCE,
            pre_privilege=PrivilegeLevel.NETWORK_ACCESS,
            post_privilege=PrivilegeLevel.ROOT
        )
