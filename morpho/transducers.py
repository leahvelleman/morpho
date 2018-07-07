# Utility FSTs. We generate these once at import time, and we optimize them
# because they'll be used frequently. This speeds up queries substantially.

import pynini

LETTER = pynini.union(*
  "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'")

LETTER_STAR = LETTER.star.optimize()

CONNECTOR = pynini.union(*"-")

RH_SEPARATOR = pynini.union(*"$ ")
LH_SEPARATOR = pynini.union(*"^ ")

MORPH = pynini.union(
            CONNECTOR + LETTER_STAR,
            LETTER_STAR,
            LETTER_STAR + CONNECTOR
        ).optimize()

LETTER_LIST = pynini.union(LETTER, " ").star.optimize() 

FEATURES = pynini.union(LETTER, "(", ")", " ").star.optimize() 


SIGMA = pynini.union(LETTER, "-", "(", ")", " ", "$", "^", "|").optimize()

SIGMA_STAR = SIGMA.star.optimize()

PARENTHESIZED = (
        pynini.acceptor("(") + 
        MORPH + 
        pynini.acceptor(")")
    ).optimize()


SEG_REWRITE = pynini.cdrewrite(
        pynini.transducer("", PARENTHESIZED), "", RH_SEPARATOR, SIGMA_STAR).optimize()

ADD_LEFT_PAREN = pynini.cdrewrite( 
        pynini.transducer("", "("), LH_SEPARATOR, "", SIGMA_STAR).optimize()

ADD_RIGHT_PAREN = pynini.cdrewrite(
        pynini.transducer("", ")"), "", RH_SEPARATOR, SIGMA_STAR).optimize()

GLOSS_REWRITE = pynini.compose(
        pynini.compose(ADD_LEFT_PAREN, ADD_RIGHT_PAREN),
        pynini.cdrewrite(pynini.transducer("", MORPH), "", "(",
            SIGMA_STAR)).optimize()

def buildQuery(segmentation=None, gloss=None, features=None):
    if segmentation is not None:
        segAcceptor = "^" + toAcceptor(segmentation) + "$"
        segQuery = (pynini.compose(
                                segAcceptor, 
                                SEG_REWRITE,
                             ).project(project_output = True) + 
                      FEATURES + "|").optimize()
    else:
        segQuery = SIGMA_STAR

    if gloss is not None:
        glossAcceptor = "^" + toAcceptor(gloss) + "$"
        glossQuery = (pynini.compose(
                                glossAcceptor,
                                GLOSS_REWRITE,
                            ).project(project_output = True) +
                      FEATURES + "|").optimize()
    else:
        glossQuery = SIGMA_STAR

    if features is not None:
        featQuery = "^" + SIGMA_STAR + "$" + toAcceptor(features) + "|"
    else:
        featQuery = SIGMA_STAR

    result = pynini.intersect(segQuery, glossQuery)
    result = pynini.intersect(result, featQuery)
    return result

def toAcceptor(obj):
    if obj is None:
        return None
    if isinstance(obj, pynini.Fst):
        return obj
    if isinstance(obj, list):
        obj = " ".join(obj)
    if isinstance(obj, dict):
        obj = " ".join(sorted("{}({})".format(k,v) 
            for k, v in obj.items()))
    return pynini.acceptor(obj)


