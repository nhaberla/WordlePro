import pytest
import numpy as np

from wordlepro.patterns import encode_guess_result, encode_word_list, generate_pattern_matrix


class TestEncodeGuessResult:
    def test_all_grey(self) -> None:
        assert encode_guess_result("00000") == 0

    def test_all_green(self) -> None:
        assert encode_guess_result("22222") == 242

    def test_first_yellow(self) -> None:
        assert encode_guess_result("10000") == 1

    def test_second_yellow(self) -> None:
        assert encode_guess_result("01000") == 3

    def test_invalid_alpha(self) -> None:
        with pytest.raises(ValueError):
            encode_guess_result("abc")

    def test_invalid_digit_3(self) -> None:
        with pytest.raises(ValueError):
            encode_guess_result("3")

    def test_empty_string(self) -> None:
        with pytest.raises(ValueError):
            encode_guess_result("")


class TestEncodeWordList:
    def test_shape(self) -> None:
        words = ["crane", "slate", "audio"]
        result = encode_word_list(words)
        assert result.shape == (3, 5)

    def test_values_match_ord(self) -> None:
        words = ["crane"]
        result = encode_word_list(words)
        for j, ch in enumerate("crane"):
            assert result[0, j] == ord(ch)


class TestGeneratePatternMatrix:
    def test_shape(self) -> None:
        guesses = ["crane", "slate"]
        answers = ["trace", "audio", "light"]
        m = generate_pattern_matrix(guesses, answers)
        assert m.shape == (2, 3)

    def test_dtype(self) -> None:
        m = generate_pattern_matrix(["crane"], ["trace"])
        assert m.dtype == np.uint8

    def test_all_green(self) -> None:
        m = generate_pattern_matrix(["crane"], ["crane"])
        assert m[0, 0] == 242

    def test_all_grey(self) -> None:
        m = generate_pattern_matrix(["aaaaa"], ["bbbbb"])
        assert m[0, 0] == 0

    def test_crane_vs_trace(self) -> None:
        # c=yellow(1), r=green(2), a=green(2), n=grey(0), e=green(2)
        # 1*1 + 2*3 + 2*9 + 0*27 + 2*81 = 1+6+18+0+162 = 187
        m = generate_pattern_matrix(["crane"], ["trace"])
        assert m[0, 0] == 187
