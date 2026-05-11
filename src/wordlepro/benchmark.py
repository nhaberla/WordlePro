import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass

from wordlepro.patterns import generate_pattern_matrix, encode_guess_result
from wordlepro.solver import NWordleSolver


@dataclass
class BenchmarkResult:
    total_words: int
    solved: int
    failed_words: list[str]
    guess_counts: list[int]
    elapsed_seconds: float

    @property
    def mean_guesses(self) -> float:
        return statistics.mean(self.guess_counts)

    @property
    def distribution(self) -> dict[int, int]:
        dist: dict[int, int] = {}
        for c in self.guess_counts:
            dist[c] = dist.get(c, 0) + 1
        return dist


def run_benchmark(
    answers: list[str],
    guesses: list[str],
    num_boards: int,
    max_guesses: int,
    progress_callback: Callable[[int], None] | None = None,
) -> BenchmarkResult:
    # Pre-build the solver once to warm the cache, then reuse via reset()
    solver = NWordleSolver(num_boards, max_guesses, answers, guesses)

    # Pre-compute a lookup: answer word → column index in the pattern matrix
    answer_index = {word: i for i, word in enumerate(answers)}

    # We need the full pattern matrix (guesses × answers) for pattern lookup
    # solver._init_data already built it; grab it before any reset mutates it
    base_matrix = solver.pattern_matrices[0].copy()

    failed_words: list[str] = []
    guess_counts: list[int] = []
    start = time.monotonic()

    for n, target in enumerate(answers):
        solver.reset()
        target_col = answer_index[target]
        guesses_used = 0

        while not solver.game_over:
            guess_word, _ = solver.get_guess()
            guesses_used += 1

            guess_row = solver.guesses[guess_word]
            pattern_int = int(base_matrix[guess_row, target_col])
            # Convert integer pattern back to result string
            digits = []
            val = pattern_int
            for _ in range(5):
                digits.append(str(val % 3))
                val //= 3
            result_str = "".join(digits)

            solver.limit_options(guess_word, [result_str])

            if solver.solved:
                break

        if solver.solved:
            guess_counts.append(guesses_used)
        else:
            failed_words.append(target)
            guess_counts.append(max_guesses + 1)

        if progress_callback is not None:
            progress_callback(n + 1)

    elapsed = time.monotonic() - start
    return BenchmarkResult(
        total_words=len(answers),
        solved=len(answers) - len(failed_words),
        failed_words=failed_words,
        guess_counts=guess_counts,
        elapsed_seconds=elapsed,
    )
