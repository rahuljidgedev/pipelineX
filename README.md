# PipelineX 🚀

**Generative AI for Kotlin Multiplatform (KMP)**

PipelineX is an autonomous, multi-agent AI pipeline designed to generate, validate, and iteratively refine full Kotlin Multiplatform (KMP) mobile applications from a simple prompt.

## Overview

PipelineX uses a multi-stage AI workflow to bridge the gap between high-level requirements and working, compilable KMP code. The pipeline features:

1. **PM Agent**: Parses user prompts to generate comprehensive Product Requirements Documents (PRDs) and Job Requirement Contexts (JRC).
2. **DEV Agent**: Generates and injects custom KMP code (Compose Multiplatform) based on the PRD.
3. **QA/AST Validation**: Automatically runs a local Gradle build and a structural Abstract Syntax Tree (AST) checker to ensure the UI matches the required specifications.
4. **Iterative Refinement**: If the build or AST validation fails, the error logs are fed back into the DEV agent for an automated retry.
5. **Interactive Web UI**: Provides a clean interface for users to enter prompts, view real-time factory logs, and manually approve final builds.

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rahuljidgedev/pipelineX.git
   cd pipelineX
   ```

2. **Environment Variables:**
   Create a `.env` or `.env.local` file in the root directory and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   GITHUB_TOKEN=your_github_token # (Optional) for autonomous bug reporting
   ```

3. **Install Dependencies:**
   ```bash
   poetry install
   ```

4. **Run the Application:**
   ```bash
   ./run_pipelinex.sh
   ```
   The web UI will be accessible at `http://127.0.0.1:8000`.

## Architecture

- **Backend:** FastAPI (Python) handles the orchestration of the AI agents and the execution of background shell commands for Gradle compilation.
- **Frontend:** Vanilla JS and CSS for a responsive, dark-mode dashboard.
- **LLM Integration:** Supports both OpenAI and Google Gemini models.
- **Workspace:** Generated KMP applications are built inside the `workspace/apps/` directory.

## License

This project is licensed under the MIT License.
