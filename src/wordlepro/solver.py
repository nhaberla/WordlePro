import math
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.stats import entropy as scipy_entropy  # type: ignore[import-untyped]

from wordlepro.cache import get_cache_path, load_cache, save_cache
from wordlepro.patterns import NUM_PATTERNS, generate_pattern_matrix
from wordlepro.words import load_word_lists


class NWordleSolver:
    def __init__(
        self,
        num_boards: int,
        max_guesses: int,
        answers: list[str],
        guesses: list[str],
    ) -> None:
        self.num_guesses = 0
        self.max_guesses = max_guesses
        self.num_boards = num_boards
        self.boards_solved = [False] * num_boards
        # Valid guesses = answer words ∪ extra guess words (mirrors real Wordle)
        combined = sorted(set(answers) | set(guesses))
        self._all_guesses = combined
        self.guesses = {word: i for i, word in enumerate(combined)}
        self._answers = answers
        self.curr_entropies: NDArray[np.float64] | None = None
        self._init_data()

    @classmethod
    def from_files(
        cls,
        num_boards: int = 1,
        max_guesses: int = 6,
        answers_path: Path | None = None,
        guesses_path: Path | None = None,
    ) -> "NWordleSolver":
        answers, guesses = load_word_lists(answers_path, guesses_path)
        return cls(num_boards, max_guesses, answers, guesses)

    def _init_data(self) -> None:
        cache_path = get_cache_path(self._answers, self._all_guesses)
        cached = load_cache(cache_path)
        if cached is not None:
            pattern_matrix, self.first_entropy = cached
        else:
            pattern_matrix = generate_pattern_matrix(self._all_guesses, self._answers)
            self.first_entropy = self.calculate_entropies(pattern_matrix)
            save_cache(cache_path, pattern_matrix, self.first_entropy)

        self.pattern_matrices = [pattern_matrix.copy() for _ in range(self.num_boards)]

    def calculate_entropies(
        self, pattern_matrix: NDArray[np.uint8]
    ) -> NDArray[np.float64]:
        distributions = np.apply_along_axis(
            lambda x: np.bincount(x, minlength=NUM_PATTERNS),
            axis=1,
            arr=pattern_matrix,
        )
        result: NDArray[np.float64] = scipy_entropy(distributions, axis=1, base=2)
        return result

    def get_guess(self) -> tuple[str, float]:
        self.num_guesses += 1

        for i, matrix in enumerate(self.pattern_matrices):
            if matrix.shape[1] == 1 and not self.boards_solved[i]:
                return list(self.guesses.keys())[int(np.argmax(matrix))], 0.0

        if self.num_guesses == 1:
            self.curr_entropies = self.first_entropy.copy()
        else:
            combined = np.concatenate(self.pattern_matrices, axis=1)
            self.curr_entropies = self.calculate_entropies(combined)

        num_best = int(
            np.count_nonzero(self.curr_entropies == np.max(self.curr_entropies))
        )
        if num_best > 1:
            best_indices = np.where(
                self.curr_entropies == np.max(self.curr_entropies)
            )[0]
            intersect = np.intersect1d(
                np.where(self.possible_answers() >= 1), best_indices
            )
            index_best = int(
                best_indices[0] if intersect.shape[0] == 0 else intersect[0]
            )
        else:
            index_best = int(np.argmax(self.curr_entropies))

        return self._all_guesses[index_best], float(self.curr_entropies[index_best])

    def get_top_guesses(self, count: int) -> list[tuple[str, float]]:
        if self.curr_entropies is None:
            return []
        best_indices = np.argpartition(self.curr_entropies, -count)[-count:][::-1]
        return [
            (self._all_guesses[int(i)], round(float(self.curr_entropies[i]), 2))
            for i in best_indices
        ]

    def possible_answers(self) -> NDArray[np.intp]:
        combined = np.concatenate(self.pattern_matrices, axis=1)
        result: NDArray[np.intp] = np.asarray(combined == 242).sum(axis=1)
        return result

    def limit_options(self, guess: str, results: list[str]) -> None:
        from wordlepro.patterns import encode_guess_result

        index = self.guesses[guess]
        search_vals = [encode_guess_result(res) for res in results]

        self.boards_solved = [
            solved or val == 242
            for solved, val in zip(self.boards_solved, search_vals)
        ]
        if self.solved:
            return

        for i in range(self.num_boards):
            remaining = np.array(
                np.where(self.pattern_matrices[i][index] == search_vals[i])
            ).flatten()
            idx = np.ix_(
                np.arange(self.pattern_matrices[i].shape[0]), remaining
            )
            self.pattern_matrices[i] = self.pattern_matrices[i][idx]

    @property
    def num_answers(self) -> int:
        return sum(m.shape[1] for m in self.pattern_matrices)

    @property
    def remaining_entropy(self) -> float:
        return math.log(self.num_answers, 2)

    @property
    def solved(self) -> bool:
        return all(self.boards_solved)

    @property
    def game_over(self) -> bool:
        return self.solved or self.num_guesses == self.max_guesses

    def reset(self) -> None:
        self.num_guesses = 0
        self.boards_solved = [False] * self.num_boards
        self.curr_entropies = None
        self._init_data()
