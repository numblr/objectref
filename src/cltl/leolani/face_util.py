import logging
import os
import pickle
import uuid
from collections import namedtuple
from glob import glob
from typing import Tuple

import jsonpickle
import numpy as np
import python_on_whales
import requests
import time
from PIL import Image
from emissor.representation.annotation import AnnotationType
from emissor.representation.entity import Gender, Person, Object
from emissor.representation.ldschema import emissor_dataclass
from emissor.representation.scenario import ImageSignal, Mention, Annotation

from .cv.plots import Annotator, Colors

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def cosine_similarity(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Compute the cosine similarity of the two vectors.

    Args
    ----
    x, y: vectors

    Returns
    -------
    similarity: a similarity score between -1 and 1, where 1 is the most
        similar.

    """

    similarity = np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))

    return similarity


def start_docker_container(
    image: str, port_id: int, sleep_time=5
) -> python_on_whales.Container:
    """Start docker container given the image name and port number.

    Args
    ----
    image: docker image name
    port_id: port id
    sleep_time: warmup time

    Returns
    -------
    container: a docker container object.

    """
    container = python_on_whales.docker.run(
        image=image, detach=True, publish=[(port_id, port_id)]
    )

    logging.info(f"starting a {image} container ...")
    logging.debug(f"warming up the container ...")
    time.sleep(sleep_time)

    return container


def kill_container(container: python_on_whales.Container) -> None:
    """Kill docker container.

    Args
    ----
    container:
        a docker container object.

    """
    container.kill()
    logging.info(f"container killed.")
    logging.info(f"DONE!")


def unpickle(path: str):
    """Unpickle the pickled file, and return it.

    Args
    ----
    path: path to the pickle

    Returns
    -------
    returned: un unpickled object to be returned.

    """
    with open(path, "rb") as stream:
        returned = pickle.load(stream)

    return returned


def load_embeddings(paths: str = "./friend_embeddings/*.pkl") -> dict:
    """Load pre-defined face embeddings.

    Args
    ----
    paths: paths to the face embedding vectors.

    Returns
    -------
    embeddings_predefined: predefined embeddings

    """
    embeddings_predefined = {}
    for path in glob(paths):
        name = path.split("/")[-1].split(".pkl")[0]
        unpickled = unpickle(path)

        embeddings_predefined[unpickled["uuid"]] = {
            "embedding": unpickled["embedding"],
            "name": name,
        }

    return embeddings_predefined


def face_recognition(
    friends_path: str, embeddings: list, COSINE_SIMILARITY_THRESHOLD=0.65
) -> list:
    """Perform face recognition based on the cosine similarity.

    Args
    ----
    embeddings: a list of embeddings
    COSINE_SIMILARITY_THRESHOLD: Currently fixed to The cosine similarity
        threshold is fixed to 0.65. Feel free to play around with this number.

    Returns
    -------
        faces_detected: list of faces (uuids and names) detected.

    """
    embeddings_predefined = load_embeddings(friends_path + "/*.pkl")

    cosine_similarities = []
    for embedding in embeddings:
        cosine_similarities_ = {
            uuid_
            + " "
            + embedding_name["name"]: cosine_similarity(
                embedding, embedding_name["embedding"]
            )
            for uuid_, embedding_name in embeddings_predefined.items()
        }
        cosine_similarities.append(cosine_similarities_)

    logging.debug(f"cosine similarities: {cosine_similarities}")

    faces_detected_ = [max(sim, key=sim.get) for sim in cosine_similarities]
    faces_detected = []
    for uuid_name, sim in zip(faces_detected_, cosine_similarities):
        uuid_, name = uuid_name.split()
        if sim[uuid_name] > COSINE_SIMILARITY_THRESHOLD:
            faces_detected.append({"uuid": uuid_, "name": name})
        else:
            logging.info("new face!")
            faces_detected.append({"uuid": str(uuid.uuid4()), "name": None})
            pass

    return faces_detected


def load_binary_image(image_path: str) -> bytes:
    """Load encoded image as a binary string and return it.

    Args
    ----
    image_path: path to the image to load.

    Returns
    -------
    binary_image: encoded binary image in bytes

    """
    logging.debug(f"{image_path} loading image ...")
    with open(image_path, "rb") as stream:
        binary_image = stream.read()
    logging.info(f"{image_path} image loaded!")

    return binary_image


def run_face_api(to_send: dict, url_face: str = "http://127.0.0.1:10002/") -> tuple:
    """Make a RESTful HTTP request to the face API server.

    Args
    ----
    to_send: dictionary to send to the server. In this function, this will be
        encoded with jsonpickle. I know this is not conventional, but encoding
        and decoding is so easy with jsonpickle somehow.
    url_face: the url of the face recognition server.

    Returns
    -------
    face_bboxes: (list) boudning boxes
    det_scores: (list) detection scores
    landmarks: (list) landmarks
    embeddings: (list) face embeddings
    """
    logging.debug(f"sending image to server...")
    to_send = jsonpickle.encode(to_send)
    response = requests.post(url_face, json=to_send)
    logging.info(f"got {response} from server!...")

    response = jsonpickle.decode(response.text)

    face_detection_recognition = response["face_detection_recognition"]
    logging.info(f"{len(face_detection_recognition)} faces deteced!")

    face_bboxes = [fdr["bbox"] for fdr in face_detection_recognition]
    det_scores = [fdr["det_score"] for fdr in face_detection_recognition]
    landmarks = [fdr["landmark"] for fdr in face_detection_recognition]

    embeddings = [fdr["normed_embedding"] for fdr in face_detection_recognition]

    return face_bboxes, det_scores, landmarks, embeddings


def run_age_gender_api(
    embeddings: list, url_age_gender: str = "http://127.0.0.1:10003/"
) -> tuple:
    """Make a RESTful HTTP request to the age-gender API server.

    Args
    ----
    embeddings: a list of embeddings. The number of elements in this list is
        the number of faces detected in the frame.
    url_age_gender: the url of the age-gender API server.

    Returns
    -------
    ages: (list) a list of ages
    genders: (list) a list of genders.

    """
    # -1 accounts for the batch size.
    data = np.array(embeddings).reshape(-1, 512).astype(np.float32)
    data = pickle.dumps(data)

    data = {"embeddings": data}
    data = jsonpickle.encode(data)
    logging.debug(f"sending embeddings to server ...")
    response = requests.post(url_age_gender, json=data)
    logging.info(f"got {response} from server!...")

    response = jsonpickle.decode(response.text)
    ages = response["ages"]
    genders = response["genders"]

    return ages, genders


def run_yolo_api(to_send: dict, url_yolo: str = "http://127.0.0.1:10004/") -> list:
    """Make a RESTful HTTP request to the face API server.

    Args
    ----
    to_send: dictionary to send to the server. In this function, this will be
        encoded with jsonpickle. I know this is not conventional, but encoding
        and decoding is so easy with jsonpickle somehow.
    url_yolo: the url of the YOLO server.

    Returns
    -------
    results: yolo results. Each element in this list is a dictionary. e.g.,
        {'yolo_bbox': [752, 46, 1148, 716], 'det_score': 0.875, 'label_num': 0,
        'label_string': 'person'}

    """
    logging.debug(f"Running yolo ...")
    logging.debug(f"sending image to server at {url_yolo}...")

    to_send = jsonpickle.encode(to_send)
    print("url",url_yolo)
    response = requests.post(url_yolo, json=to_send)
    logging.info(f"got {response} from server!...")
    response = jsonpickle.decode(response.text)
    results = response["yolo_results"]

    for result in results:
        result["yolo_bbox"] = result.pop("bbox")
    results = [{key: val for key, val in result.items()} for result in results]

    return results


def annotate_yolo(image: Image.Image, yolo_results: list) -> Image.Image:
    """Annotate YOLO Image.

    Args
    ----
    image: PIL image object.
    yolo_results: yolo prediction results.

    Returns
    -------
    image_annotated: Annotated PIL image object.

    """
    logging.debug("Annotating yolo image ...")
    annotator = Annotator(np.ascontiguousarray((image)))
    colors = Colors()  # create instance for 'from utils.plots import colors'

    for result in yolo_results:
        box = result["yolo_bbox"]
        label_num = result["label_num"]
        label_string = result["label_string"]

        color = colors(label_num)
        annotator.box_label(box, label_string, color=color)

    image_annotated = Image.fromarray(annotator.im)
    logging.info(f"YOLO image annotation is done!")

    return image_annotated


def annotate_face(
    image: Image.Image, genders, ages, face_bboxes, faces_detected, det_scores
):
    """Annotate face nicely.

    Args
    ----

    Returns
    -------

    """
    logging.debug("Annotating face, genders, and ages ...")

    assert (
        len(genders)
        == len(ages)
        == len(face_bboxes)
        == len(faces_detected)
        == len(det_scores)
    )
    annotator = Annotator(np.ascontiguousarray((image)))
    colors = Colors()  # create instance for 'from utils.plots import colors'

    for gender, age, face_bbox, uuid_name, faceprob in zip(
        genders, ages, face_bboxes, faces_detected, det_scores
    ):
        box = face_bbox.tolist()
        if gender["m"] > gender["f"]:
            binary_gender = "male"
        else:
            binary_gender = "female"

        try:
            short_name = str(uuid_name["name"].split("_")[0])
        except:
            short_name = str(uuid_name["name"])

        label_string = (
            f"{short_name}, " f"{round(age['mean'])} years old, " f"{binary_gender}."
        )

        color = colors(81)
        annotator.box_label(box, label_string, color=color)

    image_annotated = Image.fromarray(annotator.im)
    logging.info("Annotating face, genders, and ages is done!")

    return image_annotated


FaceInfo = namedtuple('FaceInfo', ('gender',
                                   'age',
                                   'bbox',
                                   'face_id',
                                   'det_score',
                                   'embedding',
                                   'yolo_result'))

def detect_faces(
    friends_path: str,
    image_path: str,
    url_face: str = "http://127.0.0.1:10002/",
    url_age_gender: str = "http://127.0.0.1:10003/",
    url_yolo: str = "http://127.0.0.1:10004",
) -> Tuple[FaceInfo]:
    """Detect faces in an image.

    Args
    ----
    image_path: path to the image in disk
    url_face: the url of the face recognition server.
    url_age_gender: the url of the age-gender API server.
    url_yolo: the url of the YOLO5 API server

    Returns
    -------
    List[FaceInfo]
    """
    MAXIMUM_ENTROPY = {"gender": 0.6931471805599453, "age": 4.615120516841261}

    data = {"image": load_binary_image(image_path)}

    face_bboxes, det_scores, landmarks, embeddings = run_face_api(data, url_face)

    faces_detected = face_recognition(friends_path, embeddings)

    ages, genders = run_age_gender_api(embeddings, url_age_gender)

    yolo_results = run_yolo_api(data, url_yolo)

    logging.debug("annotating image ...")
    image = Image.open(image_path)
    image = annotate_yolo(image, yolo_results)
    image = annotate_face(image, genders, ages, face_bboxes, faces_detected, det_scores)
    logging.info("image annotation is done!")

    image_path = image_path + ".ANNOTATED.jpg"
    logging.debug(f"saving image at {image_path}...")
    image.save(image_path)
    logging.info(f"image saved at {image_path}")

    return tuple(FaceInfo(*info) for info in zip(genders,
                                          ages,
                                          face_bboxes,
                                          faces_detected,
                                          det_scores,
                                          embeddings,
                                          yolo_results))



def detect_objects(
    image_path: str,
    url_yolo: str = "http://127.0.0.1:10004",
):
    """Detect objects in an image.

    Args
    ----
    image_path: path to the image in disk
    url_yolo: the url of the YOLO5 API server

    Returns
    -------
    List[ObjectInfo]
    """

    data = {"image": load_binary_image(image_path)}

    yolo_results = run_yolo_api(data, url_yolo)

    logging.debug("annotating image ...")
    image = Image.open(image_path)
    image = annotate_yolo(image, yolo_results)
    logging.info("image annotation is done!")

    image_path = image_path + ".ANNOTATED.jpg"
    logging.debug(f"saving image at {image_path}...")
    image.save(image_path)
    logging.info(f"image saved at {image_path}")

    return yolo_results


def create_face_mention(image_signal: ImageSignal,
                        source: str,
                        current_time: int,
                        bbox: Tuple[int, int , int, int],
                        uri: str,
                        name: str,
                        age: str,
                        gender: str,
                        face_prob: float) -> Mention:
    bbox = [max(x, lower) for x, lower in zip(bbox[:2], image_signal.ruler.bounds[:2])] + \
            [min(x, upper) for x, upper in zip(bbox[-2:], image_signal.ruler.bounds[-2:])]
    face_segment = image_signal.ruler.get_area_bounding_box(*bbox)
    face_annotation = Annotation(AnnotationType.PERSON.name,
                                 FacePerson(uri, name, age, Gender[gender.upper()], face_prob),
                                 source, current_time)

    return Mention(str(uuid.uuid4()), [face_segment], [face_annotation])


def create_object_mention(image_signal: ImageSignal,
                        source: str,
                        current_time: int,
                        bbox: Tuple[int, int , int, int],
                        name: str,
                        obj_prob: float) -> Mention:
    bbox = [max(x, lower) for x, lower in zip(bbox[:2], image_signal.ruler.bounds[:2])] + \
            [min(x, upper) for x, upper in zip(bbox[-2:], image_signal.ruler.bounds[-2:])]
    object_segment = image_signal.ruler.get_area_bounding_box(*bbox)
    object_annotation = Annotation(AnnotationType.OBJECT.name,
                                 ImageObject(str(uuid.uuid4()), name, obj_prob),
                                 source, current_time)

    return Mention(str(uuid.uuid4()), [object_segment], [object_annotation])


@emissor_dataclass(namespace="http://cltl.nl/leolani/n2mu")
class FacePerson(Person):
    face_prob: float


@emissor_dataclass(namespace="http://cltl.nl/leolani/n2mu")
class ImageObject(Object):
    obj_prob: float