import io
import json
import logging
from functools import wraps
from http import HTTPStatus
from typing import Callable

import flask
from PIL import Image, ImageDraw, ImageFont
from cltl.backend.source.client_source import ClientImageSource
from cltl.backend.spi.image import ImageSource
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.object_recognition.api import Object
from emissor.representation.scenario import class_type
from flask import Response

from cltl.friends.api import FriendStore

logger = logging.getLogger(__name__)


try:
    import matplotlib.font_manager
    system_fonts = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    arial = next(f for f in system_fonts if 'arial' in f.lower() and 'bold' in f.lower())
    FONT = ImageFont.truetype(arial, 25)
except:
    FONT = ImageFont.load_default()


def no_cache(f):
    """ Flask decorator that sets headers to prevent caching. """
    @wraps(f)
    def wrapped_f(*args, **kwargs):
        response = f(*args, **kwargs)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response
    return wrapped_f


class MonitoringService:
    @classmethod
    def from_config(cls, friend_store: FriendStore,
                    event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.monitoring")
        image_topic = config.get("topic_image")
        object_topic = config.get("topic_object")
        vector_id_topic = config.get("topic_vector_id")
        text_in_topic = config.get("topic_text_in")
        text_out_topic = config.get("topic_text_out")

        def image_loader(url) -> ImageSource:
            return ClientImageSource.from_config(config_manager, url)

        return cls(image_topic, object_topic, vector_id_topic, text_in_topic, text_out_topic,
                   image_loader, friend_store, event_bus, resource_manager)

    def __init__(self, image_topic: str, object_topic: str, vector_id_topic: str, text_in_topic: str, text_out_topic: str,
                 image_loader: Callable[[str], ImageSource], friend_store: FriendStore,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._image_loader = image_loader

        self._image_topic = image_topic
        self._object_topic = object_topic
        self._vector_id_topic = vector_id_topic
        self._text_in_topic = text_in_topic
        self._text_out_topic = text_out_topic

        self._topic_worker = None

        self._friend_store = friend_store
        self._friend_cache = dict()

        self._app = None
        self._text_info = None
        self._image = None
        self._display = None

    @property
    def app(self):
        if self._app:
            return self._app

        self._app = flask.Flask(__name__)

        @self._app.route('/text', methods=['GET'])
        @no_cache
        def text_info():
            if not self._text_info:
                return Response(status=HTTPStatus.NOT_FOUND)

            return Response(json.dumps(self._text_info), mimetype="application/json")

        @self._app.route('/image.jpg', methods=['GET'])
        def _image():
            if not self._display:
                return Response(status=HTTPStatus.NOT_FOUND)

            response = flask.send_file(io.BytesIO(self._display), mimetype='image/jpeg')

            return response

        return self._app

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._image_topic, self._object_topic, self._vector_id_topic,
                                          self._text_in_topic, self._text_out_topic],
                                         self._event_bus, buffer_size=8, processor=self._process,
                                         resource_manager=self._resource_manager,
                                         name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event):
        if event.metadata.topic == self._text_in_topic:
            self._update_text(event, "You")
        elif event.metadata.topic == self._text_out_topic:
            self._update_text(event, "Leolani")
        elif event.metadata.topic == self._image_topic:
            self._update_image(event)
        elif event.metadata.topic == self._object_topic:
            self._update_objects(event)
        elif event.metadata.topic == self._vector_id_topic:
            self._update_people(event)
        else:
            logger.warning("Unhandled event: %s", event)

    def _update_text(self, event, speaker):
        self._text_info = {
            "utterance": event.payload.signal.text,
            "speaker": speaker
        }

    def _update_image(self, event):
        image_location = event.payload.signal.files[0]

        with self._image_loader(image_location) as source:
            image = source.capture()

        self._image = Image.fromarray(image.image)
        self._create_display(self._image)

        logger.debug("Updated image")

    def _update_people(self, event):
        items = []

        # TODO replace "VectorIdentity" with class_type(VectorIdentity)
        for face_id, bounds in [(annotation.value, mention.segment[0].bounds)
                        for mention in event.payload.mentions
                        for annotation in mention.annotations
                        if annotation.type == "VectorIdentity" and mention.segment]:
            if face_id:
                items.append((self._get_name(face_id), bounds))

        self._annotate_image(items)

    def _get_name(self, face_id):
        if face_id in self._friend_cache:
            return self._friend_cache[face_id]

        _, names = self._friend_store.get_friend(face_id)
        if names and names[0]:
            name = names[0]
            self._friend_cache[face_id] = name

            return name

        return face_id

    def _update_objects(self, event):
        objects = [(annotation.value.type, mention.segment[0].bounds)
                   for mention in event.payload.mentions
                   for annotation in mention.annotations
                   if annotation.type == class_type(Object) and annotation.value and mention.segment]

        self._annotate_image(objects)

    def _annotate_image(self, items) -> None:
        if not self._image or not items:
            return

        draw = ImageDraw.Draw(self._image)
        for name, bbox in items:
            draw.rectangle(bbox, outline=(0, 0, 0))
            draw.text((bbox[0], bbox[1]), (name[:12] + ".." if len(name) > 12 else name), fill=(255, 0, 0), font=FONT)

        self._create_display(self._image)

        logger.debug("Draw %s items in image", len(items))

    def _create_display(self, image) -> None:
        factor = min(1200/image.size[0], 750/image.size[1])
        new_size = tuple(int(factor * dim) for dim in image.size)

        resized = image.resize(new_size, Image.ANTIALIAS)

        img_src = io.BytesIO()
        resized.save(img_src, format="JPEG")
        img_src.seek(0)

        self._display = img_src.read()
