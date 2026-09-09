# Animated Domino UI Implementation Plan

## Goal
Completely replace the static linear stepper with a dynamic, beautifully animated Domino UI. This gives users a tangible, highly intuitive visual representation of the AI pipeline progress, where each agent's completion triggers the next action, much like falling dominoes.

## Proposed Changes

### 1. index.html
- Remove the old `<div class="stepper-container">`
- Add a new `<div class="domino-container" id="domino-container">` which will house the domino tiles.
- Each tile will represent a step: `Init`, `PM`, `PRD`, `Dev`, `QA`, `Review`, `Build`, `Done`.

### 2. css/styles.css
- Add rich, intuitive styles for `.domino-tile`. We will use nice gradients, rounded corners, and a slight 3D shadow to make them look like premium dominoes.
- Add CSS animations and transitions for the "falling" effect (`transform: rotateZ(75deg) translateX(20px); origin: bottom right;`).
- Add active states (glow effects) for the domino currently being worked on by the agent.

### 3. js/app.js
- Remove the old `updateStepper` logic.
- Introduce `updateDominos(activeStep)` logic to handle the state transitions.
- Connect to the backend's Server-Sent Events (SSE) stream endpoint (`/api/v1/stream`) to listen for real-time `domino_event_bus` updates. This allows the UI to instantly knock down a domino when an agent completes a task, rather than waiting for the generic status poller.
- Add logic so that when step N completes, it adds a CSS class `.falling` to domino N, which triggers the CSS animation.

## Verification
- Run the pipeline and ensure the dominoes look premium and that they fall correctly in sequence as the backend processes the tasks.
