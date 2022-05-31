import logging
import pathlib
import uuid
from datetime import datetime

import requests
from cltl.brain import LongTermMemory
from cltl.combot.event.emissor import LeolaniContext, ScenarioStarted, ScenarioStopped
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.combot.infra.time_util import timestamp_now
from cltl.commons.discrete import UtteranceType
from emissor.representation.scenario import Modality, Scenario

logger = logging.getLogger(__name__)


class ContextService:
    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.context")
        scenario_topic = config.get("topic_scenario")
        speaker_topic = config.get("topic_speaker")
        knowledge_topic = config.get("topic_knowledge")
        intention_topic = config.get("topic_intention")
        desire_topic = config.get("topic_desire")

        config = config_manager.get_config("cltl.brain")
        log_path = config.get("log_dir")

        return cls(scenario_topic, speaker_topic, knowledge_topic,
                   intention_topic, desire_topic,
                   log_path, event_bus, resource_manager)

    def __init__(self, scenario_topic: str, speaker_topic: str, knowledge_topic: str,
                 intention_topic: str, desire_topic: str, log_path: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._scenario_topic = scenario_topic
        self._speaker_topic = speaker_topic
        self._intention_topic = intention_topic
        self._desire_topic = desire_topic
        self._knowledge_topic = knowledge_topic

        self._topic_worker = None

        self.AGENT = "Leolani"
        self.brain = LongTermMemory(address="http://localhost:7200/repositories/sandbox",
                                    log_dir=pathlib.Path(log_path),
                                  clear_all=True)
        self._scenario = None

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._intention_topic, self._desire_topic], self._event_bus,
                                         provides=[self._intention_topic],
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
        if event.metadata.topic == self._intention_topic:
            intentions = event.payload.intentions
            if "init" in intentions:
                self._start_scenario()
            if "terminate" in intentions:
                self._stop_scenario()
        elif event.metadata.topic == self._desire_topic:
            achieved = event.payload.achieved
            if "quit" in achieved:
                self._stop_scenario()
        elif event.metadata.topic == self._speaker_topic:
            id_annotation, name_annotation = event.payload.mentions[0].annotations
            self._scenario.context.speaker = id_annotation.value
            # TODO set face ID in brain
            # capsule = {}
            # self._event_bus.publish(self._knowledge_topic, Event.for_payload(capsule))

    def _start_scenario(self):
        scenario, capsule = self._create_scenario()
        self._event_bus.publish(self._scenario_topic,
                                Event.for_payload(ScenarioStarted.create(scenario)))
        self._event_bus.publish(self._knowledge_topic, Event.for_payload([capsule]))
        self._scenario = scenario
        logger.info("Started scenario %s", scenario)

    def _stop_scenario(self):
        self._event_bus.publish(self._scenario_topic,
                                Event.for_payload(ScenarioStopped.create(self._scenario)))
        logger.info("Stopped scenario %s", self._scenario)

    def _create_speaker_capsule(self, mention_id, id, name):
        return {}
        # return {
        #     "chat": self._scenario.id,
        #     "turn": mention_id,
        #     "author": {"label": "leolani", "type": ["robot"],
        #                'uri': "http://cltl.nl/leolani/friends/leolani"},
        #     "utterance": "",
        #     "utterance_type": UtteranceType.STATEMENT,
        #     "position": "",
        #     "subject": {"label": name, "type": ["person"], 'uri': None},
        #     "predicate": {"label": "has face", "uri": "http://cltl.nl/leolani/n2mu/has-face"},
        #     "object": {"label": id, "type": ["face"], 'uri': None},
        #     "perspective": {"certainty": 1, "polarity": 1, "sentiment": 0},
        #     "timestamp": timestamp_now(),
        #     "context_id": self._scenario.id
        # }

    def _create_scenario(self):
        AGENT = "Leolani"

        signals = {
            Modality.IMAGE.name.lower(): "./image.json",
            Modality.TEXT.name.lower(): "./text.json",
            Modality.AUDIO.name.lower(): "./audio.json"
        }

        scenario_start = datetime.today().strftime('%Y-%m-%d')
        location = self._get_location()

        scenario_context = LeolaniContext(AGENT, "", str(uuid.uuid4()), location)
        scenario = Scenario.new_instance(str(uuid.uuid4()), scenario_start, None, scenario_context, signals)

        capsule = {
            "type": "context",
            "context_id": scenario.id,
            "date": scenario_start,
            "place": None,
            "place_id": None,
            "country": location["country"],
            "region": location["region"],
            "city": location["city"]
        }

        return scenario, capsule

    def _get_location(self):
        try:
            return requests.get("https://ipinfo.io").json()
        except:
            return {"country": "", "region": "", "city": ""}
