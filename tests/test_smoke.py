"""End-to-end smoke test covering the full pipeline (issue #18)."""
import importlib.resources
import shutil

import platformdirs
import pytest

from wordlepro.benchmark import run_benchmark
from wordlepro.cache import get_cache_path
from wordlepro.patterns import generate_pattern_matrix
from wordlepro.solver import NWordleSolver
from wordlepro.words import load_word_lists


def _combined_guesses(answers: list[str], guesses: list[str]) -> list[str]:
    """The solver merges answers ∪ guesses as the full guess pool."""
    return sorted(set(answers) | set(guesses))


def _clear_cache(answers: list[str], guesses: list[str]) -> None:
    path = get_cache_path(answers, _combined_guesses(answers, guesses))
    if path.exists():
        path.unlink()


@pytest.fixture()
def word_lists() -> tuple[list[str], list[str]]:
    return load_word_lists()


class TestCacheMissAndHit:
    def test_cache_miss_generates_and_saves(
        self, word_lists: tuple[list[str], list[str]]
    ) -> None:
        answers, guesses = word_lists
        _clear_cache(answers, guesses)
        cache_path = get_cache_path(answers, _combined_guesses(answers, guesses))
        assert not cache_path.exists()

        # First init: cache miss — builds and saves
        NWordleSolver(1, 6, answers, guesses)
        assert cache_path.exists(), "Cache file should be created after first init"

        solver = NWordleSolver(1, 6, answers, guesses)

        guess, bits = solver.get_guess()
        assert len(guess) == 5
        assert bits > 0

    def test_cache_hit_loads_without_recomputing(
        self, word_lists: tuple[list[str], list[str]]
    ) -> None:
        answers, guesses = word_lists
        # Ensure cache exists
        NWordleSolver(1, 6, answers, guesses)
        cache_path = get_cache_path(answers, _combined_guesses(answers, guesses))
        assert cache_path.exists()

        mtime_before = cache_path.stat().st_mtime
        # Second init: should hit cache (file not modified)
        NWordleSolver(1, 6, answers, guesses)
        assert cache_path.stat().st_mtime == mtime_before


class TestSolveLoop:
    def test_valid_result_updates_board(
        self, word_lists: tuple[list[str], list[str]]
    ) -> None:
        answers, guesses = word_lists
        solver = NWordleSolver(1, 6, answers, guesses)
        before = solver.num_answers

        guess, bits = solver.get_guess()
        assert bits > 0

        # Compute the real pattern for the first answer so limit_options succeeds
        target_col = answers.index(answers[0])
        base = solver.pattern_matrices[0].copy()
        row = solver.guesses[guess]
        pat = int(base[row, target_col])
        digits = []
        v = pat
        for _ in range(5):
            digits.append(str(v % 3))
            v //= 3
        solver.limit_options(guess, ["".join(digits)])

        assert solver.num_answers <= before

    def test_invalid_result_raises_value_error(
        self, word_lists: tuple[list[str], list[str]]
    ) -> None:
        answers, guesses = word_lists
        solver = NWordleSolver(1, 6, answers, guesses)
        guess, _ = solver.get_guess()
        with pytest.raises(ValueError):
            solver.limit_options(guess, ["abc"])


class TestBenchmarkSmoke:
    def test_small_benchmark_completes(self) -> None:
        answers, guesses = load_word_lists()
        subset = answers[:10]
        result = run_benchmark(subset, guesses, num_boards=1, max_guesses=6)
        assert result.total_words == 10
        assert result.solved + len(result.failed_words) == result.total_words
        assert sum(result.distribution.values()) == result.total_words
        assert result.elapsed_seconds > 0


class TestCacheLocation:
    def test_cache_in_platformdirs_location(
        self, word_lists: tuple[list[str], list[str]]
    ) -> None:
        answers, guesses = word_lists
        cache_path = get_cache_path(answers, _combined_guesses(answers, guesses))
        expected_base = platformdirs.user_cache_dir("wordlepro", appauthor=False)
        assert str(cache_path).startswith(expected_base)
