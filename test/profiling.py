import cProfile
import pynini
from test.utils import *

def profiling_test():
    m = Morphology()
    f = Form(segmentation=["a", "b", "c"],
             gloss=["a", "b", "c"],
             lemmaSegmentation=["a", "b", "c"],
             lemmaGloss=["a", "b", "c"])
    g = Form(segmentation=["d", "e", "f"],
             gloss=["d", "e", "f"],
             lemmaSegmentation=["d", "e", "f"],
             lemmaGloss=["d", "e", "f"])
    h = Form(segmentation=["g", "h", "i"],
             gloss=["g", "h", "i"],
             lemmaSegmentation=["g", "h", "i"],
             lemmaGloss=["g", "h", "i"])
    m.addForm(f)
    m.addForm(g)
    m.addForm(h)
    result = m.query(segmentation=["a", "b", "c"])
    assert f in result
    assert g not in result


cProfile.run("profiling_test()")
