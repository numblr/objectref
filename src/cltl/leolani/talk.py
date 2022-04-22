from random import choice
import pprint

from cltl.brain.commons.discrete import UtteranceType
from cltl.brain.long_term_memory import LongTermMemory
from cltl.brain.utils.helper_functions import brain_response_to_json
from cltl.reply_generation.lenka_replier import LenkaReplier
from cltl.reply_generation.data.sentences import GREETING, ASK_NAME, ELOQUENCE, TALK_TO_ME

from cltl.triple_extraction.api import Chat
from emissor.representation.scenario import TextSignal, Scenario
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
import cltl.leolani.emissor_api as d_util
import cltl.leolani.capsule_util as c_util
import cltl.leolani.text_util as t_util


def add_mention_to_episodic_memory(textSignal: TextSignal, source, mention_list, my_brain, scenario, location,
                                      place_id):
    response_list = []
    for mention in mention_list:

        ### We created a perceivedBy triple for this experience,
        ### @TODO we need to include the bouding box somehow in the object
        #print(mention)
        capsule = c_util.scenario_image_triple_to_capsule(scenario,
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


def get_subj_obj_labels_from_capsules(capsule_list):
    mentions = []
    for capsule in capsule_list:
        label = capsule['subject']['label']
        if label: mentions.append(label)
        label = capsule['object']['label']
        if label: mentions.append(label)
    mentions = list(set(mentions))
    return mentions

def understand_and_remember(scenario,
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
    textSignal = d_util.create_text_signal(scenario, initial_prompt)

    utterance = ""
    #### Get input and loop
    while not (utterance.lower() == 'stop' or utterance.lower() == 'bye'):
        ###### Getting the next input signals
        utterance = input('\n')
        print(HUMAN_NAME + ": " + utterance)
        textSignal = d_util.create_text_signal(scenario, utterance)

        #### Process input and generate reply

        capsule_list, reply_list, response_list = process_statement_and_reply(scenario,
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
        textSignal = d_util.create_text_signal(scenario, reply)

        ###### Add denotedIn links for every subject and object label
        mention_list = get_subj_obj_labels_from_capsules(capsule_list)
        add_mention_to_episodic_memory(textSignal, HUMAN_ID, mention_list, my_brain, scenario, location, place_id)

def understand_remember_reply(scenario, textSignal, chat, replier, analyzer,
                        AGENT,
                        HUMAN_ID,
                        my_brain,
                        location,
                        place_id,
                        logger):
    #### Process input and generate reply

    capsule_list, reply_list, response_list = process_statement_reply_with_brain(scenario,
                                                 place_id,
                                                 location,
                                                 HUMAN_ID,
                                                 AGENT,
                                                 textSignal,
                                                 chat,
                                                 analyzer,
                                                 replier,
                                                 my_brain,
                                                 logger)


    ###### Add denotedIn links for every subject and object label

    mention_list = get_subj_obj_labels_from_capsules(capsule_list)
    add_mention_to_episodic_memory(textSignal, HUMAN_ID, mention_list, my_brain, scenario, location, place_id)

    reply = ""
    for a_reply in reply_list:
        reply+= a_reply+". "
    reply_textSignal = d_util.create_text_signal(scenario, reply)

    return reply_textSignal


def understand_and_remember_loop(scenario, textSignal,
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
    #### Process input and generate reply

    capsule_list, reply_list, response_list = process_statement_and_reply(scenario,
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
    #print(AGENT + ": " + reply)
    textSignal = d_util.create_text_signal(scenario, reply)

    ###### Add denotedIn links for every subject and object label
    mention_list = get_subj_obj_labels_from_capsules(capsule_list)
    add_mention_to_episodic_memory(textSignal, HUMAN_ID, mention_list, my_brain, scenario, location, place_id)

def understand(scenario, textSignal, chat, analyzer,
                        AGENT,
                        HUMAN_ID,
                      location,
                      place_id):
    print_details = False
    #### Process input and generate reply

    capsule_list, reply_list = process_statement_and_reply(scenario,
                                                 place_id,
                                                 location,
                                                 HUMAN_ID,
                                                 textSignal,
                                                 chat,
                                                 analyzer,
                                                 print_details)

    reply = ""
    for a_reply in reply_list:
        reply+= a_reply+". "
    print(AGENT + ": " + reply)
    textSignal = d_util.create_text_signal(scenario, reply)

    return textSignal

# basic function that creates a capsule from a triple and stores it on the brain
# @parameters triple as a json string and the initilised brain as LongTermMemory
# Posting triples triggers thoughts that are converted to json and returned
# ADDITIONAL PARAMETERS  my_brain.update(capsule, reason_types=True, create_label=False)
# reason_types=True --> it will find subjects and objects in the Semantic web and add the type information
# create_label=True --> it will automatically create a rdfs:label property from the subject label

def post_a_triple(triple, my_brain: LongTermMemory):
    response_json = None
    response = None
    capsule = c_util.triple_to_capsule(triple, UtteranceType.STATEMENT)
    try:
        response = my_brain.update(capsule)
        response_json = brain_response_to_json(response)
    except:
        print('Error:', response)
    return capsule, response_json

def post_a_triple_label_and_type(triple, my_brain: LongTermMemory):
    response_json = None
    response = None
    capsule = c_util.triple_to_capsule(triple, UtteranceType.STATEMENT)
    try:
        response = my_brain.update(capsule, reason_types=True, create_label=True)
        response_json = brain_response_to_json(response)
    except:
        print('Error:', response)
    return capsule, response_json

def post_a_triple_and_verbalise_throughts(triple, replier: LenkaReplier, my_brain: LongTermMemory):
    reply = None
    response = None
    capsule = c_util.triple_to_capsule(triple, UtteranceType.STATEMENT)
    #print(capsule)
    try:
        response = my_brain.update(capsule) # ADDITIONAL PARAMTERS reason_types=True, create_label=False
        response_json = brain_response_to_json(response)
        reply = replier.reply_to_statement(response_json) # ADDITIONAL PARAMETERS proactive=True, persist=True
    except:
        print('Error:', response)
    if reply is None:
        reply = choice(ELOQUENCE)

    return reply

def post_a_query(triple,my_brain: LongTermMemory):
    response_json = None
    response = None

    capsule = c_util.triple_to_capsule(triple, UtteranceType.QUESTION)
    #print(capsule)
    try:
        response = my_brain.query_brain(capsule)
        response_json = brain_response_to_json(response)
    except:
        print('Error:', response)
        
    return response_json


def post_a_query_and_verbalise_answer(triple, replier: LenkaReplier, my_brain: LongTermMemory):
    reply = None
    response = None

    capsule = c_util.triple_to_capsule(triple, UtteranceType.QUESTION)
    #print(capsule)
    try:
        response = my_brain.query_brain(capsule)
        response_json = brain_response_to_json(response)
        reply = replier.reply_to_question(response_json)
    except:
        print('Error:', response)
        
    if reply is None:
        reply = choice(ELOQUENCE)

    return reply



######## Utility function to integrate calls to the brain with ESMISSOR scenarios


def process_text_and_reply(scenario: Scenario,
                           place_id: str,
                           location: str,
                           human_id: str,
                           textSignal: TextSignal,
                           chat: Chat,
                           analyzer: CFGAnalyzer,
                           replier: LenkaReplier,
                           my_brain: LongTermMemory,
                           print_details:False):
    reply_list = []
    capsule = None
    response = None
    response_json = None
    response_list = []
    ### Next, we get all possible triples
    chat.add_utterance(c_util.seq_to_text(textSignal.seq))
    analyzer.analyze(chat.last_utterance)

    if print_details:
            print('Last utterance:', c_util.seq_to_text(textSignal.seq))

    if not chat.last_utterance.triples:
        reply = choice(ELOQUENCE)
        reply_list.append(reply)
    else:
        for extracted_triple in chat.last_utterance.triples:
            print(extracted_triple)
            capsule = c_util.scenario_utterance_to_capsule(scenario, place_id, location, textSignal,human_id, extracted_triple)

            if chat.last_utterance.utterance_type.name == UtteranceType.QUESTION.name:
                capsule = c_util.lowcase_triple_json_for_query(capsule)
                try:
                    response = my_brain.query_brain(capsule)
                    response_json = brain_response_to_json(response)
                    reply = replier.reply_to_question(response_json)
                    response_list.append(response_json)
                    reply_list.append(reply)
                except:
                    print('Error:', response)
            elif chat.last_utterance.utterance_type.name == UtteranceType.STATEMENT.name:
                try:
                    response = my_brain.update(capsule, reason_types=True, create_label=True)
                    response_json = brain_response_to_json(response)
                    reply = replier.reply_to_statement(response_json, proactive=True, persist=True)
                    response_list.append(response_json)
                    reply_list.append(reply)
                except:
                    print('Error:', response)
            response_list.append(response_json)

    return capsule, reply_list, response_list

def process_statement_reply_with_brain(scenario: Scenario,
                           place_id: str,
                           location: str,
                           speaker: str,
                           hearer: str,
                           textSignal: TextSignal,
                           chat: Chat,
                           analyzer: CFGAnalyzer,
                           replier: LenkaReplier,
                           my_brain: LongTermMemory,
                           logger):
    print_details = True
    reply_list = []
    capsule_list = []
    response = None
    response_json = None
    response_list = []
    ### Next, we get all possible triples
    logger.info("UTTERANCE: (%s)", c_util.seq_to_text(textSignal.seq))

    chat.add_utterance(c_util.seq_to_text(textSignal.seq))
    logger.info("Analyzer type: (%s)", type(analyzer).__name__)

    if type(analyzer).__name__=="CFGAnalyzer":
        analyzer.analyze(chat.last_utterance)
    elif type(analyzer).__name__=="spacyAnalyzer":
        analyzer.analyze(chat.last_utterance, speaker, hearer)

    if not chat.last_utterance.triples:
        reply = choice(ELOQUENCE)
        reply_list.append(reply)
    else:
        for extracted_triple in chat.last_utterance.triples:
            c_util.add_uri_to_triple(extracted_triple)
            capsule = c_util.scenario_utterance_to_capsule(scenario,place_id,location, textSignal,speaker, extracted_triple)
            capsule_list.append(capsule)
            logger.info("Triple: (%s)", extracted_triple)
            logger.info("Capsule: (%s)", capsule)
            try:
                response = my_brain.update(capsule, reason_types=True, create_label=True)
                response_json = brain_response_to_json(response)
                reply = replier.reply_to_statement(response_json, proactive=True, persist=True)
                response_list.append(response_json)
                reply_list.append(reply)
            except:
                logger.info("Error from KG: (%s)", response)

    response_list.append(response_json)


    return capsule_list, reply_list, response_list

def process_statement_and_reply(scenario: Scenario,
                           place_id: str,
                           location: str,
                           human_id: str,
                           textSignal: TextSignal,
                           chat: Chat,
                           analyzer: CFGAnalyzer,
                           print_details:False):
    reply_list = []
    capsule_list = []
    ### Next, we get all possible triples
    chat.add_utterance(c_util.seq_to_text(textSignal.seq))
    analyzer.analyze(chat.last_utterance)

    if print_details:
            print('Last utterance:', c_util.seq_to_text(textSignal.seq))

    if not chat.last_utterance.triples:
        reply = choice(ELOQUENCE)
        reply_list.append(reply)
    else:
        reply_list = chat.last_utterance.triples

    return capsule_list, reply_list

def process_text_spacy_and_reply(scenario: Scenario,
                           place_id: str,
                           location: str,
                           speaker: str,
                           hearer:str,
                           textSignal: TextSignal,
                           replier: LenkaReplier,
                           my_brain: LongTermMemory,
                           nlp,
                           print_details:False):
    reply_list = []
    response_list = []
    response = None
    ### We first add the mentions for any entities to the signal
    entities = t_util.add_ner_annotation_with_spacy(textSignal, nlp)
    subject_objects = t_util.add_np_annotation_with_spacy(textSignal, nlp, speaker, hearer)
    if print_details:
        print('Entities', entities)
        print('Subject_and_objects', subject_objects)

    if entities is None and subject_objects is None:
        reply = choice(ELOQUENCE)
        reply_list.append(reply)
    if len(entities)>0:
        for entity in entities:
            capsule = c_util.scenario_text_mention_to_capsule(scenario,
                                                              place_id,
                                                              location,
                                                              textSignal,
                                                              speaker,
                                                              entity,
                                                              "denotedIn",
                                                              textSignal.id)


            if print_details:
                print('Entity Capsule:')
                pprint.pprint(capsule)

            try:
                response = my_brain.update(capsule, reason_types=True, create_label=True)
                response_json = brain_response_to_json(response)
                reply = replier.reply_to_statement(response_json, proactive=True, persist=True)
                response_list.append(response_json)
                reply_list.append(reply)
                if print_details:
                    print('Entity reply', reply)
            except:
                print('Error:', response)
    if len(subject_objects)>0:
        for np in subject_objects:
            capsule = c_util.scenario_text_mention_to_capsule(scenario,
                                                              place_id,
                                                              location,
                                                              textSignal,
                                                              speaker,
                                                              np,
                                                              "denotedIn",
                                                              textSignal.id)


            if print_details:
                print('Subj/Obj Capsule:')
                pprint.pprint(capsule)

            try:
                response = my_brain.update(capsule, reason_types=True, create_label=True)
                response_json = brain_response_to_json(response)
                reply = replier.reply_to_statement(response_json, proactive=True, persist=True)
                reply_list.append(reply)
                response_list.append(response)
                if print_details:
                    print('Sub/Obj reply', reply)

            except:
                print('Error:', response)

    return reply_list, response_list

def process_triple_spacy_and_reply(scenario: Scenario,
                           place_id: str,
                           location: str,
                           speaker: str,
                           hearer:str,
                           textSignal: TextSignal,
                           replier: LenkaReplier,
                           my_brain: LongTermMemory,
                           nlp,
                           print_details:False):
    reply_list = []
    response_list = []
    response = None
    triples = t_util.get_subj_amod_triples_with_spacy(textSignal, nlp, speaker, hearer)
    triples.extend(t_util.get_subj_obj_triples_with_spacy(textSignal, nlp, speaker, hearer))
    if print_details:
        print('Triples', triples)

    if triples is None:
        reply = choice(ELOQUENCE)
        reply_list.append(reply)
    else:
        for triple in triples:
            capsule = c_util.scenario_text_mention_to_capsule(scenario,
                                                              place_id,
                                                              location,
                                                              textSignal,
                                                              speaker,
                                                              triple[1],
                                                              "hasState",
                                                              triple[2])
            if print_details:
                print('Triple spacy Capsule:')
                pprint.pprint(capsule)

            try:
                response = my_brain.update(capsule, reason_types=True, create_label=True)
                response_json = brain_response_to_json(response)
                reply = replier.reply_to_statement(response_json, proactive=True, persist=True)
                response_list(response_json)
                reply_list.append(reply)
                if print_details:
                    print('Triple spacy reply', reply)

            except:
                print('Error:', response)

    return reply_list, response_list



