---
name: illustrate
description: Create a static SVG illustration to explain a concept. Use for "illustrate", "draw a diagram", "画图" or "图解说明", or when a diagram would help a tutoring explanation.
whenToUse: Load when the learner requests a static illustration or a tutoring explanation needs one.
---

# Illustrate

Make a clear, accurate static diagram suited to the learner and the concept.

## Workflow

1. **Frame and choose a format.** Identify the concept and what the illustration should clarify; ask only if the request is unclear. Use hand-written SVG for simple diagrams, Mermaid for medium-complexity diagrams, and PlantUML when precise sequence diagrams, state machines, or hardware timing waveforms are a better fit. Choose based on the diagram's needs rather than complexity alone. Ground labels and values in the learner's materials or reliable sources; label invented examples as illustrative.
2. **Check rendering options.** Reuse available tools before proposing installations.
   * **SVG:** Write SVG directly; no diagram renderer is needed.
   * **Mermaid:** A browser can render Mermaid to SVG, but it needs the Mermaid JavaScript library and a way to run it and extract the result. Use an available local library and browser, or, for non-sensitive diagrams, offer to load the library from a trusted CDN. The Mermaid `render` API returns an SVG string; save that result or extract the rendered SVG. Do not assume the chat GUI renders Mermaid or that a browser alone includes the library. If these options are unavailable, offer an appropriate local alternative.
   * **PlantUML:** Check for Java, a usable PlantUML JAR, and any renderer dependencies needed for the chosen diagram, such as Graphviz. If missing, offer to install the missing tools and download the JAR from an official source into the tools/ directory. Proceed only with the learner's approval. Render to SVG locally. If the learner declines installation, offer a public service such as Kroki.io or the official PlantUML server for a non-sensitive diagram; explain that the diagram source is sent to that service, and send it only with explicit approval. If online rendering is declined or unsuitable, offer a local alternative such as SVG.
3. **Create and verify.** Create `illustrations/` if needed and save a descriptive, kebab-case `.svg` there. Do not overwrite an existing illustration without approval. Verify the file is valid SVG, contains the intended diagram rather than a renderer error, and is readable and self-contained when opened as an image. If visual inspection is available, check for clipped labels and layout problems; otherwise state that the visual layout was not verified. Correct any problems before delivery.
4. **Present.** Embed the saved SVG in the chat response using Markdown image syntax, with descriptive alt text.

## Guardrails

- Never send sensitive content or material-derived diagram source to a third-party service. Use local trusted rendering for sensitive content, including the Mermaid library.
- If an illustration accompanies a learning session, follow that session's progress and tutoring rules. A standalone illustration does not by itself require a progress entry or quiz.
- Use the simplest diagram that communicates the idea, and avoid executable scripts or external resources in the saved SVG.
