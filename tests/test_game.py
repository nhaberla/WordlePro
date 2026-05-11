import pytest

from wordlepro.game import WordleGame
from wordlepro.patterns import compute_pattern

VALID: set[str] = {"crane", "slate", "audio", "arise", "basic", "catch", "abbey"}


def make_game(secret: str, max_guesses: int = 6) -> WordleGame:
    return WordleGame(secret=secret, max_guesses=max_guesses, valid_guesses=VALID)


# --- compute_pattern ---

def test_compute_pattern_all_green() -> None:
    assert compute_pattern("crane", "crane") == [2, 2, 2, 2, 2]


def test_compute_pattern_mixed_yellow_grey() -> None:
    # "basic" vs "crane": 'a' is yellow (in crane, wrong pos), 'c' is yellow; rest grey
    assert compute_pattern("basic", "crane") == [0, 1, 0, 0, 1]


def test_compute_pattern_yellow() -> None:
    # 'c' is in "crane" but wrong position; 'r' same
    result = compute_pattern("crane", "nacre")
    # c→wrong pos(yellow), r→wrong pos(yellow), a→wrong pos(yellow), n→wrong pos(yellow), e→green
    assert result == [1, 1, 1, 1, 2]


def test_compute_pattern_duplicate_letters_in_guess() -> None:
    # answer "abbey": a=0,b=1,b=2,e=3,y=4
    # guess "catch": c=grey, a=yellow(a in abbey pos0), t=grey, c=grey, h=grey
    result = compute_pattern("catch", "abbey")
    assert result == [0, 1, 0, 0, 0]


def test_compute_pattern_duplicate_letters_in_answer() -> None:
    # answer "abbey" has two b's; guess "basic" has one b
    result = compute_pattern("basic", "abbey")
    # b→yellow(b in abbey but pos1≠pos0), a→yellow(a in abbey at pos0≠pos1), s→grey, i→grey, c→grey
    assert result == [1, 1, 0, 0, 0]


# --- WordleGame.submit ---

def test_submit_wrong_length() -> None:
    game = make_game("crane")
    with pytest.raises(ValueError, match="5 letters"):
        game.submit("hi")


def test_submit_invalid_word() -> None:
    game = make_game("crane")
    with pytest.raises(ValueError, match="not a valid word"):
        game.submit("zzzzz")


def test_submit_after_game_over() -> None:
    game = make_game("crane", max_guesses=1)
    game.submit("slate")
    with pytest.raises(ValueError, match="already over"):
        game.submit("crane")


def test_submit_records_guess_and_pattern() -> None:
    game = make_game("crane")
    pattern = game.submit("slate")
    assert game.guesses == ["slate"]
    assert game.patterns == [pattern]


# --- win / lose ---

def test_won() -> None:
    game = make_game("crane")
    game.submit("crane")
    assert game.won
    assert game.over
    assert not game.lost


def test_lost() -> None:
    game = make_game("crane", max_guesses=2)
    game.submit("slate")
    game.submit("audio")
    assert game.lost
    assert game.over
    assert not game.won


def test_not_over_mid_game() -> None:
    game = make_game("crane")
    game.submit("slate")
    assert not game.over
