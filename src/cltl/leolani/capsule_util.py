from datetime import date
from emissor.representation.scenario import ImageSignal, TextSignal, Scenario


def seq_to_text(seq):
    text = ""
    for c in seq:
        text += c
    return text


def triple_to_capsule (triple: str, utterance_type:str):
    capsule = {"chat": "1",
               "turn": "1",
               "author": "me",
               "utterance": "",
               "utterance_type": utterance_type,
               "position": "",
               "context_id": "1",
               "date": date.today(),
               "place": "",
               "place_id": "",
               "country": "",
               "region": "",
               "city": "",
               "objects": [],
               "people": []
               }
    if triple:
        capsule.update(rephrase_triple_json_for_capsule(triple))  
        
    return capsule    

def scenario_utterance_to_capsule(scenario: Scenario,
                                  place_id: str,
                                  location: str,
                                  signal: TextSignal,
                                  author: str,
                                  subj: str,
                                  pred: str,
                                  obj: str):
    capsule = {"chat": scenario.id,
               "turn": signal.id,
               "author": author,
               "utterance": seq_to_text(signal.seq),
               "utterance_type": "STATEMENT",
               "position": "0-" + str(len(signal.seq)),  # TODO generate the true offset range
               "subject": {"label": subj, "type": ""},
               "predicate": {"label": pred},
               "object": {"label": obj, "type": ""},
               "context_id": scenario.context,
               ##### standard elements
               "date": date.today(),
               "place": location['city'],
               "place_id": place_id,
               "country": location['country'],
               "region": location['region'],
               "city": location['city'],
               "objects":  [],
               "people":  []
               }
    return capsule

def scenario_utterance_to_capsule(scenario: Scenario,
                                  place_id: str,
                                  location: str,
                                  signal: TextSignal,
                                  author: str,
                                  triple: str):
    capsule = {"chat": scenario.id,
               "turn": signal.id,
               "author": author,
               "utterance": seq_to_text(signal.seq),
               "utterance_type": "STATEMENT",
               "position": "0-" + str(len(signal.seq)),  # TODO generate the true offset range
               "subject": triple["subject"],
               "predicate": triple["predicate"],
               "object": triple["object"],
               'utterance_type': 'STATEMENT',
               "context_id": scenario.context,
               ##### standard elements
               "date": date.today(),
               "place": location['city'],
               "place_id": place_id,
               "country": location['country'],
               "region": location['region'],
               "city": location['city'],
               "objects":  [],
               "people":  []
               }
    return capsule

def scenario_utterance_to_capsule_with_perspective(scenario: Scenario,
                                                   place_id: str,
                                                   location: str,
                                                   signal: TextSignal,
                                                   author: str,
                                                   perspective: str,
                                                   subj: str,
                                                   pred: str,
                                                   obj: str):
    capsule = {"chat": scenario.id,
               "turn": signal.id,
               "author": author,
               "utterance": seq_to_text(signal.seq),
               "utterance_type": "STATEMENT",
               "position": "0-" + str(len(signal.seq)),  # TODO generate the true offset range
               "subject": {"label": subj, "type": "person"},
               "predicate": {"type": pred},
               "object": {"label": obj, "type": "object"},
               "context_id": scenario.context,
               ##### standard elements
               "date": date.today(),
               "place": location['city'],
               "place_id": place_id,
               "country": location['country'],
               "region": location['region'],
               "city": location['city'],
               "objects": [],
               "people": []
               }
     
    if perspective:
        capsule['perspective'] = perspective
        
    return capsule


### create a capsule for a TextSignal with a triple and perspective string
def scenario_utterance_and_triple_to_capsule(scenario: Scenario,
                                             place_id: str,
                                             location: str,
                                             signal: TextSignal,
                                             author: str,
                                             utterance_type: str,
                                             perspective: dict,
                                             triple: dict):
    
    capsule = {"chat": scenario.id,
               "turn": signal.id,
               "author": author,
               "utterance": seq_to_text(signal.seq),
               "utterance_type": utterance_type,
               "position": "0-" + str(len(signal.seq)),  # TODO generate the true offset range
               "context_id": scenario.context,
               ##### standard elements
               "date": date.today(),
               "place": location['city'],
               "place_id": place_id,
               "country": location['country'],
               "region": location['region'],
               "city": location['city'],
               "objects": [],
               "people": []
               }
    if triple:
        capsule.update(rephrase_triple_json_for_capsule(triple))
    if perspective:
        capsule['perspective'] = perspective
        
    return capsule


# Hack to make the triples compatible with the capsules
# {'subject': {'label': 'stranger', 'type': ['noun.person']},
# 'predicate': {'label': 'be', 'type': ['verb.stative']},
# 'object': {'label': 'Piek', 'type': ['noun.person']}}
def rephrase_triple_json_for_capsule(triple: dict):
    subject_type = []
    object_type = []
    predicate_type = []

    if triple['subject']['type']:
        subject_type = triple['subject']['type'][0]
    if triple['predicate']['type']:
        predicate_type = triple['predicate']['type'][0]
    if triple['object']['type']:
        object_type = triple['object']['type'][0]

    rephrase = {
        "subject": {'label': triple['subject']['label'], 'type': subject_type, 'uri':triple['uri']},
        "predicate": {'label': triple['predicate']['label'], 'type': predicate_type},
        "object": {'label': triple['object']['label'], 'type': object_type},
    }
    return rephrase

def add_uri_to_triple(triple:dict):
    uri = {'uri':None}
    triple['subject'].update(uri)
    triple['predicate'].update(uri)
    triple['object'].update(uri)
    print(triple)

def lowcase_triple_json_for_query(capsule: dict): 
    if capsule['subject']['label']:
        capsule['subject']['label'] = capsule['subject']['label'].lower()
    if capsule['predicate']['label']:
        capsule['subject']['label'] = capsule['subject']['label'].lower()
    if capsule['object']['label']:
        capsule['subject']['label'] = capsule['subject']['label'].lower()
    return capsule


###### Hardcoded capsule for perceivedBy triple for an ImageSignal
def scenario_image_perceivedBy_triple_to_capsule(scenario: Scenario,
                                                 place_id: str,
                                                 location: str,
                                                 signal: ImageSignal,
                                                 author: str,
                                                 perspective: str,
                                                 triple: str):

    reference = signal.signal.id + "#" + str(signal.bounds)  # NOT ALLOWED
    capsule = {"chat": scenario.id,
               "turn": signal.id,
               "author": author,
               "utterance": "",
               "position": "image",
               "subject": {"label": author, "type": "person"},
               "predicate": {"label": "perceivedBy"},
               "object": {"label": reference, "type": "string"},
               "context_id": scenario.context,
               ##### standard elements
               "date": date.today(),
               "place": location['city'],
               "place_id": place_id,
               "country": location['country'],
               "region": location['region'],
               "city": location['city'],
               "objects": [],
               "people": []
               }

    return capsule


def scenario_image_triple_to_capsule(scenario: Scenario,
                                     place_id: str,
                                     location: str,
                                     signal: ImageSignal,
                                     author: str,
                                     subj: str,
                                     pred: str,
                                     obj: str):

    capsule = {"chat": scenario.id,
               "turn": signal,
               "author": author,
               "utterance": "",
               "position": "image",
               "subject": {"label": subj, "type": "", "uri":None},
               "predicate": {"label": pred, "uri":None},
               "object": {"label": obj, "type": "", "uri":None},
               "context_id": scenario.context,
               "utterance_type": "STATEMENT",
               ##### standard elements
               "date": date.today(),
               "place": location['city'],
               "place_id": place_id,
               "country": location['country'],
               "region": location['region'],
               "city": location['city'],
               "objects": [],
               "people": []
               }

    return capsule

#### Leaving out the context information
def scenario_image_triple_to_capsule_without_context(scenario: Scenario,
                                     signal: ImageSignal,
                                     author: str,
                                     subj: str,
                                     pred: str,
                                     obj: str):

    capsule = {"chat": scenario.id,
               "turn": signal,
               "author": author,
               "utterance": "",
               "position": "image",
               "subject": {"label": subj, "type": "", "uri":None},
               "predicate": {"label": pred, "uri":None},
               "object": {"label": obj, "type": "", "uri":None},
               "context_id": scenario.context,
               "date": date.today(),
               "utterance_type": "STATEMENT",

               ##### standard elements
               "place": "",
               "place_id": "",
               "country": "",
               "region": "",
               "city": "",
               "objects": [],
               "people": []
               }

    return capsule


def scenario_text_mention_to_capsule(scenario: Scenario,
                                     place_id: str,
                                     location: str,
                                     signal: TextSignal,
                                     author: str,
                                     subj: str,
                                     pred: str,
                                     obj: str):

    capsule = {"chat": scenario.id,
               "turn": signal.id,
               "author": author,
               "utterance": "",
               "position": "image",
               "subject": {"label": subj, "type": "noun.person"},
               "predicate": {"label": "denotedIn"},
               "object": {"label": obj, "type": ""},
               "context_id": scenario.context,
               ##### standard elements
               "date": date.today(),
               "place": location['city'],
               "place_id": place_id,
               "country": location['country'],
               "region": location['region'],
               "city": location['city'],
               "objects": [],
               "people": []
               }

    return capsule


