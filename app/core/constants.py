from enum import Enum

class PipelineMode(str, Enum):
    GREENFIELD = "greenfield"
    MAINTENANCE = "maintenance"

MAX_QA_ATTEMPTS = 4
MAX_AST_ATTEMPTS = 4
MAX_AUDITOR_ATTEMPTS = 10
