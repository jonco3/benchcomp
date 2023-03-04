# -*- coding: utf-8 -*-

# Run executable under linux perf

# todo: check perf available

import re

def updateCommandForPerf(args, cmd):
    events = [
        'context-switches',
        'cpu-migrations',
        'instructions',
        'cycles',
        'stalled-cycles-frontend',
        'stalled-cycles-backend',
        'uops_dispatched',
        'uops_retired',
        'all_dc_accesses',
        'l1_dtlb_misses',
        'l2_cache_accesses_from_dc_misses',
    ]
    return ['perf', 'stat', '-e', ','.join(events)] + cmd

def parsePerfOutput(result, text):
    for line in text.splitlines():
        match = re.match(r'\s+([\d\.,]+) ([\w -]+)', line)
        if not match:
            continue

        value, key = match.group(1), match.group(2).strip()
        value = float(value.replace(',', ''))

        result[key] = value
