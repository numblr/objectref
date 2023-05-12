from typing import Tuple, Iterable

from cltl.backend.api.camera import Image, Bounds

from objectref.objectloc.api import ObjectReference


class DummyObjectReference(ObjectReference):
    # TODO Adapt interface to our needs
    def add_observation(self, image: Image, objects: Iterable[Tuple[str, Tuple[int, int, int, int]]]):
        pass

    def process_utterance(self, utterance: str) -> str:
        return f"You said {utterance}"

    def get_location(self, image: Image, bounds: Bounds) -> Tuple[float, float, float]:
        return (0, 0, 0)