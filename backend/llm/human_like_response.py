import re
import random

# Contractions map — safe, non-disruptive post-processing
_CONTRACTIONS = {
    r"\bI am\b": "I'm",
    r"\byou are\b": "you're",
    r"\bhe is\b": "he's",
    r"\bshe is\b": "she's",
    r"\bit is\b": "it's",
    r"\bwe are\b": "we're",
    r"\bthey are\b": "they're",
    r"\bI have\b": "I've",
    r"\byou have\b": "you've",
    r"\bwe have\b": "we've",
    r"\bthey have\b": "they've",
    r"\bI will\b": "I'll",
    r"\byou will\b": "you'll",
    r"\bwe will\b": "we'll",
    r"\bthey will\b": "they'll",
    r"\bdo not\b": "don't",
    r"\bdoes not\b": "doesn't",
    r"\bdid not\b": "didn't",
    r"\bcannot\b": "can't",
    r"\bcould not\b": "couldn't",
    r"\bwould not\b": "wouldn't",
    r"\bshould not\b": "shouldn't",
    r"\bis not\b": "isn't",
    r"\bare not\b": "aren't",
    r"\bhave not\b": "haven't",
    r"\bhas not\b": "hasn't",
    r"\bwas not\b": "wasn't",
    r"\bwere not\b": "weren't",
}

# Phrases that scream AI — always at the very start of a response
_AI_OPENER_PATTERNS = [
    r"^I understand (that |how |what |why )",
    r"^I can (see|hear|tell|sense) that ",
    r"^It sounds like (you|your)",
    r"^I appreciate (you|your|that)",
    r"^Thank you for sharing",
    r"^Thank you for (being|telling|opening)",
    r"^I'm sorry to hear that\.",
    r"^That must be (really |very |so )?(hard|difficult|tough|challenging)",
    r"^Of course[,!]",
    r"^Absolutely[,!]",
    r"^Certainly[,!]",
    r"^Great question",
    r"^That's a great",
]

# Natural reaction openers — used to replace stripped AI openers
_REACTION_OPENERS = [
    "Oh.", "Hmm.", "Yeah.", "Ugh.", "Wait.", "Hey.",
    "Okay.", "Hm.", "Oh wow.", "Right.", "Ah.",
]


def _strip_ai_opener(text: str) -> str:
    """
    If response opens with a robotic AI opener, strip the opening sentence
    and optionally prepend a natural reaction word.
    Only fires on clear AI-isms, not on natural human starts.
    """
    for pattern in _AI_OPENER_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            # Find end of first sentence
            end = re.search(r'[.!?…]\s+', text)
            if end and end.start() < 120:
                remainder = text[end.end():].strip()
                if remainder:
                    # 40% chance to prepend a reaction opener for naturalness
                    if random.random() < 0.4:
                        opener = random.choice(_REACTION_OPENERS)
                        return f"{opener} {remainder}"
                    return remainder
            break  # Pattern matched but sentence too long — leave it alone
    return text


def make_human_like(response: str, user_input: str = "") -> str:
    """
    Post-processing pipeline:
    1. Strip robotic AI opener sentences
    2. Apply contractions
    Safe — never mutates the meaning of a response, only strips/replaces clear AI-isms.
    """
    if not response:
        return response

    result = _strip_ai_opener(response)

    for pattern, replacement in _CONTRACTIONS.items():
        result = re.sub(pattern, replacement, result)

    return result
