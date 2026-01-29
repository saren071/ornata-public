# AGENTS.md

This document defines how coding agents should operate when contributing to this repository.

---

- Python Version: 3.14 - DO NOT change this.
- DO NOT USE EXTERNAL REQUIRED DEPENDENCIES.
- USE UV TO RUN ANYTHING IN THIS PROJECT.
- ACTIVATE THE VENV WITH `.venv\Scripts\activate` BEFORE RUNNING ANY COMMANDS IN THE TERMINAL.
- DO NOT USE EMOJIS.
- DO NOT IMPLEMENT LINUX AND MACOS INTEGRATION AS THIS SYSTEM IS WINDOWS FIRST DURING DEVELOPMENT.
- WHATEVER THE USER/ DEV STATES OVERRIDES THIS AGENTS.MD

- WHEN IMPORTING FROM CROSS MODULES, LIKE CORE TO RENDERING, OR STYLING TO CORE, ETC, USE `from ornata.api.exports.{module} import {function/method/class, etc}`. WHEN IMPORTING IN THE SAME MODULE, LIKE RENDERING TO RENDERING, USE FULL PATH `from ornata.rendering.{path} import {function/method/class, etc}`.


THIS SYSTEM DOES NOT USE CSS. IT USES CUSTOM STYLING CALLED ORNATA STYLE AND THEMING SHEET, OSTS.
---

## Coding Philosophy

- **Separation of Concerns:**
  - Each module/file should have a single clear purpose.
  - Avoid mixing I/O, domain logic, and orchestration in the same function.
- **Purity Preference:**
  - Favor pure functions where possible (no shared state, no side-effects).
  - If a function mutates state or performs I/O, name it accordingly (e.g., `write_config`, `load_state`).
- **Requirements:**
  - Everything specified in this document must be followed.
  - IF YOU ARE UNSURE ABOUT ANYTHING AT ALL, ASK QUESTIONS. QUESTIONS ARE REQUIRED TO BE ANSWERED BEFORE ANY CODE CAN BE WRITTEN. This can include intent, architecture, etc.
  - This is being built with python 3.14t/3.14. Compatibility is required for both regular python, and freethreading This also uses cython for performance, but that is an optional download for users.
  - Ornata is a terminal text & UI formatting engine (to directly compete with React, Rust packages, PyQt6, and other GUI frameworks, but being the first python framework to be able to run freethreading, AND run apps as advanced as web apps) for building console applications, GUI applications, TTY applications, and GPU (DirectX11, DirectX12, OpenGL) applications.
  - Most files should contain at least one class for encapsulation, but utility modules (constants, simple functions, type definitions) may be exceptions where appropriate.
  - All types must be in the src/ornata/definitions/ files to ensure all types are properly accounted for and used.

## Dependency rule

- Subsystem → api only. No subsystem ↔ subsystem imports. GUI contexts expose only RenderContext; real GPU work lives under gpu/.

## Free Threading

- Render loop infra uses actor-based concurrency patterns with WorkStealingScheduler, ParallelProcessor, and WorkerManager from core/concurrency.py. Cython ops live under optimization/cython/ and must avoid shared interpreter state.
- This must support both No GIL, and GIL.

- **README.md**:
  - Always update the README.md file at the root to reflect the current state of the project unless the user specifically states otherwise.
  - Include clear usage examples, and API documentation.
  - Document supported platforms, Python version requirements, and dependencies.
  - Be descriptive and clear about the project's purpose as a terminal text & UI formatting library.

---

## Code Style Rules

| Area | Rule |
|------|------|
| Imports | Group: stdlib → third-party → internal. No unused imports. No wildcard imports. |
| Naming | `snake_case` for functions/vars, `PascalCase` for classes, `CONSTANT_CASE` for constants. |
| Venv | Activate the `venv` with `.venv\Scripts\activate` before running commands in the terminal. |
| Package running | Use `UV` to run the package when needed or other files, eg. `uv run test.py` |
| Linting | Use the `ruff` linter to enforce the code style rules. |
| Formatting | Use the `ruff` formatter to enforce the code style rules. |
| Type Ignoring | DO NOT use `# type: ignore` comments. ONLY use `# pragma: no cover` or any other pragmas where required for pytest. |
| Functions | Small, composable. If >100 lines, consider splitting logic. |
| Side Effects | Must be explicit in function name or docstring. |
| Comments | Only for **intent or rationale**, not obvious code. If needing todo comments, write them as `# TODO: (reason):` rather than guessing architectural direction. |
| Errors | Fail loudly and clearly. Raise typed exceptions, or log and continue, don’t silently pass. Don't use fallbacks except fallbacks for things like gpu not loading, falling back to cpu, for example, as some users may not have a gpu or may not have the required drivers.|
| Docstrings | Required for all functions. One-sentence summary on first line. Always include the parameters and the return type in the docstring.|
| Types | **All new code must include type hints**. Avoid `Any` unless justified inline.  Also avoid using `Dict`, `List`, `Tuple`, `Set`, `Union`, `Optional`, and instead use `dict`, `list`, `tuple`, `set`, `(vertical bar or pipe)` for `Union`, `(vertical bar or pipe) None` for `Optional`, respecively. Import `Callable` from `collections.abc`, not `typing`. Always include the type hints in the docstring. Do not use Cast. |

---

## Agent Behavior Rules

- **When modifying code:**
  - Prefer surgical edits over refactors unless refactor is explicitly needed.
  - Preserve existing structure unless it is clearly flawed.
  - If introducing new concept, use a dedicated module instead of extending an unrelated one.

- **When adding functionality:**
  - First check if similar logic exists — reuse before writing new.
  - If adding a new file/module, ensure its name clearly communicates its domain responsibility.

- **When unsure about intent:**
  - Default to minimal impact.
  - Add a `# TODO: (reason):` rather than guessing architectural direction.

---

## Type and Interface Guidelines

- Public-facing functions should define input/output types clearly.
- Return **actual data structures**, not raw dicts, unless marked as internal.
- Prefer `TypedDict` / `dataclass` / `Enum` for structured data.
- Avoid boolean flags that change behavior — split into two functions instead.

---

## Clean Code Priorities (ALL REQUIRED)

1. Correctness
2. Clarity
3. Explicitness
4. Composability
5. Performance
6. Security
7. Doc Strings/ comments
8. Ease of use when importing the library and using the library.
9. Documentation


ALL TESTS GO IN TESTS/ AND ARE SORTED PER SYSTEM.

### FINAL NOTE

- Ensure you make the api system the only interface to the public. Deter devs from using the internal packages, by printing a warning when they're accessed, but don't block them from doing so.

---

End of `AGENTS.md`.
