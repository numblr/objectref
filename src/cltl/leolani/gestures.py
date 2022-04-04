from dataclasses import dataclass
from enum import Enum, auto

class GestureType(Enum):
    ABOVE = "above" 
    AFFIRMATIVE = "affirmative" 
    AFFORD = "afford" 
    AGITATED = "agitated" 
    ALL = "all" 
    ALLRIGHT = "allright" 
    ALRIGHT = "alright" 
    ANY = "any" 
    APPEASE = "appease" 
    ASHAMED = "ashamed" 
    ASSUAGE = "assuage" 
    ATTEMPER = "attemper" 
    BACK = "back" 
    BASHFUL = "bashful" 
    BECALM = "becalm" 
    BEG = "beg" 
    BESEECH = "beseech" 
    BLANK = "blank" 
    BODY_LANGUAGE = "body_language" 
    BORED = "bored" 
    BOW = "bow" 
    BUT = "but" 
    CALL = "call" 
    CALM = "calm" 
    CHOICE = "choice" 
    CHOOSE = "choose" 
    CLEAR = "clear" 
    CLOUD = "cloud" 
    COGITATE = "cogitate" 
    COOL = "cool" 
    CRAZY = "crazy" 
    DESPAIRING = "despairing" 
    DESPERATE = "desperate" 
    DISAPPOINTED = "disappointed" 
    DOWN = "down" 
    EARTH = "earth" 
    EMBARRASSED = "embarrassed" 
    EMPTY = "empty" 
    ENTHUSIASTIC = "enthusiastic" 
    ENTIRE = "entire" 
    ENTREAT = "entreat" 
    ESTIMATE = "estimate" 
    EVERY = "every" 
    EVERYONE = "everyone" 
    EVERYTHING = "everything" 
    EXALTED = "exalted" 
    EXCEPT = "except" 
    EXCITED = "excited" 
    EXPLAIN = "explain" 
    FAR = "far" 
    FIELD = "field" 
    FLOOR = "floor" 
    FORLORN = "forlorn" 
    FRIENDLY = "friendly" 
    FRONT = "front" 
    FRUSTRATED = "frustrated" 
    GENTLE = "gentle" 
    GIFT = "gift" 
    GIVE = "give" 
    GROUND = "ground" 
    HAPPY = "happy" 
    HELLO = "hello" 
    HER = "her" 
    HERE = "here" 
    HEY = "hey" 
    HI = "hi" 
    HIGH = "high" 
    HIM = "him" 
    HOPELESS = "hopeless" 
    HYSTERICAL = "hysterical" 
    I = "i" 
    IMPLORE = "implore" 
    INDICATE = "indicate" 
    JOYFUL = "joyful" 
    ME = "me" 
    MEDITATE = "meditate" 
    MODEST = "modest" 
    MOLLIFY = "mollify" 
    MY = "my" 
    MYSELF = "myself" 
    NEGATIVE = "negative" 
    NERVOUS = "nervous" 
    NO = "no" 
    NOT_KNOW = "not_know" 
    NOTHING = "nothing" 
    OFFER = "offer" 
    OK = "ok" 
    ONCE_UPON_A_TIME = "once_upon_a_time" 
    OPPOSE = "oppose" 
    OR = "or" 
    PACIFY = "pacify" 
    PEACEFUL = "peaceful" 
    PICK = "pick" 
    PLACATE = "placate" 
    PLEASE = "please" 
    PRESENT = "present" 
    PROFFER = "proffer" 
    QUIET = "quiet" 
    RAPTUROUS = "rapturous" 
    RARING = "raring" 
    REASON = "reason" 
    REFUTE = "refute" 
    REJECT = "reject" 
    ROUSING = "rousing" 
    SAD = "sad" 
    SELECT = "select" 
    SHAMEFACED = "shamefaced" 
    SHOW = "show" 
    SHOW_SKY = "show_sky" 
    SHY = "shy" 
    SKY = "sky" 
    SOOTHE = "soothe" 
    SUN = "sun" 
    SUPPLICATE = "supplicate" 
    TABLET = "tablet" 
    TALL = "tall" 
    THEM = "them" 
    THERE = "there" 
    THINK = "think" 
    TIMID = "timid" 
    TOP = "top" 
    UNACQUAINTED = "unacquainted" 
    UNCOMFORTABLE = "uncomfortable" 
    UNDETERMINED = "undetermined" 
    UNDISCOVERED = "undiscovered" 
    UNFAMILIAR = "unfamiliar" 
    UNKNOWN = "unknown" 
    UNLESS = "unless" 
    UP = "up" 
    UPSTAIRS = "upstairs" 
    VOID = "void" 
    WARM = "warm" 
    WINNER = "winner" 
    YEAH = "yeah" 
    YES = "yes" 
    YOO_HOO = "yoo-hoo" 
    YOU = "you" 
    YOUR = "your" 
    ZERO = "zero" 
    ZESTFUL = "zestful"

options = [GestureType.ABOVE,
               GestureType.AFFIRMATIVE,
               GestureType.AFFORD,
               GestureType.AGITATED,
               GestureType.ALL,
               GestureType.ALLRIGHT,
               GestureType.ALRIGHT,
               GestureType.ANY,
               GestureType.APPEASE,
               GestureType.ASHAMED,
               GestureType.ASSUAGE,
               GestureType.ATTEMPER,
               GestureType.BACK,
               GestureType.BASHFUL,
               GestureType.BECALM,
               GestureType.BEG,
               GestureType.BESEECH,
               GestureType.BLANK,
               GestureType.BODY_LANGUAGE,
               GestureType.BORED,
               GestureType.BOW,
               GestureType.BUT,
               GestureType.CALL,
               GestureType.CALM,
               GestureType.CHOICE,
               GestureType.CHOOSE,
               GestureType.CLEAR,
               GestureType.CLOUD,
               GestureType.COGITATE,
               GestureType.COOL,
               GestureType.CRAZY,
               GestureType.DESPAIRING,
               GestureType.DESPERATE,
               GestureType.DISAPPOINTED,
               GestureType.DOWN,
               GestureType.EARTH,
               GestureType.EMBARRASSED,
               GestureType.EMPTY,
               GestureType.ENTHUSIASTIC,
               GestureType.ENTIRE,
               GestureType.ENTREAT,
               GestureType.ESTIMATE,
               GestureType.EVERY,
               GestureType.EVERYONE,
               GestureType.EVERYTHING,
               GestureType.EXALTED,
               GestureType.EXCEPT,
               GestureType.EXCITED,
               GestureType.EXPLAIN,
               GestureType.FAR,
               GestureType.FIELD,
               GestureType.FLOOR,
               GestureType.FORLORN,
               GestureType.FRIENDLY,
               GestureType.FRONT,
               GestureType.FRUSTRATED,
               GestureType.GENTLE,
               GestureType.GIFT,
               GestureType.GIVE,
               GestureType.GROUND,
               GestureType.HAPPY,
               GestureType.HELLO,
               GestureType.HER,
               GestureType.HERE,
               GestureType.HEY,
               GestureType.HI,
               GestureType.HIGH,
               GestureType.HIM,
               GestureType.HOPELESS,
               GestureType.HYSTERICAL,
               GestureType.I,
               GestureType.IMPLORE,
               GestureType.INDICATE,
               GestureType.JOYFUL,
               GestureType.ME,
               GestureType.MEDITATE,
               GestureType.MODEST,
               GestureType.MOLLIFY,
               GestureType.MY,
               GestureType.MYSELF,
               GestureType.NEGATIVE,
               GestureType.NERVOUS,
               GestureType.NO,
               GestureType.NOT_KNOW,
               GestureType.NOTHING,
               GestureType.OFFER,
               GestureType.OK,
               GestureType.ONCE_UPON_A_TIME,
               GestureType.OPPOSE,
               GestureType.OR,
               GestureType.PACIFY,
               GestureType.PEACEFUL,
               GestureType.PICK,
               GestureType.PLACATE,
               GestureType.PLEASE,
               GestureType.PRESENT,
               GestureType.PROFFER,
               GestureType.QUIET,
               GestureType.RAPTUROUS,
               GestureType.RARING,
               GestureType.REASON,
               GestureType.REFUTE,
               GestureType.REJECT,
               GestureType.ROUSING,
               GestureType.SAD,
               GestureType.SELECT,
               GestureType.SHAMEFACED,
               GestureType.SHOW,
               GestureType.SHOW_SKY,
               GestureType.SHY,
               GestureType.SKY,
               GestureType.SOOTHE,
               GestureType.SUN,
               GestureType.SUPPLICATE,
               GestureType.TABLET,
               GestureType.TALL,
               GestureType.THEM,
               GestureType.THERE,
               GestureType.THINK,
               GestureType.TIMID,
               GestureType.TOP,
               GestureType.UNACQUAINTED,
               GestureType.UNCOMFORTABLE,
               GestureType.UNDETERMINED,
               GestureType.UNDISCOVERED,
               GestureType.UNFAMILIAR,
               GestureType.UNKNOWN,
               GestureType.UNLESS,
               GestureType.UP,
               GestureType.UPSTAIRS,
               GestureType.VOID,
               GestureType.WARM,
               GestureType.WINNER,
               GestureType.YEAH,
               GestureType.YES,
               GestureType.YOO_HOO,
               GestureType.YOU,
               GestureType.YOUR,
               GestureType.ZERO,
               GestureType.ZESTFUL]

def main():
    print((GestureType(2)) )
if __name__ == '__main__':
    main()
