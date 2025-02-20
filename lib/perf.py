# -*- coding: utf-8 -*-

# Run executable under linux perf

# todo: check perf available

import re

def updateCommandForPerf(args, cmd):
    perf = 'simpleperf' if args.android else 'perf'
    events = [
        'context-switches',
        'cpu-migrations',
        'instructions',
        'stalled-cycles-frontend',
        'stalled-cycles-backend'
    ]
    if args.android:
        events = events + [
            'cpu-cycles',
            'bus-cycles',
            'branch-misses',
            'dTLB-load-misses',
            'L1-dcache-load-misses',
            'L1-dcache-store-misses',
            'raw-dtlb-walk',
            'raw-inst-retired',
            'page-faults'
        ]
    else:
        events = events + [
            'uops_dispatched',
            'uops_retired',
            'all_dc_accesses',
            'l1_dtlb_misses',
            'l2_cache_accesses_from_dc_misses'
        ]
    return [perf, 'stat', '-e', ','.join(events)] + cmd

def parsePerfOutput(result, stdout, stderr, args):
    if args.android:
        text = stdout
    else:
        text = stderr

    sawHeader  = False
    for line in text.splitlines():
        if not sawHeader:
            if 'Performance counter' not in line:
                continue
            sawHeader = True

        match = re.match(r'\s+([\d\.,]+)\s+([\w _-]+)', line)
        if not match:
            continue

        value, key = match.group(1), match.group(2).strip()
        value = float(value.replace(',', ''))
        result[key] = value
