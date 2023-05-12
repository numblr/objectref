from typing import Tuple

from cltl.backend.api.camera import Image, Bounds

from objectref.objectloc.api import ObjectReference


class DummyObjectReference(ObjectReference):
    def get_location(self, image: Image, bounds: Bounds) -> Tuple[float, float, float]:
        return (0,0,0)