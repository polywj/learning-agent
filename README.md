# Learning Workspace

English | [中文](README.zh.md)

A tutoring workspace for learning a subject of your choice. Add study materials
(PDF, PPTX, and more) to `materials/` for the AI tutor to explain and quiz you
on, or ask about a topic directly. Progress is tracked in `progress.md`.

- **This file** — how to set up and use the workspace (for you, the learner).
- **`AGENTS.md`** — the agent's rulebook: tutoring style, session choreography,
  and environment notes.

You can start with a one-off question, quiz, or material ingestion, and set up a
learner profile and curriculum whenever you like. You can also adjust the
tutoring behavior in `AGENTS.md`.

## Prerequisites

| Requirement | Why |
|---|---|
| **Node.js** (includes `npx`) | Runs the DSH launch command. |
| **DeepSeek Harness (DSH)** — `npx @deepseek-ai/dsh web`; it launches the GUI in your web browser automatically. | Runs the agent and the web interface. |
| **Python 3.10 – 3.14** | MarkItDown (the document-to-Markdown converter) requires `>=3.10, <3.15`. This workspace's venv uses 3.14. |
| **PowerPoint** (desktop, Windows; only for PPT/PPTX ingestion) | Renders presentation slides to images during ingest. |

## Setup

### 1. Configure models (DSH web GUI settings)

Under **Models** in the GUI settings, declare:

- the **tutor model** — your main agent;
- **subagent models** — routes the agent can delegate to (it discovers them
  automatically and defaults to `deepseek-flash` for image analysis; see the
  `ingest` skill).

For the model that will read page/slide images, make sure **Image** is checked
under its **Input types** (alongside Text). Without it, image analysis fails
with *"model does not declare image input"*.

### 2. Python venv (`.venv/`)

The agent sets this up on request — just say *"set up the venv"*. To do it
manually instead:

```powershell
python -m venv .venv
& .venv\Scripts\python.exe -m pip install "markitdown[all]" pymupdf comtypes
```

Tested with: Python 3.14, markitdown 0.1.9, PyMuPDF 2.0, comtypes 1.4.17.

## Quick start

Start with whichever is useful:

- **Ask or learn:** *"Teach me [topic]"*
- **Quiz:** *"Quiz me on [topic]."*
- **Ingest:** Drop a file into `materials/` and tell the agent *"ingest
  <file>"*. It converts the document to Markdown under `materials/md/`; PDF and
  PowerPoint files also get page/slide images. The agent analyzes generated
  images when an image-capable model is available and gives you an orientation
  summary.

For a personalized, ongoing plan, ask the agent to help set one up.
It will briefly ask about your subject, goals, experience, and preferences,
then propose a manageable curriculum. Once you agree, it adds your profile,
goals, and curriculum to `progress.md`. You can also set up a plan after
ingesting materials or taking a quiz.

## Modes

| Mode | What it is |
|---|---|
| **Teach me X** | Structured explanation with comprehension checks woven in; end with an explain-back. |
| **Quiz me** | Test understanding on the requested topic or ingested materials; when available, adapt to your agreed curriculum. Follows the `quiz-me` skill. |
| **Deep dive** | Explore an advanced topic, trade-off, design decision, or failure case. |
| **Review** | Recap `progress.md`, revisit weak spots, spaced repetition of older topics. |
| **Ingest** | Convert and index new training materials — the `ingest` skill — then offer a short orientation summary of what they cover. |
| **Free chat** | Ad-hoc Q&A; the tutoring principles in `AGENTS.md` still apply. |

If the mode is unclear, just say what you want — the agent will suggest one.

## Directory layout

```
materials/          # original training files as dropped (PDF, PPTX, DOCX, ...) — read-only, never modify
materials/md/       # Markdown conversions, mirroring source filenames (+ <name>_media/ page images)
notes/              # session summaries and concept notes
tools/              # conversion & workspace utility scripts (run with the .venv; see AGENTS.md)
.venv/              # workspace Python virtualenv
.agents/            # workspace skills the agent loads on demand
progress.md         # optional learner profile, goals, curriculum, materials, quiz and session logs (format: progress-log skill)
AGENTS.md           # agent rulebook
README.md           # this file
README.zh.md        # this file in Chinese (中文版)
```

## License

This project is licensed under the GNU Affero General Public License v3.0
(AGPL-3.0). See [LICENSE](LICENSE).
