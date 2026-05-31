"""Unit tests for TOOL_SCHEMAS — structure validation only, no OpenAI calls."""

from __future__ import annotations

from solar_financing_assistant.infrastructure.llm.tool_schemas import TOOL_SCHEMAS

_EXPECTED_NAMES = {
    "extract_energy_bill_data",
    "complete_energy_bill_data",
    "simulate_financing_from_bill",
    "check_simulation_status",
}


def test_tool_schemas_contains_four_tools() -> None:
    assert len(TOOL_SCHEMAS) == 4


def test_all_tools_have_type_function() -> None:
    for schema in TOOL_SCHEMAS:
        assert schema["type"] == "function", f"Expected 'function', got {schema['type']!r}"


def test_all_expected_tool_names_present() -> None:
    names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    assert names == _EXPECTED_NAMES


def test_each_tool_has_non_empty_description() -> None:
    for schema in TOOL_SCHEMAS:
        desc = schema["function"].get("description", "")
        assert isinstance(desc, str) and desc.strip(), (
            f"Tool {schema['function']['name']!r} has an empty description."
        )


def test_each_tool_has_parameters_object() -> None:
    for schema in TOOL_SCHEMAS:
        params = schema["function"].get("parameters", {})
        assert params.get("type") == "object", (
            f"Tool {schema['function']['name']!r} parameters must have type='object'."
        )
        assert "properties" in params, (
            f"Tool {schema['function']['name']!r} parameters must have 'properties'."
        )


def test_extract_energy_bill_data_requires_file_path() -> None:
    schema = next(s for s in TOOL_SCHEMAS if s["function"]["name"] == "extract_energy_bill_data")
    params = schema["function"]["parameters"]
    assert "file_path" in params["properties"]
    assert "file_path" in params.get("required", [])


def test_complete_energy_bill_data_requires_both_params() -> None:
    schema = next(s for s in TOOL_SCHEMAS if s["function"]["name"] == "complete_energy_bill_data")
    params = schema["function"]["parameters"]
    assert "extracted_bill_data" in params["properties"]
    assert "manual_values" in params["properties"]
    required = params.get("required", [])
    assert "extracted_bill_data" in required
    assert "manual_values" in required


def test_simulate_financing_requires_extracted_bill_data() -> None:
    schema = next(
        s for s in TOOL_SCHEMAS if s["function"]["name"] == "simulate_financing_from_bill"
    )
    params = schema["function"]["parameters"]
    assert "extracted_bill_data" in params["properties"]
    assert "extracted_bill_data" in params.get("required", [])


def test_check_simulation_status_requires_simulation_id() -> None:
    schema = next(s for s in TOOL_SCHEMAS if s["function"]["name"] == "check_simulation_status")
    params = schema["function"]["parameters"]
    assert "simulation_id" in params["properties"]
    assert "simulation_id" in params.get("required", [])
