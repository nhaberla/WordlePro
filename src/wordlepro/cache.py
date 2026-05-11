import hashlib
from pathlib import Path

import numpy as np
import platformdirs
from numpy.typing import NDArray


def get_cache_path(answers: list[str], guesses: list[str]) -> Path:
    digest = hashlib.sha256(
        (",".join(sorted(answers)) + "|" + ",".join(sorted(guesses))).encode()
    ).hexdigest()[:12]
    base = Path(platformdirs.user_cache_dir("wordlepro", appauthor=False))
    return base / f"pattern_{digest}.npy"


def load_cache(
    path: Path,
) -> tuple[NDArray[np.uint8], NDArray[np.float64]] | None:
    if not path.exists():
        return None
    with path.open("rb") as f:
        matrix: NDArray[np.uint8] = np.load(f)
        first_entropy: NDArray[np.float64] = np.load(f)
    return matrix, first_entropy


def save_cache(
    path: Path,
    matrix: NDArray[np.uint8],
    first_entropy: NDArray[np.float64],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        np.save(f, matrix)
        np.save(f, first_entropy)
