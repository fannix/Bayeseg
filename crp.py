#!/usr/bin/env python2
"""
Chinese Restraunt Process
"""

from random import choice 
import numpy as np
import random

def crp():
    alphabets = np.array(["a", "b", " "])
    dist = [0.15, 0.35, 0.5]
    alpha0 = 10.0

    N = 1000
    words = []
    w = ""
    for i in range(N):
        open_new_table = alpha0 / (len(words) + alpha0)
        if open_new_table > random.random():
            c = str(alphabets[np.random.multinomial(1, dist) == 1][0])
            if c != " ":
                w += c
            if c == " " and w:
                words.append(w)
                w = ""
        else:
            w = choice(words)
            words.append(w)
            w = ""

    f = open("unseg", 'w')
    f.write("".join(words))
    f.close()
    f = open("seg", 'w')
    f.write(" ".join(words))
    f.close()

crp()
