---
name: demonstrate
description: Build an interactive single-file HTML demo in demos/ that illustrates a concept with live simulation, concept toggles, and material-grounded numbers.
whenToUse: Load when the learner asks to see a concept demonstrated or visualized (e.g. "show me X", "demonstrate X", "演示 X", "给我看 X").
---

# Demonstrate

Turn a concept into a very realistic, interactive visual demo (ideally 3D) the learner can poke — not a canned animation.

## Workflow

1. **Frame the story first.** Confirm the concept(s) to show and the comparisons the demo must offer (A/B toggles) — proceed directly if the request is clear, and only ask if genuinely ambiguous. Keep one concept family per demo. Decide which numbers come from ingested materials (cite slide/page in the demo header or captions) and which are illustrative. If no reference materials are in context, state that standard industry/textbook values are used.
2. **Build** a single self-contained HTML file in `demos/` (kebab-case name, e.g., `demos/ctle-peaking.html`).
   * **3D (preferred):** Aim for a very realistic 3D scene using ES modules with a pinned-version CDN `<script type="importmap">` covering both `three` and `three/addons/` (needed for `OrbitControls`). Note the internet requirement (and `python -m http.server` fallback if `file://` blocks modules) in an HTML comment at the top.
   * **2D / Offline:** Use dependency-free HTML5 `<canvas>` when the concept is inherently 2D (waveforms, eye diagrams, constellation plots) or when offline portability is requested.
3. **Simulate, don't tween.** Compute the behavior live from underlying equations/state — whatever the concept — so every control genuinely responds. Clamp frame `dt` (e.g., `<= 0.05s`) so tab-switching cannot destabilize the simulation. Keep the model physically honest; where you must exaggerate scale/time for visibility, label it `"illustrative"` in the UI, while material-grounded values stay exact.
4. **Interaction defaults:**
   * Boot playing; start with the simplest baseline when appropriate, then use impairments to make the phenomenon visible.
   * A toggle per impairment/concept (each toggle is a thought experiment).
   * Parameter sliders with live numeric readouts and units (e.g., `dB`, `UI`, `ps`).
   * Play / Pause / Simulation speed controls.
   * `OrbitControls` with damping for 3D scenes (plus a "Reset Camera" button), with responsive `resize` handling so controls never clip the canvas.
   * Live captions/annotations that name the phenomenon as it happens, and a clear color legend.
   * Make the physics visible in the scene itself (e.g., draw the live waveform along the signal path; color by phenomenon), and add lab-style instruments where they fit (scopes, TDR, eye) rather than relying on captions alone.
5. **Verify before delivering:**
   * Run a syntax check on inline JS (extract `<script type="module">` blocks to a `.mjs` file before running `node --check`).
   * Verify the exact pinned CDN module URLs imported (not just directory prefixes like `three/addons/`) resolve (HTTP 200) via `web_fetch`.
   * Verify the rendered demo with a screenshot when a screenshot tool and vision-capable model are available.
   * Invite the learner to report any visual or WebGL rendering issues.
6. **Deliver** with a short guided tour that starts with the simplest first principles (such as an ideal baseline when appropriate) and progressively introduces complexity. Explain what to watch, which toggle A/Bs which concept, and where the numbers come from.

## Guardrails
* Demo creation is a workspace task, not a learning session: do not log it in `progress.md`, and do not append a quiz unless the learner asks.
* Keep CSS and JS inline inside the single `.html` file; do not generate external `.css` or `.js` assets.
