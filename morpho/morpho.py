from functools import total_ordering
import pynini

# Utility FSTs. We generate these once at import time, and we optimize them
# because they'll be used frequently. This speeds up queries substantially.

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


class Form(object):
    def __init__(self, 
            lemmaMorphemes=None,
            lemmaSegmentation=None,
            lemmaGloss=None, 
            morphemes=None,
            segmentation=None, 
            gloss=None, 
            features = None, 
            **kwargs):

        if lemmaMorphemes:
            assert not lemmaSegmentation and not lemmaGloss
            lemmaSegmentation, lemmaGloss = unzip(lemmaMorphemes)
            lemmaSegmentation = list(lemmaSegmentation)
            lemmaGloss = list(lemmaGloss)
        if morphemes:
            assert not segmentation and not gloss
            segmentation, gloss = unzip(morphemes)
            segmentation = list(segmentation)
            gloss = list(gloss)
        self.lemmaSegmentation = lemmaSegmentation or []
        self.lemmaGloss = lemmaGloss or []
        self.segmentation = segmentation or []
        self.gloss = gloss or []
        #self.features = {**features, **kwargs}
        self.features = features or kwargs

    @classmethod
    def fromStrings(cls, top, bottom):
        lemmaMorphemes, _ = breakFstString(top)
        morphemes, features = breakFstString(bottom)
        return cls(lemmaMorphemes=lemmaMorphemes,
                   morphemes=morphemes,
                   features=features)

    def toStrings(self):
        lemmaMorphemes = zip(self.lemmaSegmentation, self.lemmaGloss)
        morphemes = zip(self.segmentation, self.gloss)
        features = self.features
        topString = makeFstString(lemmaMorphemes, features)
        bottomString = makeFstString(morphemes, features)
        return topString, bottomString
        

    @classmethod
    def fromFst(cls, fst):
        fst = fst.copy()                # We're going to destructively
                                        # project it in a minute, so we need a
                                        # copy.
        bottomString = fst.stringify()
        fst.project(project_output=False)
        topString = fst.stringify()
        return cls.fromStrings(top=topString, bottom=bottomString)


    def toFst(self):
        topString, bottomString = self.toStrings()
        return pynini.transducer(topString, bottomString)


    @total_ordering
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key() == other._key()

    @total_ordering
    def __gt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key() > other._key()

    def __str__(self):
        return self.text

    def __repr__(self):
        return ('Form(segmentation={0}, gloss={1}, ' +
                'lemmaSegmentation={2}, lemmaGloss={3}, ' + 
                'features={4})').format(
                        self.segmentation, 
                        self.gloss, 
                        self.lemmaSegmentation, 
                        self.lemmaGloss, 
                        self.features)

    @property
    def morphemes(self):
        return list(zip(self.segmentation, self.gloss))

    @property
    def lemmaMorphemes(self):
        return list(zip(self.lemmaSegmentation, self.lemmaGloss))

    @property
    def text(self):
        return "".join([s.strip("-") for s in self.segmentation])

    @property
    def lemmaText(self):
        return "".join([s.strip("-") for s in self.lemmaSegmentation])

    def _key(self):
        return self.text + " " + str(self.toStrings())

def unzip(listOfPairs):
    pairOfLists = tuple(zip(*listOfPairs))
    if len(pairOfLists) == 1:
        pairOfLists = [pairOfLists[0], ()]
    return pairOfLists

def makeFstString(morphemes, features):
    fItems = [(k, features[k]) for k in sorted(features)]
    morphemeString = " ".join(["{}({})".format(segment, gloss)
                                for segment, gloss in morphemes])
    featureString = " ".join(["{}({})".format(feature, value)
                                for feature, value in fItems])
    totalString = "^" + morphemeString + "$" + featureString + "|"
    return totalString

def breakFstString(s):
    morphemeString, featureString = s.strip("^").strip("|").split("$")
    morphemes = [tuple(pair.strip(")").split("(")) 
                    for pair in morphemeString.split(" ")]
    features = [tuple(pair.strip(")").split("(")) 
                    for pair in featureString.split(" ")]
    if features == [('',)]:
        features = {}
    else:
        features = {k: v for k, v in features}
    return morphemes, features



EM = pynini.EncodeMapper("standard", True, True)

class Morphology(object):

    def __init__(self, _fst=None):
        self._fst = _fst or pynini.Fst()

    def __eq__(self, other):
        return pynini.equivalent(pynini.encode(self._fst, EM),
                                 pynini.encode(other._fst, EM))

    def add_form(self, form=None, **kwargs):
        form = form or Form(**kwargs)
        self._fst.union(form.toFst()).optimize()
        # Optimize needed because path counting and equivalence testing
        # break after union otherwise. This is annoying and might be a
        # Pynini bug.

    def add_rule(self, ifst):
        self._fst = pynini.compose(self._fst, ifst)

    def query(self, lemmaSegmentation=None, lemmaGloss=None, 
            segmentation=None, gloss=None, features=None, 
            **kwargs):
        #features = {**features, **kwargs}
        topQueryFst = buildQuery(segmentation=lemmaSegmentation,
                                 gloss=lemmaGloss,
                                 features=features)
        bottomQueryFst = buildQuery(segmentation=segmentation,
                                    gloss=gloss,
                                    features=features)
        result = pynini.compose(topQueryFst, self._fst)
        result = pynini.compose(result, bottomQueryFst)
        return [Form.fromStrings(top, bottom) 
                for top, bottom, _ in result.paths()]

class Condition(object):
    def __init__(self, text=None, gloss=None, segmentation=None):
        self._fst = query(text=text, gloss=gloss, segmentation=segmentation)

    def then(self, ifst):
        return pynini.compose(self._fst, ifst)

def when(*args, **kwargs):
    return Condition(*args, **kwargs)

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

def suffix(segmentation, gloss):
    morphemes = zip(segmentation, gloss)
    morphemes_string = " ".join("{0}({1})".format(t, g) for t, g in morphemes)
    return (sigma_star + 
            pynini.transducer("", morphemes_string) + 
            pynini.acceptor("|") +
            sigma_star)


def ignoring(lhs, rhs):
    target = lhs.copy()
    for lhstate in lhs.states():
        start_of_loop = target.num_states()
        for rhstate in rhs.states():
            target.add_state()
            for arc in rhs.arcs(rhstate):
                target.add_arc(start_of_loop+rhstate,
                        pynini.Arc(arc.ilabel, arc.olabel, arc.weight,
                            start_of_loop+arc.nextstate))
            if rhs.final(rhstate) != pynini.Weight.Zero(rhs.weight_type()):
                target.add_arc(start_of_loop+rhstate, pynini.Arc(0,0,0,lhstate))
        target.add_arc(lhstate, pynini.Arc(0, 0, 0, start_of_loop))
    return target


