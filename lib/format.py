# -*- coding: utf-8 -*-

# Format benchmark data for display.

import math

def statsHeader():
    return "%-8s  %-8s  %-8s  %-6s  %-6s  %-6s  %-7s" % (
        "Min", "Mean", "Max", "CofV", "Runs", "Change", "P-value")

def formatFloat(width, x):
    # General purpose number format that fits the most significant
    # digits possible in |width|. Only uses scientific notation if
    # necessary.
    assert width >= 5
    s = "%*.*g" % (width, width - 1, x)
    if len(s) <= width:
        return s
    return "%*.*g" % (width, width - 5, x)

def formatStats(stats, comp=None):
    diff = formatFloat(8, comp.diff) if comp else ""
    change = "%5.1f%%" % (comp.factor *
                          100) if comp and comp.factor != None else ""
    pvalue = "%7.2f" % comp.pvalue if comp and comp.pvalue != None else ""

    return "%8s  %8s  %8s  %5.1f%%  %6d  %6s  %7s" % (formatFloat(
        8, stats.min), formatFloat(8, stats.mean), formatFloat(
            8, stats.max), stats.cofv * 100, stats.count, change, pvalue)

def compactStatsHeader(withComparison):
    header = "%-8s  %-6s" % ("Mean", "CofV")
    if withComparison:
        header += "  %-6s  %-7s" % ("%", "P-value")
    return header

def formatCompactStats(stats, comp=None):
    line = "%8s  %5.1f%%" % (formatFloat(8, stats.mean), stats.cofv * 100)

    if comp:
        percent = "%5.1f%%" % (comp.factor *
                               100) if comp.factor != None else ""
        pvalue = "%7.2f" % comp.pvalue if comp.pvalue != None else ""
        line += "  %6s  %7s" % (percent, pvalue)

    return line

def formatBox(minAll, maxAll, stats):
    width = 40
    scale = (maxAll - minAll) / (width - 1)

    def pos(x):
        assert x >= minAll
        return math.floor((x - minAll) / scale)

    maxDev = stats.mean + stats.stdv / 2
    minDev = stats.mean - stats.stdv / 2

    chars = list()
    for i in range(width):
        x = minAll + i * scale
        if x >= stats.max:
            c = ' '
        elif x >= maxDev:
            c = '-'
        elif x >= minDev:
            c = '='
        elif x >= stats.min:
            c = '-'
        else:
            c = ' '

        chars.append(c)

    chars[pos(stats.min)] = "|"
    chars[pos(stats.max)] = "|"
    chars[pos(stats.mean)] = "O"

    return ''.join(chars)

HistogramChars = u'▁▂▃▄▅▆▇'

def formatSamples(minAll, maxAll, stats):
    width = 40
    scale = (maxAll - minAll) / (width - 1)

    def pos(x):
        assert x >= minAll
        return math.floor((x - minAll) / scale)

    bins = [0] * width
    maxCount = 0
    for x in stats.samples:
        i = pos(x)
        bins[i] += 1
        maxCount = max(maxCount, bins[i])

    chars = [' '] * width
    for i in range(pos(stats.min), min(pos(stats.max) + 1, len(chars))):
        count = bins[i]
        if count != 0:
            y = math.floor((count / maxCount) * (len(HistogramChars) - 1))
            chars[i] = HistogramChars[y]

    return ''.join(chars)
