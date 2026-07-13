"""OpenAI tool/function schemas for FinancingAssistantTools.

Each entry follows the OpenAI ``tools`` parameter format:
https://platform.openai.com/docs/guides/function-calling
"""

from __future__ import annotations

from typing import Any

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "extract_energy_bill_data",
            "description": (
                "Extract structured data from an energy bill image or PDF file. "
                "Call this tool whenever the user provides a file path to an energy bill, "
                "electricity invoice, or conta de energia (PDF, PNG, JPG, etc.). "
                "Returns the extracted fields and a list of any fields that are still missing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "Absolute or relative file-system path to the energy bill "
                            "image or PDF supplied by the user."
                        ),
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_energy_bill_data",
            "description": (
                "Merge manually supplied field values into a previously extracted energy bill DTO. "
                "Call this tool when extract_energy_bill_data returned a non-empty missing_fields "
                "list and the user has now provided the missing values. "
                "Only absent fields are updated; fields already present from OCR are preserved."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "extracted_bill_data": {
                        "type": "object",
                        "description": (
                            "The 'data' dict returned by extract_energy_bill_data or a previous "
                            "call to complete_energy_bill_data."
                        ),
                    },
                    "manual_values": {
                        "type": "object",
                        "description": (
                            "Key-value pairs with the missing field names and the values "
                            "provided by the user. "
                            "Numeric fields (monthly_consumption_kwh, monthly_cost_brl, "
                            "tariff_brl_per_kwh) must be supplied as strings "
                            "(e.g. '380,50' or '380.50'). "
                            "reference_month must be in YYYY-MM format."
                        ),
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["extracted_bill_data", "manual_values"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_financing_from_bill",
            "description": (
                "Run the full solar financing simulation pipeline from a complete energy bill DTO. "
                "Call this tool ONLY after: (a) all required fields are present "
                "(missing_fields is empty), AND (b) the user has explicitly confirmed "
                "they want to proceed with the simulation. "
                "After this tool returns a simulation_id AND an access_token, you MUST "
                "immediately call check_simulation_status with BOTH values to confirm the "
                "status before presenting results to the user. "
                "Returns status='missing_fields' if data is still incomplete, "
                "or status='error' if the simulation fails."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "extracted_bill_data": {
                        "type": "object",
                        "description": (
                            "The complete energy bill data dict "
                            "(from extract_energy_bill_data or complete_energy_bill_data)."
                        ),
                    },
                },
                "required": ["extracted_bill_data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_simulation_status",
            "description": (
                "Retrieve the current status of a previously created financing simulation. "
                "ALWAYS call this tool after simulate_financing_from_bill returns a "
                "simulation_id — pass both the returned simulation_id and access_token to "
                "confirm the official status before presenting any results to the user. "
                "Also call this tool when the user asks about the result or status of a "
                "simulation and provides a simulation ID (UUID). "
                "Returns the simulation status, solar project data, and financing offer "
                "if approved."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "simulation_id": {
                        "type": "string",
                        "description": (
                            "UUID of the simulation to look up, "
                            "as returned by simulate_financing_from_bill."
                        ),
                    },
                    "access_token": {
                        "type": "string",
                        "description": (
                            "The access_token returned by simulate_financing_from_bill for "
                            "this simulation. Required to read a simulation you just created."
                        ),
                    },
                },
                "required": ["simulation_id"],
            },
        },
    },
]
