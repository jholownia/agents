# Three-Layer Scoping

The kb plugin is *one* of three persistence layers available to an agent. The right home for a piece of information depends on **how durable it is** and **who it's about**, not on whether it feels "personal" or "project".

## The axis: durable fact vs ephemeral state

| What | Where |
|---|---|
| User preferences about agent behaviour ("address me as bro", "I prefer rebase", "use terse output") | Claude's auto-memory |
| Short-lived project state (current task, last error seen, in-progress debugging) | Claude's auto-memory |
| Normative workflow rules ("don't push to master", "tests must hit a real DB") | `CLAUDE.md` / `AGENTS.md` (project or user scope) |
| Durable facts — project, domain, codebase, **or personal-life** | KB `notes/` via `kb remember` |
| Decisions, runbook material, longer-form facts | KB `inbox/` → canonical pages via `kb stage` + `kb-dream` |
| URL pointers to read later | KB `inbox/` via `kb stage --url` |
| Project TODOs that should survive sessions | KB `inbox/` via `kb stage --kind followup` |

## Litmus test

Would re-deriving this fact require meaningful work — grep, ask the user, synthesise across sources?

- **Yes** → KB. The cost of asking again is real.
- **No, trivial to re-ask** → auto-memory. Saving it costs more than re-asking.
- **Only relevant to the current session** → auto-memory (or nothing).

## Personal vs project KBs

The "personal vs project" axis is about *which KB* a fact lands in, not whether it belongs in any KB:

- If the user has a personal `user-kb` *and* one or more project KBs, route by content. Personal-life facts ("My birthday is 15 November", "Mum's email is …", "Dentist appointment cadence") → personal KB. Project facts ("Customer A12 wants weekly reports", "Nightly job runs at 02:00 UTC") → project KB.
- If only a project KB is registered, prefer auto-memory for personal facts. Don't misfile personal data into a project KB.

## Explicit invocation overrides the heuristic

If the user types `/remember`, `kb remember ...`, `kb stage ...`, or otherwise explicitly invokes a KB skill or command, honour the routing they chose. The agent's job is to write what was asked, not to second-guess.

## What never goes in a KB

- Secrets, credentials, tokens.
- Sensitive personal data (SSN, financial, medical records). Non-sensitive personal facts (birthdays, contacts, addresses) are fine in a personal KB.
- Transcripts and raw conversation dumps (stage as inbox material instead, let `kb-dream` synthesise).
