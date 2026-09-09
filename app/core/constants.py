from enum import Enum

class PipelineMode(str, Enum):
    GREENFIELD = "greenfield"
    MAINTENANCE = "maintenance"
