---
name: progress-log
description: progress.md format and update conventions for the learner's goals, curriculum, study materials, quizzes, and sessions.
whenToUse: Load before creating or editing progress.md for learning activity.
---

# progress.md format

```markdown
# Learning progress
## Learner profile

## Goals

## Curriculum
| Topic | Status (not started / learning / proficient) | Last touched | Gaps / notes |
|---|---|---|---|

## Materials
| Material | Topics covered | Useful sections / figures |
|---|---|---|

## Quiz log
| Date | Topic | Result & notes |
|---|---|---|

## Session log
```

Keep it concise and learning-focused; record only learning-relevant profile details. Create `progress.md` on the first quiz or ingestion if it does not exist. Before setup is agreed, add each activity to its relevant section (Quiz log or Materials), preserving all earlier entries; leave Learner profile, Goals, Curriculum, and unrelated sections unpopulated. After the learner agrees to setup, record their profile, goals, and curriculum rather than proposals, and preserve the existing activity history. The materials index tracks materials and where useful content appears, not conversion details; the session log records learning events only after setup. Update after every quiz or review session when the file exists. The learner is the owner — propose meaningful edits and respect their decisions.
