# general imports for EMISSOR and the BRAIN

from cltl import brain
from cltl.reply_generation.data.sentences import GREETING, ASK_NAME, ELOQUENCE, TALK_TO_ME
from cltl.reply_generation.lenka_replier import LenkaReplier
from cltl.triple_extraction.api import Chat
from emissor.representation.scenario import Modality, ImageSignal, TextSignal, Mention, Annotation, Scenario

# specific imports
from random import getrandbits, choice
import time
import spacy
import pathlib
import emissor_api

#### The next utils are needed for the interaction and creating triples and capsules
import talk
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer


def get_subj_obj_labels_from_capsules(capsule_list):
    mentions = []
    for capsule in capsule_list:
        label = capsule['subject']['label']
        if label: mentions.append(label)
        label = capsule['object']['label']
        if label: mentions.append(label)
    mentions = list(set(mentions))
    return mentions

def add_mention_to_episodic_memory(textSignal: TextSignal, source, mention_list, my_brain, scenario_ctrl, location,
                                      place_id):
    response_list = []
    for mention in mention_list:

        ### We created a perceivedBy triple for this experience,
        ### @TODO we need to include the bouding box somehow in the object
        #print(mention)
        capsule = capsule_util.scenario_image_triple_to_capsule(scenario_ctrl,
                                                          textSignal,
                                                          location,
                                                          place_id,
                                                          source,
                                                          mention,
                                                          "denotedIn",
                                                          textSignal.id)

        #print(capsule)
        # Create the response from the system and store this as a new signal
        # We use the throughts to respond
        response = my_brain.update(capsule, reason_types=True, create_label=True)
        response_list.append(response)
    return response_list

def listen_and_remember(scenario_ctrl,
                        AGENT,
                        HUMAN_NAME,
                        HUMAN_ID,
                      my_brain,
                      location,
                      place_id):
    print_details = False
    replier = LenkaReplier()
    analyzer = CFGAnalyzer()
    chat = Chat(HUMAN_ID)
    #### Initial prompt by the system from which we create a TextSignal and store it
    initial_prompt = f"{choice(TALK_TO_ME)}"
    print(AGENT + ": " + initial_prompt)
    textSignal = d_util.create_text_signal(scenario_ctrl, initial_prompt)
    scenario_ctrl.append_signal(textSignal)

    utterance = ""
    #### Get input and loop
    while not (utterance.lower() == 'stop' or utterance.lower() == 'bye'):
        ###### Getting the next input signals
        utterance = input('\n')
        print(HUMAN_NAME + ": " + utterance)
        textSignal = d_util.create_text_signal(scenario_ctrl, utterance)
        scenario_ctrl.append_signal(textSignal)

        #### Process input and generate reply

        capsule_list, reply_list, response_list = talk.process_statement_and_reply(scenario_ctrl,
                                                     place_id,
                                                     location,
                                                     HUMAN_ID,
                                                     textSignal,
                                                     chat,
                                                     analyzer,
                                                     replier,
                                                     my_brain,
                                                     print_details)

        reply = ""
        for a_reply in reply_list:
            reply+= a_reply+". "
        print(AGENT + ": " + reply)
        textSignal = d_util.create_text_signal(scenario_ctrl, reply)
        scenario_ctrl.append_signal(textSignal)

        ###### Add denotedIn links for every subject and object label
        mention_list = get_subj_obj_labels_from_capsules(capsule_list)
        add_mention_to_episodic_memory(textSignal, HUMAN_ID, mention_list, my_brain, scenario_ctrl, location, place_id)


def main():
    nlp = spacy.load("en_core_web_sm")

    ##### Setting the agents
    AGENT = "Leolani2"
    HUMAN_NAME = "Stranger"
    HUMAN_ID = "stranger1"
    scenarioStorage, scenario_ctrl, imagefolder, rdffolder, location, place_id = emissor_api.start_a_scenario(AGENT, HUMAN_ID, HUMAN_NAME)

    # Initialise the brain in GraphDB
    log_path = pathlib.Path(rdffolder)
    my_brain = brain.LongTermMemory(address="http://localhost:7200/repositories/sandbox",
                                    log_dir=log_path,
                                    clear_all=True)


    listen_and_remember(scenario_ctrl, AGENT, HUMAN_NAME, HUMAN_ID, my_brain, location, place_id)
    scenario_ctrl.scenario.ruler.end = int(time.time() * 1e3)
    scenarioStorage.save_scenario(scenario_ctrl)

if __name__ == '__main__':
    main()
    

