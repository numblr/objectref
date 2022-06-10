import logging
import pathlib
import uuid
from datetime import datetime

import requests
from cltl.combot.event.emissor import LeolaniContext, Agent, ScenarioStarted, ScenarioStopped, ScenarioEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.topic_worker import TopicWorker
from emissor.representation.scenario import Modality, Scenario

from cltl.friends.brain import BrainFriendsStore

logger = logging.getLogger(__name__)


AGENT = Agent("Leolani", "http://cltl.nl/leolani/world/leolani")


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

        self.AGENT = AGENT
        self._friend_store = BrainFriendsStore(address="http://localhost:7200/repositories/sandbox",
                                    log_dir=pathlib.Path(log_path))
        self._scenario = None

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._intention_topic, self._desire_topic, self._speaker_topic],
                                         self._event_bus, provides=[self._intention_topic],
                                         buffer_size=32, processor=self._process,
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
            self._update_scenario(event)
        else:
            logger.warning("Unhandled event: %s", event)

    def _start_scenario(self):
        scenario, capsule = self._create_scenario()
        self._event_bus.publish(self._scenario_topic,
                                Event.for_payload(ScenarioStarted.create(scenario)))
        self._event_bus.publish(self._knowledge_topic, Event.for_payload([capsule]))
        self._scenario = scenario
        logger.info("Started scenario %s", scenario)

    def _update_scenario(self, event):
        # TODO multiple mentions
        mention = event.payload.mentions[0]
        name_annotation = next(iter(filter(lambda a: a.type == "Entity", mention.annotations)))
        id_annotation = next(iter(filter(lambda a: a.type == "VectorIdentity", mention.annotations)))

        speaker_name = name_annotation.value.text
        uri = self._friend_store.add_friend(id_annotation.value, speaker_name,
                                            scenario_id=self._scenario.id, mention_id=mention.id)
        self._scenario.context.speaker = Agent(speaker_name, str(uri))

        self._event_bus.publish(self._scenario_topic, Event.for_payload(ScenarioEvent.create(self._scenario)))
        logger.info("Updated scenario %s", self._scenario)

    def _stop_scenario(self):
        self._event_bus.publish(self._scenario_topic,
                                Event.for_payload(ScenarioStopped.create(self._scenario)))
        logger.info("Stopped scenario %s", self._scenario)

    def _create_scenario(self):
        signals = {
            Modality.IMAGE.name.lower(): "./image.json",
            Modality.TEXT.name.lower(): "./text.json",
            Modality.AUDIO.name.lower(): "./audio.json"
        }

        scenario_start = datetime.today().strftime('%Y-%m-%d')
        location = self._get_location()

        scenario_context = LeolaniContext(AGENT, Agent(), str(uuid.uuid4()), location, [])
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
