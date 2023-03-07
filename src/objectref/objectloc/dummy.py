import abc
from typing import Tuple

from cltl.backend.api.camera import Image, Bounds

from objectref.objectloc.api import ObjectLocationDetector


class DummyObjectLocationDetector(ObjectLocationDetector):
    def get_location(self, image: Image, bounds: Bounds) -> Tuple[float, float, float]:
        return (0,0,0)