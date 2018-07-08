import pynini
from morpho.transducers import buildQuery
from morpho.form import Form


EM = pynini.EncodeMapper("standard", True, True)

class Morphology(object):

    def __init__(self, _fst=None):
        self._fst = _fst or pynini.Fst()

    def __eq__(self, other):
        return pynini.equivalent(pynini.encode(self._fst, EM),
                                 pynini.encode(other._fst, EM))

    def __iter__(self):
        paths = self._fst.paths()
        return (Form.fromStrings(top, bottom) for top, bottom, _ in paths)

    def __repr__(self):
        formList = [form for form in self]
        return "<Morphology: {}>".format(formList)

    def __str__(self):
        return "\n\n".join(str(form) for form in self)

    def addForm(self, form=None, **kwargs):
        form = form or Form(**kwargs)
        self._fst.union(form.toFst()).optimize()
        # Optimize needed because path counting and equivalence testing
        # break after union otherwise. This is annoying and might be a
        # Pynini bug.

    def addRule(self, ifst):
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


