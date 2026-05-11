import numpy as np
import pytest

from wordlepro.cache import get_cache_path, load_cache, save_cache


def _matrix() -> np.ndarray:  # type: ignore[type-arg]
    return np.array([[242, 0], [1, 2]], dtype=np.uint8)


def _entropy() -> np.ndarray:  # type: ignore[type-arg]
    return np.array([5.84, 3.12], dtype=np.float64)


class TestRoundTrip:
    def test_save_then_load_returns_equal_arrays(self, tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
        path = tmp_path / "cache.npy"
        m, e = _matrix(), _entropy()
        save_cache(path, m, e)
        result = load_cache(path)
        assert result is not None
        assert np.array_equal(result[0], m)
        assert np.array_equal(result[1], e)


class TestCachePathDeterminism:
    def test_same_lists_same_path(self) -> None:
        p1 = get_cache_path(["apple"], ["crane"])
        p2 = get_cache_path(["apple"], ["crane"])
        assert p1 == p2

    def test_different_answers_different_path(self) -> None:
        p1 = get_cache_path(["apple"], ["crane"])
        p2 = get_cache_path(["mango"], ["crane"])
        assert p1 != p2

    def test_different_guesses_different_path(self) -> None:
        p1 = get_cache_path(["apple"], ["crane"])
        p2 = get_cache_path(["apple"], ["slate"])
        assert p1 != p2


class TestMissingFile:
    def test_load_nonexistent_returns_none(self, tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
        assert load_cache(tmp_path / "missing.npy") is None


class TestDirectoryCreation:
    def test_save_creates_parent_dirs(self, tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
        nested = tmp_path / "a" / "b" / "c" / "cache.npy"
        save_cache(nested, _matrix(), _entropy())
        assert nested.exists()
