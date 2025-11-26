from abc import ABC, abstractmethod
from typing import Dict

from stats.entities.tracks.track_detail import TrackDetailBase


class Diagram(ABC):
    def __init__(self, tracks: Dict[int, Dict[int, TrackDetailBase]]):
        self.tracks: Dict[int, Dict[int, TrackDetailBase]] = tracks

    @abstractmethod
    def draw_and_save(self) -> dict[int, bytes]:
        pass
