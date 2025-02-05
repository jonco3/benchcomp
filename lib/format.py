# -*- coding: utf-8 -*-

# Format benchmark data for display.

import math
import sys

ColumnNames = ("Min", "Mean", "Median", "Max", "CofV", "Runs", "Change*", "P-value")

def statsHeader(key=None):
    columns = map(lambda name: (name + "*") if key == name.lower() else name,
                  ColumnNames)
    return "%-8s  %-8s  %-8s  %-8s  %-6s  %-6s  %-6s  %-7s" % tuple(columns)

def formatFloat(width, x):
    # General purpose number format that fits the most significant
    # digits possible in |width|. Only uses scientific notation if
    # necessary.
    # This is tricky because e.g. %5f can yeild more than 5 characters.
    assert width >= 5
    if x is None:
        return " " * width
    s = "%*.*g" % (width, width - 1, x)
    if len(s) <= width:
        return s
    s = "%*.*g" % (width, width - 5, x)
    return s[:width]

def formatFloat2(width, x):
    assert width >= 5
    if x is None:
        return " " * width
    return "%*.2f" % (width, x)

def formatPercent(width, x):
    assert width >= 5
    if x is None:
        return " " * width
    return "%*.1f%%" % (width - 1, x)

def formatInt(width, x):
    if x is None:
        return " " * width
    return "%*i" % (width, x)

def formatStats(stats, comp, args):
    change = comp.factor * 100 if comp and comp.factor != None else None
    pvalue = comp.pvalue if comp and comp.pvalue != None else None

    fields = [formatFloat(8, stats.min), formatFloat(8, stats.mean),
              formatFloat(8, stats.median), formatFloat(8, stats.max),
              formatFloat(6, stats.cofv * 100), formatInt(6, stats.count),
              formatPercent(6, change), formatFloat2(7, pvalue)]
    delimiter = ", " if args.csv else "  "
    return delimiter.join(fields)
#    return "%8s  %8s  %8s  %8s  %5.1f%%  %6d  %6s  %7s" % data

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
