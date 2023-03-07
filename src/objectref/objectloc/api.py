import abc
from typing import Tuple

from cltl.backend.api.camera import Image, Bounds


class ObjectLocationDetector(abc.ABC):
    def get_location(self, image: Image, bounds: Bounds) -> Tuple[float, float, float]:
        raise NotImplementedError()