from enum import Enum

class PipelineMode(str, Enum):
    GREENFIELD = "greenfield"
    MAINTENANCE = "maintenance"

MAX_QA_ATTEMPTS = 4
MAX_AST_ATTEMPTS = 4
MAX_AUDITOR_ATTEMPTS = 10

# Models
DEFAULT_MODEL_SMART = 'gpt-4o'
DEFAULT_MODEL_FAST = 'gpt-4o-mini'

# Paths
WORKSPACE_DIR = 'workspace'
