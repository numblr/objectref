import abc
from typing import Tuple, Iterable

from cltl.backend.api.camera import Image, Bounds


class ObjectReference(abc.ABC):
    def get_location(self, image: Image, bounds: Bounds) -> Tuple[float, float, float]:
        raise NotImplementedError()

    def add_observation(self, image: Image, objects: Iterable[Tuple[str, Tuple[int, int, int, int]]]):
        raise NotImplementedError()

    def process_utterance(self, utterance: str) -> str:
        raise NotImplementedError()