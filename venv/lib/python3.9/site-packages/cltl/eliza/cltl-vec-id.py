import abc

import numpy as np


class VectorIdentity(abc.ABC):
    def register(self, id: str, representations: np.ndarray) -> str:
        raise NotImplementedError("")

    def add(self, representations: np.ndarray) -> str:
        raise NotImplementedError("")

    def resolve_id(self, representation: np.ndarray) -> str:
        raise NotImplementedError("")


class AgglomerativeIdentity(VectorIdentity):
    def __init__(self, ndim: int):
        self._registered = dict()
        self._centroids = np.array()

        self._representations = np.array((10, ndim))

    def register(self, id: str, representations: np.ndarray) -> str:
        if id not in self._registered:
            self._registered[id] = representations
        else:
            self._registered = np.hstack([self._registered, representations])

    def _cluster(self):


    def add(self, representation: np.ndarray) -> str:
        np.hstack(self._representations, representation)


    def resolve_id(self, representation: np.ndarray) -> str:
        idx = np.argmin(np.cosine(representation, self._centroids))

        return self._clusters[idx]




    def face_detection(self, results):
        faces = [(signal, face) for signal, result in results for face in result]

        face_ids = self.get_unique_faces([face['normed_embedding'] for _, face in faces])

        return [(face_result[0], face_result[1], face_id) for face_result, face_id in zip(faces, face_ids)]

    def get_unique_faces(self, embeddings):
        logging.debug(f"finding unique faces ...")

        friends, representations = zip(*FRIENDS.items())

        if len(embeddings) == 0:
            return None
        # elif len(embeddings) == 1:
        #     labels_clustered = np.array([0])
        else:
            ac = AgglomerativeClustering(n_clusters=None,
                                         affinity='cosine',
                                         linkage='average',
                                         distance_threshold=self.face_cos_distance_threshold)

            clustering = ac.fit(representations + tuple(embeddings))
            friend_labels = clustering.labels_[:len(friends)]
            labels_clustered = clustering.labels_[len(friends):]

        friend_labels = {label: friend for friend, label in zip(friends, friend_labels)}
        labels_unique = np.unique(labels_clustered)
        label2name = {label: friend_labels[label] if label in friend_labels else str(uuid.uuid4())
                      for label in labels_unique}

        face_ids = [label2name[label] for label in labels_clustered]

        return face_ids[len(friends):]














def get2ky():
    states = ["NEW_FACE_KNOWN", "NEW_FACE_UNKNOWN", "GOT_NAME", "GOT_IMAGES", "DONE"]
    actions = {"NEW_FACE_KNOWN": "GREET",
               "NEW_FACE_UNKNOWN": "ASK_NAME",
               "GOT_NAME": "ASK_IMAGES",
               "GOT_IMAGES": "GREET",
               "DONE": None
            }

    }