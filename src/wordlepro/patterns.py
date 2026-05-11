import itertools as it

import numpy as np
from numpy.typing import NDArray

NUM_PATTERNS: int = 3**5  # 243


def compute_pattern(guess: str, answer: str) -> list[int]:
    """Return per-position clue: 0=grey, 1=yellow, 2=green."""
    result = [0] * len(guess)
    pool = list(answer)
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = 2
            pool[i] = ""
    for i, g in enumerate(guess):
        if result[i] == 0 and g in pool:
            result[i] = 1
            pool[pool.index(g)] = ""
    return result


def encode_word_list(words: list[str]) -> NDArray[np.uint8]:
    return np.array([[ord(c) for c in word] for word in words], dtype=np.uint8)


def encode_guess_result(result: str) -> int:
    if not result.isnumeric() or any(c not in "012" for c in result):
        raise ValueError(f"Invalid result string: {result!r}. Use digits 0, 1, 2 only.")
    return sum(int(x) * 3**i for i, x in enumerate(result))


def generate_pattern_matrix(
    guess_list: list[str], answer_list: list[str]
) -> NDArray[np.uint8]:
    num_guesses = len(guess_list)
    num_answers = len(answer_list)
    len_word = len(guess_list[0])

    clue_matrix = np.zeros((num_guesses, num_answers, len_word), dtype=np.uint8)

    guess_ints = encode_word_list(guess_list)
    answer_ints = encode_word_list(answer_list)

    equality = np.zeros((num_guesses, num_answers, len_word, len_word), dtype=bool)
    for i, j in it.product(range(len_word), range(len_word)):
        equality[:, :, i, j] = np.equal.outer(guess_ints[:, i], answer_ints[:, j])

    for i in range(len_word):
        matches = equality[:, :, i, i].flatten()
        clue_matrix[:, :, i].flat[matches] = 2
        for j in range(len_word):
            equality[:, :, i, j].flat[matches] = False
            equality[:, :, j, i].flat[matches] = False

    for i, j in it.product(range(len_word), range(len_word)):
        matches = equality[:, :, i, j].flatten()
        clue_matrix[:, :, i].flat[matches] = 1
        for k in range(len_word):
            equality[:, :, k, j].flat[matches] = False
            equality[:, :, i, k].flat[matches] = False

    patterns: NDArray[np.uint8] = np.dot(
        clue_matrix, (3 ** np.arange(len_word)).astype(np.uint8)
    )
    return patterns
