import unittest
from queue import Queue, Empty
from unittest.mock import Mock

from cltl.combot.infra.event import Event
from cltl.combot.infra.event.memory import SynchronousEventBus
from cltl_service.backend.schema import TextSignalEvent

from cltl.eliza.api import Eliza
from cltl_service.eliza.service import ElizaService


class ElizaServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        eliza_mock = unittest.mock.MagicMock(Eliza)
        eliza_mock.respond.side_effect = [f"response {i}" for i in range(10)]

        self.event_bus = SynchronousEventBus()
        self.service = ElizaService("inputTopic", "outputTopic", eliza_mock, self.event_bus, None)

    def tearDown(self) -> None:
        if self.service:
            self.service.stop()

    def test_service_all_utterances(self):
        events = Queue()

        def handler(ev):
            events.put(ev)

        self.event_bus.subscribe("outputTopic", handler)

        self.service.start()

        event = events.get(timeout=1)
        self.assertEqual("TextSignalEvent", event.payload.type)
        self.assertEqual("response 0", event.payload.text)
        self.assertRaises(Empty, lambda: events.get(timeout=0.01))

        self.event_bus.publish("inputTopic", Event.for_payload(TextSignalEvent.create("signal id", 1, "bla", [])))

        event = events.get(timeout=1)
        self.assertEqual("TextSignalEvent", event.payload.type)
        self.assertEqual("response 1", event.payload.text)
        self.assertRaises(Empty, lambda: events.get(timeout=0.01))
