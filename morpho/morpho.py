import functools
import foma


def match(*args):
    return foma.FST.wordlist(args)
