#!/usr/bin/env python2
from unigram import uwseg

if __name__=='__main__':
    import sys
    from time import time
    t0 = time()
    infile = sys.argv[1]
    u = uwseg(infile)
    u.do_training()
    print "time:", time() - t0
