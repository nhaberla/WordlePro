import pytest

from wordlepro.words import load_word_lists


class TestLoadWordLists:
    def test_returns_two_lists(self) -> None:
        result = load_word_lists()
        assert isinstance(result, tuple) and len(result) == 2

    def test_answer_count_in_range(self) -> None:
        answers, _ = load_word_lists()
        assert 2000 <= len(answers) <= 3000

    def test_guess_count_in_range(self) -> None:
        _, guesses = load_word_lists()
        assert 8000 <= len(guesses) <= 15000

    def test_all_answers_lowercase_five_alpha(self) -> None:
        answers, _ = load_word_lists()
        for word in answers:
            assert word.islower() and len(word) == 5 and word.isalpha()

    def test_all_guesses_lowercase_five_alpha(self) -> None:
        _, guesses = load_word_lists()
        for word in guesses:
            assert word.islower() and len(word) == 5 and word.isalpha()

    def test_path_override_answers(self, tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
        f = tmp_path / "custom_answers.txt"
        f.write_text("crane\nslate\naudio\n")
        answers, _ = load_word_lists(answers_path=f)
        assert answers == ["audio", "crane", "slate"]

    def test_path_override_guesses(self, tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
        f = tmp_path / "custom_guesses.txt"
        f.write_text("crane\nslate\n")
        _, guesses = load_word_lists(guesses_path=f)
        assert guesses == ["crane", "slate"]

    def test_nonexistent_path_raises(self, tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
        with pytest.raises(FileNotFoundError):
            load_word_lists(answers_path=tmp_path / "missing.txt")
