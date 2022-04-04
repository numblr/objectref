import random
import re

#import cltl.leolani.talk as talk
from cltl.leolani.api import Leolani
from cltl.reply_generation.data.sentences import GREETING, ASK_NAME, ELOQUENCE, TALK_TO_ME


VU_NAME_PHONETIC = r"\\toi=lhp\\ fraiE universitai_t Amster_dam \\toi=orth\\"

IMAGE_VU = "https://www.vu.nl/nl/Images/VUlogo_NL_Wit_HR_RGB_tcm289-201376.png"
IMAGE_SELENE = "http://wordpress.let.vupr.nl/understandinglanguagebymachines/files/2019/06/7982_02_34_Selene_Orange_Unsharp_Robot_90kb.jpg"
IMAGE_LENKA = "http://wordpress.let.vupr.nl/understandinglanguagebymachines/files/2019/06/8249_Lenka_Word_Object_Reference_106kb.jpg"
IMAGE_BRAM = "http://makerobotstalk.nl/files/2018/12/41500612_1859783920753781_2612366973928996864_n.jpg"
IMAGE_PIEK = "http://www.cltl.nl/files/2019/10/8025_Classroom_Piek.jpg"


NAME = "Leolani"
GREETING = f"Hello. I am {NAME}. How are you feeling today?"
responses = ["That makes my day.", "Don't tell it to the professor","Oh dear, I hope the professor does not hear baout this.", "Why is life so complicated?", "Humans are confusing"]


class LeolaniImpl(Leolani):

    def __init__(self):
        self.started = False

    def respond(self, statement: str) -> str:
        if not statement and not self.started:
            self.started = True
            #### Initial prompt by the system from which we create a TextSignal and store it
            GREETING = f"{random.choice(TALK_TO_ME)}"
            return GREETING

        if not statement:
            # TODO
            return

        return self._analyze(statement)

    def _reflect(self, fragment):
        tokens = fragment.lower().split()
        for i, token in enumerate(tokens):
            if token in lang.REFLECTIONS:
                tokens[i] = lang.REFLECTIONS[token]
        return ' '.join(tokens)

    def _analyze(self, statement):
        response = random.choice(responses)
        return response

#.format(*[self._reflect(g) for g in match.groups()])