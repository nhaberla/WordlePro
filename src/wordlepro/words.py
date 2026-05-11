import importlib.resources
from pathlib import Path


def load_word_lists(
    answers_path: Path | None = None,
    guesses_path: Path | None = None,
) -> tuple[list[str], list[str]]:
    """Return (answers, guesses). Uses bundled data when paths are None."""
    answers = _load_file(answers_path, "wordle_answers.txt")
    guesses = _load_file(guesses_path, "wordle_guesses.txt")
    return answers, guesses


def _load_file(path: Path | None, bundled_name: str) -> list[str]:
    if path is None:
        resource = importlib.resources.files("wordlepro.data").joinpath(bundled_name)
        text = resource.read_text(encoding="utf-8")
    else:
        if not path.exists():
            raise FileNotFoundError(f"Word list file not found: {path}")
        text = path.read_text(encoding="utf-8")
    words = sorted(set(w.lower().strip() for w in text.splitlines() if w.strip()))
    return words
