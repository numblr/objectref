# specific imports
from random import getrandbits
from datetime import datetime
import requests
import sys

import os
from typing import Tuple
import uuid
import time
from emissor.persistence import ScenarioStorage
from emissor.representation.scenario import ImageSignal, TextSignal, Scenario, Modality, Mention, Annotation


def relative_path(modality: Modality, file_name: str) -> str:
    rel_path = os.path.join(modality.name.lower())

    return os.path.join(rel_path, file_name) if file_name else rel_path


def absolute_path(scenario_storage: ScenarioStorage, scenario_id: str, modality: Modality,
                  file_name: str = None) -> str:
    abs_path = os.path.abspath(os.path.join(scenario_storage.base_path, scenario_id, modality.name.lower()))

    return os.path.join(abs_path, file_name) if file_name else abs_path


def create_image_signal(scenario: Scenario, file: str, bounds: Tuple[int, int, int, int], timestamp: int = None):
    timestamp = int(time.time() * 1e3) if timestamp is None else timestamp
    file_path = relative_path(Modality.IMAGE, file)

    return ImageSignal.for_scenario(scenario.id, timestamp, timestamp, file_path, bounds, [])


def create_text_signal(scenario: Scenario, utterance: str, timestamp: int = None):
    timestamp = int(time.time() * 1e3) if timestamp is None else timestamp
    return TextSignal.for_scenario(scenario.id, timestamp, timestamp, [], utterance, [])


def create_text_signal_with_speaker_annotation(scenario: Scenario, utterance: str, speaker: str, timestamp: int = None):
    timestamp = int(time.time() * 1e3) if timestamp is None else timestamp
    textSignal = TextSignal.for_scenario(scenario.id, timestamp, timestamp, [], utterance, [])
    add_speaker_annotation(textSignal, speaker)
    return textSignal


def create_scenario(scenarioPath: str, scenarioid: str):
    storage = ScenarioStorage(scenarioPath)

    os.makedirs(absolute_path(storage, scenarioid, Modality.IMAGE))
    # Not yet needed
    # os.makedirs(absolut_path(storage, scenarioid, Modality.TEXT))

    print(f"Directories for {scenarioid} created in {storage.base_path}")

    return storage


def add_speaker_annotation(signal: TextSignal, speaker: str):
    current_time = int(time.time() * 1e3)
    ## AnnotationType.UTTERANCE.name.lower() #### @TODO
    annotation = [Annotation("utterance", signal.id, speaker, current_time)]

    signal.mentions.extend([Mention(str(uuid.uuid4()), [signal.id], [annotation])])


def start_a_scenario (AGENT:str, HUMAN_ID:str, HUMAN_NAME: str, root_dir:str):
    ##### Setting the location

    place_id = getrandbits(8)
    location = None
    try:
        location = requests.get("https://ipinfo.io").json()
    except:
        print("failed to get the IP location")

    ### The name of your scenario
    scenario_id = datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
    scenario_path = os.path.abspath(os.path.join(root_dir, 'scenarios'))

    if scenario_path not in sys.path:
        sys.path.append(scenario_path)

    if not os.path.exists(scenario_path):
        os.mkdir(scenario_path)
        print("Created a data folder for storing the scenarios", scenario_path)

    ### Specify the path to an existing folder with the embeddings of your friends
    friends_path = os.path.abspath(os.path.join(root_dir, 'friend_embeddings'))
    if friends_path not in sys.path:
        sys.path.append(friends_path)
        print("The paths with the friends:", friends_path)

    ### Define the folders where the images and rdf triples are saved
    imagefolder = scenario_path + "/" + scenario_id + "/" + "image"
    rdffolder = scenario_path + "/" + scenario_id + "/" + "rdf"

    ### Create the scenario folder, the json files and a scenarioStorage and scenario in memory
    scenarioStorage = create_scenario(scenario_path, scenario_id)
    scenario_ctrl = scenarioStorage.create_scenario(scenario_id, int(time.time() * 1e3), None, AGENT)
    return scenarioStorage,  scenario_ctrl, imagefolder, rdffolder, location, place_id
