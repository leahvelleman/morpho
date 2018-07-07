from functools import total_ordering

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

