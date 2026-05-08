# WordlePro — CLAUDE.md

## Project Overview

WordlePro is an entropy-based Wordle solver that computes optimal guesses using information theory. The core algorithm builds a pattern matrix (guess × answer → clue encoding) and selects the guess that maximizes expected entropy across all remaining possible answers. It supports multi-board variants (e.g., Quordle).

## Tech Stack

- **Python 3.14.4**, managed with **uv**
- **NumPy** — pattern matrix generation and entropy calculations
- **Typer** — CLI framework (`wordlepro solve`, `wordlepro benchmark`)
- **Rich** — terminal UI output
- **platformdirs** — cross-platform `.npy` pattern cache location
- **mypy --strict** — enforced type checking

## Repository Layout

```
src/wordlepro/
  __init__.py       # public API re-exports
  main.py           # CLI entry point
  words.py          # word list loading via importlib.resources
  patterns.py       # pure pattern matrix functions
  cache.py          # .npy pattern cache (platformdirs)
  solver.py         # NWordleSolver class
  cli.py            # Typer app + commands
  benchmark.py      # BenchmarkResult dataclass + run_benchmark()
tests/
  test_patterns.py
  test_solver.py
  test_words.py
  test_cache.py
```

## Development Commands

```bash
uv run wordlepro solve        # interactive solver
uv run wordlepro benchmark    # benchmark run
uv run pytest                 # run test suite
uv run mypy --strict src/     # type checking
```

## Core Behavior

**1. Think Before Coding — Don't assume. Don't hide confusion. Surface tradeoffs.**
State assumptions explicitly before implementing. If multiple interpretations exist, present them — don't pick silently. If something is unclear, stop and ask.

**2. Simplicity First — Minimum code that solves the problem. Nothing speculative.**
No features beyond what was asked. No abstractions for single-use code. No "flexibility" or "configurability" that wasn't requested. If 200 lines could be 50, rewrite it.

**3. Surgical Changes — Touch only what you must. Clean up only your own mess.**
Don't improve adjacent code, comments, or formatting. Don't refactor things that aren't broken. Match existing style. If you notice unrelated dead code, mention it — don't delete it.

**4. Goal-Driven Execution — Define success criteria. Loop until verified.**
Transform tasks into verifiable goals. For multi-step work, state a brief plan with a check for each step. Don't report a task complete until the success criterion is met.
