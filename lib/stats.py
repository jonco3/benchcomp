# -*- coding: utf-8 -*-

# Caclulate some basic statistics on a list of samples.

import math
from scipy import stats
import statistics
import warnings

class Stats:
    def __init__(self, samples):
        self.samples = samples
        self.count = len(samples)
        self.min = min(samples)
        self.max = max(samples)
        self.median = statistics.median(samples)
        self.mean = statistics.mean(samples)
        self.stdv = statistics.stdev(samples,
                                     self.mean) if self.count > 1 else 0
        self.cofv = self.stdv / self.mean if self.mean != 0 else 0

class Comparison:
    def __init__(self, diff, factor, pvalue):
        self.diff = diff
        self.factor = factor
        self.pvalue = pvalue

def compareStats(a, b, key='mean'):
    if b is None or a is b:
        return None

    if not hasattr(a, key) or not hasattr(b, key):
        raise "Bad key: " + key

    x = getattr(a, key)
    y = getattr(b, key)

    diff = x - y

    factor = None
    if y != 0:
        factor = diff / y

    p = None
    if a.count > 1 and b.count > 1 and a.mean != b.mean:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = stats.ttest_ind(a.samples,
                                b.samples,
                                equal_var=False,
                                trim=0.2).pvalue

    return Comparison(diff, factor, p)
