# WordlePro

[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/managed%20with-uv-purple)](https://github.com/astral-sh/uv)
[![mypy](https://img.shields.io/badge/type%20checked-mypy%20--strict-blue)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub repo](https://img.shields.io/badge/GitHub-nhaberla%2FWordlePro-181717?logo=github)](https://github.com/nhaberla/WordlePro)

An entropy-based Wordle solver that computes optimal guesses using information theory. Given the remaining possible answers, WordlePro selects whichever guess maximizes expected information gain — minimizing the number of guesses needed to solve the puzzle. Supports standard Wordle and multi-board variants like Quordle.

## Features

- **Optimal guessing** — picks the guess with maximum expected entropy across all remaining candidates
- **Multi-board support** — solve Quordle and other N-board variants with `--boards N`
- **Pattern matrix cache** — precomputes the full guess × answer clue table once and caches it to disk; subsequent runs are instant
- **Interactive solver** — guides you through a live game step by step
- **Benchmark mode** — runs the solver against every answer word and reports guess-count statistics

## Installation

Requires [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/nhaberla/WordlePro.git
cd WordlePro
uv sync
```

## Usage

### Interactive solver

```bash
uv run wordlepro solve
```

WordlePro suggests the best guess each turn. Enter the word you played, then enter the result as a string of digits — `0` (grey), `1` (yellow), `2` (green) — for each board.

Example for a single board:
```
Suggested guess: CRANE  (5.23 bits)
Enter your guess: crane
Enter results (b1): 01200
```

### Multi-board (e.g. Quordle)

```bash
uv run wordlepro solve --boards 4
```

Results are entered space-separated, one per unsolved board:
```
Enter results (b1 b2 b3 b4): 00000 01100 22222 00120
```

### Benchmark

```bash
uv run wordlepro benchmark
```

Runs the solver against every answer word and prints a distribution table. Use `--json` for machine-readable output.

```bash
uv run wordlepro benchmark --boards 4 --json
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--boards N` | `1` | Number of simultaneous boards |
| `--max-guesses N` | `6` | Maximum guesses allowed |
| `--answers-file PATH` | bundled | Override the answer word list |
| `--guesses-file PATH` | bundled | Override the allowed guess list |

## How it works

1. **Pattern matrix** — for every (guess, answer) pair, encodes the Wordle clue as a base-3 integer (0 = grey, 1 = yellow, 2 = green). This matrix is computed once and cached as a `.npy` file via [platformdirs](https://github.com/platformdirs/platformdirs).
2. **Entropy calculation** — for each candidate guess, computes the Shannon entropy of the clue distribution across remaining possible answers. Higher entropy → more information gained → fewer guesses expected.
3. **Guess selection** — picks the guess with the highest expected entropy. On multi-board games, entropies are summed across boards.
4. **Filtering** — after each guess, eliminates answers that are inconsistent with the observed clue pattern.

## Development

```bash
uv run pytest              # run tests
uv run mypy --strict src/  # type checking
```

## Author

**Noah Haberland** — [noah17haberland@gmail.com](mailto:noah17haberland@gmail.com) · [github.com/nhaberla](https://github.com/nhaberla)
