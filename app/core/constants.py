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

# LLM Token Limits
LLM_MAX_TOKENS_DEFAULT = 1000
LLM_MAX_TOKENS_DEV = 8000
LLM_MAX_TOKENS_PM = 3000
LLM_MAX_TOKENS_MARKETING_LANDING = 3000
LLM_MAX_TOKENS_MARKETING_SOCIAL = 1500
LLM_MAX_TOKENS_COMPLIANCE_FULL = 1000
LLM_MAX_TOKENS_COMPLIANCE_SHORT = 100
LLM_MAX_TOKENS_META_FIX = 4000
LLM_MAX_TOKENS_AUDITOR = 1500
LLM_MAX_TOKENS_QA_REFLECTION = 100

# System Paths & Fallbacks
JAVA_17_PATH = "/usr/lib/jvm/java-17-openjdk-amd64"
JAVA_JBR_PATH = "/home/ekalpa/ide/android-studio-panda4/jbr"
JAVA_DEFAULT_FALLBACK = "/usr/lib/jvm/default-java"

ANDROID_HOME_PATHS = [
    "~/Android/Sdk",
    "/usr/local/lib/android/sdk",
    "/home/ekalpa/Android/Sdk"
]

# Builder Config
GRADLE_BUILD_TIMEOUT_SEC = 600

# API Config
API_DEFAULT_PORT = 8000
API_DEFAULT_HOST = "0.0.0.0"

# Resource Paths
FRONTEND_DIR = "app/frontend"
FRONTEND_INDEX_HTML = "app/frontend/index.html"
LESSONS_LEARNED_FILE = "app/resources/lessons_learned.json"
GRADLE_TEMPLATE_DIR = "app/resources/gradle_template"
KMP_GOLDEN_TEMPLATE_DIR = "app/resources/kmp_golden_template"

# Package Defaults
DEFAULT_PACKAGE_PREFIX = "com.softwarefactory."
DEFAULT_APP_TITLE = "KMP Application"
