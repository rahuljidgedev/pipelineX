#!/usr/bin/env bash
# =============================================================================
# run_pipelinex.sh – one‑click bootstrap & launch for the pipelineX project
#   • Activates the Poetry virtual‑env (equivalent to `poetry shell`)
#   • Installs / updates dependencies
#   • Exports your OpenAI API key *inside* the activated venv
#   • Starts the FastAPI server (Uvicorn)
#   • Optionally builds the Android debug APK
# =============================================================================
# Usage examples:
#   $ ./run_pipelinex.sh                # ► start only the web server (defaults to openai)
#   $ ./run_pipelinex.sh gemini         # ► start web server using Gemini API
#   $ ./run_pipelinex.sh gemini android # ► start web server using Gemini and build APK
# =============================================================================

PROVIDER="openai"
if [[ "$1" == "gemini" || "$1" == "openai" ]]; then
  PROVIDER="$1"
  shift
fi
export LLM_PROVIDER=$PROVIDER

# -------------------------------------------------------------------------
# 1️⃣ Project location – dynamic path resolution
# -------------------------------------------------------------------------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT" || { echo "❌ Cannot cd into $PROJECT_ROOT"; exit 1; }

# -------------------------------------------------------------------------
# 2️⃣ Ensure Poetry is installed (install it if missing)
# -------------------------------------------------------------------------
if ! command -v poetry >/dev/null 2>&1; then
  echo "⚙️ Poetry not found – installing via the official installer..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
fi

# -------------------------------------------------------------------------
# 3️⃣ (Re)create the virtual‑env and install dependencies
# -------------------------------------------------------------------------
echo "🔧 Configuring Poetry and cleaning old environments…"
poetry config virtualenvs.in-project true
poetry env remove --all 2>/dev/null || true

echo "🔒 Updating Poetry lock file…"
poetry lock

echo "🔧 Installing Python dependencies via Poetry…"
poetry install --no-interaction

# -------------------------------------------------------------------------
# 4️⃣ Activate the Poetry virtual‑environment (same as `poetry shell`)
# -------------------------------------------------------------------------
VENV_PATH=$(poetry env info --path 2>/dev/null || true)
if [[ -z "$VENV_PATH" ]]; then
  echo "⚠️ Could not locate Poetry venv – falling back to \`poetry shell\`."
  exec poetry shell "$0" "$@"
else
  # shellcheck source=/dev/null
  source "$VENV_PATH/bin/activate"
  echo "✅ Poetry venv activated: $VENV_PATH"
fi

# -------------------------------------------------------------------------
# 5️⃣ Load API keys from .env.local file
# -------------------------------------------------------------------------
if [[ -f ".env.local" ]]; then
  echo "🔑 Loading environment variables from .env.local..."
  set -a
  # shellcheck source=/dev/null
  source .env.local
  set +a
else
  echo "⚠️ No .env.local file found. Please create one with OPENAI_API_KEY and GEMINI_API_KEY."
fi

# -------------------------------------------------------------------------
# 6️⃣ Start the FastAPI server (Uvicorn)
# -------------------------------------------------------------------------
if [[ "$1" == "android" ]]; then
  echo "Starting FastAPI in the background on http://0.0.0.0:8000"
  poetry run python -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000 --log-level info &
  SERVER_PID=$!

  # -------------------------------------------------------------------------
  # 7️⃣ Build the Android debug APK
  # -------------------------------------------------------------------------
  echo "📱 Building Android debug APK – Gradle"
  ./gradlew clean :composeApp:assembleDebug
  APK_PATH="composeApp/build/outputs/apk/debug/composeApp-debug.apk"
  if [[ -f "$APK_PATH" ]]; then
    echo "✅ APK built successfully → $APK_PATH"
    echo "🔎 Install it with:"
    echo "    adb install -r $APK_PATH"
  else
    echo "⚠️ APK build failed – check the Gradle output above."
  fi

  # Keep the script alive while the background server runs
  wait $SERVER_PID
else
  echo "Starting FastAPI in the foreground on http://0.0.0.0:8000"
  echo "📋 Logs will appear below. Press Ctrl+C to stop."
  echo ""
  poetry run python -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000 --log-level info
fi

