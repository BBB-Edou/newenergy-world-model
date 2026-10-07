"""L2 ScenarioData extraction, building, validation and CSV export."""

from .builder import ScenarioBuildError, build_scenario_data, parse_scenario_value
from .csv_exporter import export_scenario_csv
from .extractor import ScenarioDataExtractor
from .interaction import apply_scenario_answers, generate_scenario_questions
from .markdown_tables import MarkdownTable, detect_markdown_tables, is_scenario_candidate, scenario_candidates
from .schema import BindingValidationSummary, DataManifest, ScenarioData, ScenarioExtraction, ScenarioInputBinding, ScenarioSource, ScenarioUpdateResult, TimeAlignment, UnitAlignment
from .validator import DEFAULT_REQUIRED_VARIABLES, parse_time_step, validate_scenario_data

__all__ = [
    "BindingValidationSummary",
    "DEFAULT_REQUIRED_VARIABLES",
    "DataManifest",
    "MarkdownTable",
    "ScenarioBuildError",
    "ScenarioData",
    "ScenarioDataExtractor",
    "ScenarioExtraction",
    "ScenarioInputBinding",
    "ScenarioSource",
    "ScenarioUpdateResult",
    "TimeAlignment",
    "UnitAlignment",
    "apply_scenario_answers",
    "build_scenario_data",
    "detect_markdown_tables",
    "export_scenario_csv",
    "generate_scenario_questions",
    "is_scenario_candidate",
    "parse_scenario_value",
    "parse_time_step",
    "scenario_candidates",
    "validate_scenario_data",
]