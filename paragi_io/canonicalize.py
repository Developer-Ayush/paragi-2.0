import spacy
from typing import Optional, Tuple

# Initialize spaCy once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError("Run: python -m spacy download en_core_web_sm")

def canonicalize(text: str) -> str:
    """
    Pipeline:
    1. Lowercase
    2. Lemmatize (spaCy)
    3. Remove stop words that are not named entities
    4. Return canonical form
    """
    if not text:
        return ""
    doc = nlp(text.lower())
    result = []
    for token in doc:
        # Keep if not stop word OR if part of an entity
        if not token.is_stop or token.ent_type_:
            result.append(token.lemma_)

    res = " ".join(result).strip()
    # print(f"DEBUG: canonicalize('{text}') -> '{res}'")
    return res if res else text.lower().strip()

def extract_triple(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Attempt to extract (subject, relation, object) from a natural language statement.
    Use spaCy dependency parse.
    """
    doc = nlp(text)
    subj = ""
    obj = ""
    rel = ""

    for token in doc:
        if "subj" in token.dep_:
            subj = token.text
        if "obj" in token.dep_ or "pobj" in token.dep_:
            obj = token.text
        if token.pos_ == "VERB":
            rel = token.lemma_.upper()
            # In questions, sometimes the object is the ROOT verb or a dependent
            if not obj:
                for child in token.children:
                    if "obj" in child.dep_:
                        obj = child.text
            # If still no obj, maybe the verb is what we're asking about?
            # E.g. "does fire burn" -> subj=fire, rel=BURN, obj=???
            # In this case we might want to return (fire, CAUSES, burn) if burn is the ROOT
            if not obj and token.dep_ == "ROOT":
                obj = token.text

    if subj and obj:
        if not rel:
            rel = "RELATED_TO"
        return (canonicalize(subj), rel, canonicalize(obj))

    return None

def semantic_distance(label_a: str, label_b: str) -> float:
    """
    Use spaCy word vectors to compute distance between two node labels.
    Return value 0.0 (identical) to 1.0 (completely unrelated).
    """
    doc1 = nlp(label_a)
    doc2 = nlp(label_b)
    if not doc1.vector_norm or not doc2.vector_norm:
        return 1.0 if label_a != label_b else 0.0

    similarity = doc1.similarity(doc2)
    return 1.0 - similarity
