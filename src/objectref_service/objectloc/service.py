import logging
from collections import OrderedDict
from typing import Callable

from cltl.backend.source.client_source import ClientImageSource
from cltl.backend.spi.image import ImageSource
from cltl.combot.event.emissor import TextSignalEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.object_recognition.api import Object
from cltl_service.emissordata.client import EmissorDataClient
from emissor.representation.scenario import class_type, TextSignal
from objectref.objectloc.api import ObjectReference

logger = logging.getLogger(__name__)


class ObjectReferenceService:
    @classmethod
    def from_config(cls, object_reference: ObjectReference, emissor_client: EmissorDataClient,
                    event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("objectref.objectloc")
        image_topic = config.get("topic_image")
        object_topic = config.get("topic_object")
        text_in_topic = config.get("topic_text_in")
        text_out_topic = config.get("topic_text_out")

        def image_loader(url) -> ImageSource:
            return ClientImageSource.from_config(config_manager, url)

        return cls(image_topic, object_topic, text_in_topic, text_out_topic,
                   image_loader, object_reference, emissor_client, event_bus, resource_manager)

    def __init__(self, image_topic: str, object_topic: str, text_in_topic: str, text_out_topic: str,
                 image_loader: Callable[[str], ImageSource], object_reference: ObjectReference,
                 emissor_client: EmissorDataClient, event_bus: EventBus, resource_manager: ResourceManager):
        self._emissor_client = emissor_client
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._object_reference = object_reference
        self._image_loader = image_loader

        self._image_topic = image_topic
        self._object_topic = object_topic
        self._text_in_topic = text_in_topic
        self._text_out_topic = text_out_topic

        self._image_cache = OrderedDict()
        self._object_cache = OrderedDict()

        self._topic_worker = None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._image_topic, self._object_topic, self._text_in_topic],
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
        image_id = None
        if event.metadata.topic == self._text_in_topic:
            self._process_text(event.payload.signal.text)
        elif event.metadata.topic == self._image_topic:
            image_id = self._update_image(event)
        elif event.metadata.topic == self._object_topic:
            image_id = self._update_objects(event)
        else:
            logger.warning("Unhandled event: %s", event)

        if image_id and image_id in self._image_cache and image_id in self._object_cache:
            self._process_image(image_id)

    def _process_text(self, utterance):
        # TODO process text and create an answer

        scenario_id = self._emissor_client.get_current_scenario_id()
        utterance = f"You said: {utterance}"
        signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
        self._event_bus.publish(self._text_out_topic, Event.for_payload(TextSignalEvent.for_agent(signal)))

    def _update_image(self, event):
        if len(self._image_cache) > 5:
            self._image_cache.popitem(last=False)

        image_id = event.payload.signal.id
        self._image_cache[image_id] = event.payload.signal.files[0]

        logger.debug("Updated image")

        return image_id

    def _update_objects(self, event):
        if len(self._object_cache) > 5:
            self._object_cache.popitem(last=False)

        # All segments should be in the same image, therefore we just take the first
        image_id = next((mention.segment[0].container_id
                    for mention in event.payload.mentions
                    for annotation in mention.annotations
                    if annotation.type == class_type(Object) and annotation.value and mention.segment), None)

        self._object_cache[image_id] =  [(annotation.value.label, mention.segment[0].bounds)
                   for mention in event.payload.mentions
                   for annotation in mention.annotations
                   if annotation.type == class_type(Object) and annotation.value and mention.segment]

        logger.debug("Updated image")

        return image_id

    def _process_image(self, image_id):
        image_location = self._image_cache[image_id]
        with self._image_loader(image_location) as source:
            image = source.capture()

            logger.debug("Image for objects with bounds %s", image.bounds)

        objects = self._object_cache[image_id]

        # TODO Resolve locations and store objects

        scenario_id = self._emissor_client.get_current_scenario_id()
        utterance = f"Oh, I see objects: {objects} at locations {[self._object_reference.get_location(image, bbox) for _, bbox in objects]}"
        signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
        self._event_bus.publish(self._text_out_topic, Event.for_payload(TextSignalEvent.for_agent(signal)))
