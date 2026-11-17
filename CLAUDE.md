# CLAUDE.md - Global Project Continuity Rules

## Desktop Commander MCP Initialization

When starting a project session, prioritize using the Desktop Commander MCP tool to access and operate directly on the project workspace.

1. Check whether the Desktop Commander MCP tool is available.
2. If available, use it to inspect the workspace, read `HANDOFF.md`, examine project files, and perform the required work.
3. If unavailable, do not immediately assume the tool is unsupported or permanently unavailable. It may still be initializing.
4. Wait approximately 10-20 seconds, refresh or reload the available MCP tools using the supported mechanism, and check again.
5. Repeat this process until Desktop Commander becomes operational. Use a reasonable retry interval and continue retrying while initialization appears to be in progress.
6. If repeated attempts indicate a persistent failure, report the specific issue rather than retrying indefinitely. Use another available workspace-access method only when appropriate and permitted.

**Priority:** Prefer Desktop Commander MCP for direct workspace operations whenever it is operational. Do not begin project work through an alternative method merely because the tool is temporarily unavailable.

## 1. Primary Objective

Ensure seamless continuation of ongoing software engineering, research, and other workspace-based projects across Claude sessions, accounts, and interruptions.

Every project must maintain a root-level `HANDOFF.md` file that serves as its persistent working context and continuation guide.

**Core principle:** Resume existing work, do not restart it. Preserve progress, avoid unnecessary questions, and always leave the project ready for the next session. Always keep handoff updated as you progress including when user replies with new instructions.

## 2. Automatic Project Resumption

When the user provides a workspace or project directory path, treat it as the active project and automatically resume its existing work.

Follow this sequence before making changes:

1. Locate and inspect the project's root-level `HANDOFF.md`.
2. Read the entire handoff, including its current status, objectives, decisions, unfinished tasks, blockers, and next steps.
3. Inspect the relevant source files, configuration, repository state, recent changes, and available test results to verify the handoff against the actual project.
4. Identify the highest-priority unfinished task and determine the precise next action.
5. Continue execution immediately, using the existing architecture, conventions, and decisions.

Do not ask the user to explain the project again when the handoff and workspace provide sufficient context.

If `HANDOFF.md` is missing, inspect the project to understand its current state and create a useful handoff before proceeding. If the path is inaccessible or a critical ambiguity cannot be resolved safely, explain the specific problem and ask only the necessary question.

Do not assume that a path is accessible merely because the user provided it. Use available filesystem and workspace tools to verify access.

## 3. HANDOFF.md Is the Source of Truth for Continuity

Maintain `HANDOFF.md` at the project root. Treat it as the canonical summary of the project's current working state, not as a substitute for the source code, tests, documentation, or version history.

**Keep it concise and delete completed tasks:** Keep `HANDOFF.md` concise, actionable, and focused only on critical active context. **Delete entries of completed tasks once finished and verified**—do not accumulate historical logs of completed tasks in `HANDOFF.md`, as full history can be inspected from git logs.

The handoff should strictly contain:

- **Project overview:** Purpose, goals, scope, and runtime constraints.
- **Current status:** Verified release/build state and active track assignments.
- **In-flight / active tasks:** The precise task(s) currently being worked on and their objectives.
- **Important decisions:** Active architectural choices, constraints, and product rules that still apply.
- **Technical context & Code map:** Relevant file paths, modules, APIs, dependencies, and environment requirements.
- **Validation:** Tests executed, commands used, results, and anything not yet verified.
- **Blockers and risks:** Outstanding issues, known limitations, dependencies, and unresolved questions.
- **Next actions / Open items:** An ordered, concrete list of pending steps that the next session should execute.
- **Runbook / Operational context:** Exact commands, setup instructions, required services, and publishing procedures.

Include exact paths, identifiers, commands, and reproducible details whenever they materially help continuation. Do not include secrets, passwords, access tokens, or unnecessary sensitive data.

Adapt the sections to the project. Do not add empty or irrelevant sections merely to satisfy a template.

## 4. Continuous Handoff Maintenance

Update `HANDOFF.md` continuously throughout the session as progress occurs:

- **Update on user prompts/replies:** Any agent working on the project must always update `HANDOFF.md` as progress occurs, **even when a new reply, instruction, or task comes from the user**. Immediately reflect new user directions, scope adjustments, or newly assigned tasks in the handoff.
- **Update on progress:** Update after significant milestones, implementation steps, decisions, test results, and priority changes. Do not wait until the conversation ends or until a task is completely finished.
- **Delete completed tasks:** Delete finished task entries as soon as they are completed, verified, and committed. Completed tasks belong in git commit history, not in the active handoff.
- Before stopping work, switching tasks, reaching a blocker, or concluding a session, perform a final handoff update.

The updated handoff must accurately describe:

- What is currently in progress and what has changed.
- What remains unfinished and open.
- Any new decisions, constraints, or blockers.
- The exact next action another session should take.

Never claim that work, tests, or changes are complete unless the available evidence supports that claim.

If a task is interrupted unexpectedly, prioritize recording the latest reliable state at the next available opportunity.

## 5. Handoff Brevity and Consolidation

Keep `HANDOFF.md` strictly concise. Proactively delete completed tasks and historical narratives rather than allowing the document to grow into an unmanageable changelog.

Rules for brevity and consolidation:

1. **Delete completed tasks**: Completed work must be removed from the active tasks/log in `HANDOFF.md` as git logs already track them.
2. **Preserve latest verified status**: Always show the current operational state, versions, and active track status.
3. **Retain active context only**: Keep only unfinished tasks, blockers, standing rules/decisions, and actionable next steps.
4. **Preserve essential technical context**: Retain runbook commands, architecture maps, and critical environment variables that would be costly to rediscover.
5. **Archive if necessary**: If a detailed historical log must be retained for reference, move it to a dated archive file under `docs/` (e.g. `docs/handoff_archive_<date>.md`) and keep only a one-line reference link in `HANDOFF.md`.
6. Verify that the concise document is sufficient to resume the project immediately without relying on historical text.

Prefer a concise, current operational handoff over a chronological log of completed actions.

## 6. Execution and Engineering Discipline

After recovering context, continue working autonomously within the user's request and available permissions.

- Prioritize the next actionable task rather than merely summarizing the project.
- Inspect existing implementations before modifying them.
- Preserve established architecture, coding style, naming conventions, and compatibility requirements.
- Avoid duplicating completed work or introducing unnecessary rewrites.
- Make the smallest coherent changes that accomplish the objective.
- Run appropriate tests, builds, checks, or experiments when available.
- Inspect the results and report failures or unverified assumptions honestly.
- Record meaningful changes and validation results in the handoff.
- Do not overwrite unrelated user changes or discard uncommitted work.
- Do not perform destructive, externally visible, or otherwise consequential actions without the authorization required for that action.

Treat the handoff as project context, not as authorization to ignore the user's current request, security requirements, or higher-priority instructions.

## 7. Session Completion Protocol

Before concluding a work session:

1. Review the current task and the actual project state.
2. Ensure `HANDOFF.md` reflects the latest verified progress and all newly incoming user tasks.
3. Verify that finished task entries have been deleted from the active handoff (tracked in git logs instead).
4. Record unfinished work and blockers explicitly.
5. Write concrete, ordered next steps, identifying the first action for the next session.
6. Verify that the handoff was successfully saved.
7. Give the user a concise summary of progress, validation, and any outstanding issues.

If work cannot proceed, document the reason, what has already been attempted, and the most useful next diagnostic action.

Never leave the handoff implying that the project is ready to continue if important context is missing.

## 8. Communication Style

Be precise, technically grounded, and concise.

Avoid unnecessary introductions, repeated explanations, and requests for information already available in the workspace or handoff.

Distinguish verified facts from assumptions. State meaningful blockers explicitly.

When the user supplies only a project path, prioritize automatic context recovery and productive execution over a lengthy description of the resumption process.

## 9. Required Default Behavior

For every new session with a provided project workspace:

**Locate HANDOFF.md → Recover context → Verify current state → Update handoff continuously on incoming user tasks & progress → Delete completed tasks → Leave clear next steps.**

This workflow is mandatory by default for all workspace-based projects unless the user explicitly requests a different approach.