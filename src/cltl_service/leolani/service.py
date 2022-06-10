import logging
import pathlib

from cltl.brain import LongTermMemory
from cltl.combot.event.emissor import TextSignalEvent
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


class LeolaniService:
    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.leolani")

        return cls(config.get("topic_scenario"), config.get("topic_input"), config.get("topic_output"),
                   config.get("brain_log"), event_bus, resource_manager)

    def __init__(self, scenario_topic: str, input_topic: str, output_topic: str, log_path: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._scenario_topic = scenario_topic
        self._input_topic = input_topic
        self._output_topic = output_topic

        self._topic_worker = None

        # Initialise a chat
        self.AGENT = "Leolani"
        self.HUMAN_ID = "Piek"
        self.chat = Chat(self.HUMAN_ID)
        # Initialise the brain in GraphDB
        self.brain = LongTermMemory(address="http://localhost:7200/repositories/sandbox", log_dir=pathlib.Path(log_path),
                                  clear_all=True)
        self._scenario = None

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._input_topic, self._scenario_topic], self._event_bus, provides=[self._output_topic],
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
        if hasattr(event.payload, 'scenario'):
            self._scenario = event.payload.scenario
        elif self._scenario:
            replier = LenkaReplier()
            analyzer = CFGAnalyzer()

            textSignal = TextSignal.for_scenario(self._scenario.id, 0, 0, None, event.payload.signal.text)
            emissor_api.add_speaker_annotation(textSignal, self.HUMAN_ID)

            reply_textSignal = talk.understand_remember_reply(self._scenario, textSignal, self.chat, replier, analyzer,
                                                              self.AGENT, self.HUMAN_ID,
                                                              self.brain,
                                                              self._scenario.context.location, self._scenario.context.location_id,
                                                              logger)

            emissor_api.add_speaker_annotation(reply_textSignal, self.AGENT)
            modifiedPayload = TextSignalEvent.for_agent(reply_textSignal)
            modifiedEvent = Event.for_payload(modifiedPayload)
            self._event_bus.publish("cltl.topic.text_out", modifiedEvent)
            logger.info("UTTERANCE reply (%s): (%s)", modifiedEvent.metadata.topic, modifiedEvent.payload.signal.text)
        else:
            logger.debug("Drop event as there is no scenario: %s", event.payload.signal.text)
