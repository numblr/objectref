import base64
import json
import logging
import pathlib
from io import BytesIO
from typing import Callable

import flask
from flask import Response
from PIL import Image
from cltl.backend.source.client_source import ClientImageSource
from cltl.backend.spi.image import ImageSource
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.topic_worker import TopicWorker

from cltl.friends.brain import BrainFriendsStore

logger = logging.getLogger(__name__)


class MonitoringService:
    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.monitoring")
        image_topic = config.get("topic_image")
        object_topic = config.get("topic_object")
        vector_id_topic = config.get("topic_vector_id")
        text_in_topic = config.get("topic_text_in")
        text_out_topic = config.get("topic_text_out")

        config = config_manager.get_config("cltl.brain")
        log_path = config.get("log_dir")

        def image_loader(url) -> ImageSource:
            return ClientImageSource.from_config(config_manager, url)

        return cls(image_topic, object_topic, vector_id_topic, text_in_topic, text_out_topic, log_path,
                   image_loader, event_bus, resource_manager)

    def __init__(self, image_topic: str, object_topic: str, vector_id_topic: str, text_in_topic: str, text_out_topic: str,
                 log_path: str, image_loader: Callable[[str], ImageSource],
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

        self._friend_store = BrainFriendsStore(address="http://localhost:7200/repositories/sandbox",
                                    log_dir=pathlib.Path(log_path))
        self._app = None
        self._text_info = None
        self._display_info = None

    @property
    def app(self):
        if self._app:
            return self._app

        self._app = flask.Flask(__name__)

        @self._app.route('/image', methods=['GET'])
        def display_info():
            if self._display_info:
                return json.dumps(self._display_info)

            return Response(status=404)

        @self._app.route('/text', methods=['GET'])
        def text_info():
            if self._text_info:
                return json.dumps(self._text_info)

            return Response(status=404)

        @self._app.after_request
        def set_cache_control(response):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

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

        # Construct Display Info (to be send to webclient)
        self._display_info = {
            "hash": hash(str(image.image)),
            "img": self._encode_image(Image.fromarray(image.image)),
            "items": [],
        }

    def _encode_image(self, image):
        with BytesIO() as png:
            image.save(png, 'png')
            png.seek(0)
            return base64.b64encode(png.read()).decode('utf-8')

    def _update_people(self, event):
        items = []

        for face_id, bounds in [(annotation.value, mention.segment[0].bounds)
                        for mention in event.payload.mentions
                        for annotation in mention.annotations
                        if annotation.type == "VectorIdentity" and mention.segment]:
            _, names = self._friend_store.get_friend(face_id)

            if names and names[0]:
                name = names[0]
            elif face_id:
                name = face_id
            else:
                continue

            items.append((name, bounds))

        self._add_items(items)

    def _update_objects(self, event):
        objects = [(annotation.value.type, mention.segment[0].bounds)
                        for mention in event.payload.mentions
                        for annotation in mention.annotations
                        if annotation.type == "Object" and annotation.value and mention.segment]

        self._add_items(objects)

    def _add_items(self, items):
        if self._display_info:  # If Ready to Populate
            # Add Items to Display Info
            self._display_info["items"] += [
                {"name": name,
                 "bounds": bounds,
                 } for name, bounds in items]
