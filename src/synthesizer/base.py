from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from src.synthesizer.config import SynthConfig


class BaseGenerator(ABC):
    """Common state for every generator: config + one shared seeded RNG."""

    def __init__(self, config: SynthConfig, rng: np.random.Generator):
        self.config = config
        self.rng = rng

    @abstractmethod
    def generate(self) -> pd.DataFrame:
        ...

    def random_days(self, low: int, high: int, size: int) -> pd.TimedeltaIndex:
        """Random whole-day offsets in [low, high] inclusive."""
        return pd.to_timedelta(self.rng.integers(low, high + 1, size=size), unit="D")