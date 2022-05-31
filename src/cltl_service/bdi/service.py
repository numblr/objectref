import logging
import pathlib

from cltl.brain import LongTermMemory
from cltl.combot.event.emissor import TextSignalEvent
from cltl.combot.event.bdi import IntentionEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.reply_generation import LenkaReplier
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from emissor.representation.scenario import TextSignal

from cltl.leolani import emissor_api, talk

logger = logging.getLogger(__name__)


CONTENT_TYPE_SEPARATOR = ';'


class BDIService:
    """
    Service to manage the BDI model of the agent.

    Components should listen to intentions (use intentions in the TopicWorker
    to activate them for certain intentions only) and publish achieved desires.
    """

    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.bdi")

        return cls(config.get("topic_scenario"), config.get("topic_intention"), config.get("topic_desire"),
                   event_bus, resource_manager)

    def __init__(self, scenario_topic: str, intention_topic: str, desire_topic: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._scenario_topic = scenario_topic
        self._intention_topic = intention_topic
        self._desire_topic = desire_topic

        self._topic_worker = None

        self._scenario = None
        self._intentions = []

        self._bdi = {"init":
                         {"initialized": ["chat"]},
                     "chat":
                         {"quit": ["init"]}
                     }

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._intention_topic, self._desire_topic],
                                         self._event_bus, provides=[self._intention_topic],
                                         resource_manager=self._resource_manager, processor=self._process,
                                         name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event):
        try:
            if event.metadata.topic == self._intention_topic:
                if not self._intentions:
                    self._intentions = event.payload.intentions
                    logger.info("Set intentions to %s", self._intentions)
            elif event.metadata.topic == self._desire_topic:
                self._intentions = [intention
                                    for current_intention in self._intentions
                                    for achieved in event.payload.achieved
                                    for intention in self._bdi[current_intention][achieved]]
                self._event_bus.publish(self._intention_topic, Event.for_payload(IntentionEvent(self._intentions)))
                logger.info("Achieved %s, set intentions to %s", event.payload.achieved[0], self._intentions)
        except:
            logger.exception("Failed to process achieved desire %s for intentions %s", event.payload, self._intentions)
