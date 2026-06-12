from pathlib import Path

import pytest
from typer.testing import CliRunner

from wordlepro.cache import get_cache_path
from wordlepro.cli import app
from wordlepro.main import main
from wordlepro.solver import NWordleSolver

WORDS = [
    "aback", "abase", "abate", "abbey", "abbot",
    "abhor", "abide", "abler", "abode", "abort",
]

runner = CliRunner()


@pytest.fixture()
def word_files(tmp_path: Path) -> tuple[Path, Path]:
    answers = tmp_path / "answers.txt"
    guesses = tmp_path / "guesses.txt"
    answers.write_text("\n".join(WORDS) + "\n")
    guesses.write_text("\n".join(WORDS) + "\n")
    return answers, guesses


def file_args(word_files: tuple[Path, Path]) -> list[str]:
    answers, guesses = word_files
    return ["--answers-file", str(answers), "--guesses-file", str(guesses)]


class TestSolveCommand:
    def test_solve_to_completion_warns_on_cold_cache(
        self, word_files: tuple[Path, Path]
    ) -> None:
        get_cache_path(WORDS, WORDS).unlink(missing_ok=True)
        result = runner.invoke(
            app, ["solve", *file_args(word_files)], input="abase\n22222\n"
        )
        assert result.exit_code == 0
        assert "Cache not found" in result.output
        assert "Solved in 1 guess!" in result.output

    def test_no_warning_when_cache_is_warm(self, tmp_path: Path) -> None:
        # Regression test: the cache-exists check must use the merged
        # answers ∪ guesses key the solver caches under, which only
        # differs from the raw guesses list when answers ⊄ guesses.
        answers_file = tmp_path / "answers.txt"
        guesses_file = tmp_path / "guesses.txt"
        answers_file.write_text("\n".join(WORDS) + "\n")
        guesses_file.write_text("\n".join(WORDS[5:]) + "\n")

        # Constructing a solver warms the cache under the merged key.
        NWordleSolver(1, 6, WORDS, WORDS[5:])

        result = runner.invoke(
            app,
            ["solve", "--answers-file", str(answers_file), "--guesses-file", str(guesses_file)],
            input="abase\n22222\n",
        )
        assert result.exit_code == 0
        assert "Cache not found" not in result.output
        assert "Solved in 1 guess!" in result.output


class TestBenchmarkCommand:
    def test_table_output(self, word_files: tuple[Path, Path]) -> None:
        result = runner.invoke(app, ["benchmark", *file_args(word_files)])
        assert result.exit_code == 0
        assert "Benchmark Results" in result.output

    def test_json_output(self, word_files: tuple[Path, Path]) -> None:
        result = runner.invoke(app, ["benchmark", "--json", *file_args(word_files)])
        assert result.exit_code == 0
        assert '"total_words": 10' in result.output


class TestPlayCommand:
    def test_play_with_word(self, word_files: tuple[Path, Path]) -> None:
        result = runner.invoke(
            app, ["play", "--word", "abase", *file_args(word_files)], input="abase\n"
        )
        assert result.exit_code == 0
        assert "You win!" in result.output

    def test_play_invalid_word_exits(self, word_files: tuple[Path, Path]) -> None:
        result = runner.invoke(app, ["play", "--word", "zzzzz", *file_args(word_files)])
        assert result.exit_code == 1
        assert "not in the word list" in result.output

    def test_play_random_word(
        self, word_files: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("wordlepro.cli.random.choice", lambda seq: "abase")
        result = runner.invoke(app, ["play", *file_args(word_files)], input="abase\n")
        assert result.exit_code == 0
        assert "You win!" in result.output


class TestMain:
    def test_main_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["wordlepro", "--help"])
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
