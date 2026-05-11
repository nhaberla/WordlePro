import dataclasses

from wordlepro.patterns import compute_pattern


@dataclasses.dataclass
class WordleGame:
    secret: str
    max_guesses: int
    valid_guesses: set[str]
    guesses: list[str] = dataclasses.field(default_factory=list)
    patterns: list[list[int]] = dataclasses.field(default_factory=list)

    def submit(self, guess: str) -> list[int]:
        if self.over:
            raise ValueError("Game is already over.")
        if len(guess) != len(self.secret):
            raise ValueError(f"Guess must be {len(self.secret)} letters.")
        if guess not in self.valid_guesses:
            raise ValueError(f"{guess!r} is not a valid word.")
        pattern = compute_pattern(guess, self.secret)
        self.guesses.append(guess)
        self.patterns.append(pattern)
        return pattern

    @property
    def won(self) -> bool:
        return bool(self.patterns) and self.patterns[-1] == [2] * len(self.secret)

    @property
    def lost(self) -> bool:
        return len(self.guesses) >= self.max_guesses and not self.won

    @property
    def over(self) -> bool:
        return self.won or self.lost
