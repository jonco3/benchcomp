# gcprofile
#
# Summarise GC profiling information from log data.

import math
import re
import statistics

from resultkey import ResultKey

# Result keys.
FIRST_MAJOR_GC = ResultKey('First major GC')
HEAP_SIZE_KB_AT_FIRST_MAJOR_GC = ResultKey('Heap size / KB at first major GC')
MAJOR_GC_COUNT = ResultKey('Major GC count')
TOTAL_BUDGET_OVERRUN = ResultKey('Total budget overrun')
MAX_GC_HEAP_SIZE_KB = ResultKey('Max GC heap size / KB')
MEDIAN_GC_HEAP_SIZE_KB = ResultKey('Median GC heap size / KB')
MAX_MALLOC_HEAP_SIZE_KB = ResultKey('Max malloc heap size / KB')
MEDIAN_MALLOC_HEAP_SIZE_KB = ResultKey('Median malloc heap size / KB')
MAX_NURSERY_SIZE_KB = ResultKey('Max nursery size / KB')
MEDIAN_NURSERY_SIZE_KB = ResultKey('Median nursery size / KB')
ALLOC_TRIGGER_SLICES = ResultKey('ALLOC_TRIGGER slices')
TOO_MUCH_MALLOC_SLICES = ResultKey('TOO_MUCH_MALLOC slices')
FULL_STORE_BUFFER_NURSERY_COLLECTIONS = ResultKey('Full store buffer nursery collections')
MEAN_FULL_NURSERY_PROMOTION_RATE = ResultKey('Mean full nusery promotion rate')
MAJOR_GC_CYCLE_COUNT = ResultKey('Major GC cycle count')
MEAN_MAJOR_GC_CYCLE_DURATION = ResultKey('Mean major GC cycle duration')
MAJOR_GC_SLICE_COUNT = ResultKey('Major GC slice count')
MAJOR_GC_TIME = ResultKey('Major GC time')
MEAN_MAJOR_GC_SLICE_TIME = ResultKey('Mean major GC slice time')
MINOR_GC_COUNT = ResultKey('Minor GC count')
MINOR_GC_TIME = ResultKey('Minor GC time')
MEAN_MINOR_GC_TIME = ResultKey('Mean minor GC time')
TOTAL_GC_TIME = ResultKey('Total GC time')
PARALLEL_MARKING_DONATIONS_PER_COLLECTION = ResultKey('Parallel marking donations per collection')
GEOMETRIC_MEAN_MARK_RATE = ResultKey('Geometric mean mark rate')
MAX_BUFFER_HEAP_SIZE_KB = ResultKey('Max buffer heap size / KB')
MEDIAN_BUFFER_HEAP_SIZE_KB = ResultKey('Median buffer heap size / KB')
MEDIAN_BUFFER_HEAP_DENSITY_PERCENT = ResultKey('Median buffer heap density %')

PHASE_FIELD_NAMES = ['bgwrk', 'waitBG', 'prep', 'mark', 'sweep', 'cmpct']
TOTAL_MAJOR_GC_TIME_IN_PHASE = {
    name: ResultKey('Total major GC time in phase ' + name)
    for name in PHASE_FIELD_NAMES
}

# Detect whether we're currently running a raptor test, or between
# tests.
StartTestText = 'Testing url'
EndTestText = 'PageCompleteCheck returned true'

def summariseProfile(text, result, categories, filterMostActiveRuntime=True):
    majorFields, majorData, minorFields, minorData, testCount = parseOutput(
        text)

    if len(minorData) == 0 and len(majorData) == 0:
        return  # No data.

    if filterMostActiveRuntime:
        runtime = findMostActiveRuntimeByFrequency(majorData + minorData)
        majorData = filterByRuntime(majorData, runtime)
        minorData = filterByRuntime(minorData, runtime)

    removeShutdownGCs(majorFields, majorData, minorFields, minorData)

    summariseAllData(result, majorFields, majorData, minorFields, minorData,
                     categories)

    summariseBufferAllocatorData(result, majorFields, majorData)

    if 'major' in categories:
        # Useful for scheduling changes only.
        # findFirstMajorGC(result, majorFields, majorData)

        # These are super noisy and probably not that useful.
        summarisePhaseTimes(result, majorFields, majorData)
        summariseParallelMarking(result, majorFields, majorData)

def removeShutdownGCs(majorFields, majorData, minorFields, minorData):
    reasonField = majorFields.get('Reason')
    while majorData and isShutdownReason(majorData[-1][reasonField]):
        majorData.pop()
    if majorData and majorData[-1][reasonField] == "FINISH_GC":
        majorData.pop()

    reasonField = minorFields.get('Reason')
    if minorData and minorData[-1][reasonField] == "EVICT_NURSERY":
        minorData.pop()

def isShutdownReason(reason):
    return 'SHUTDOWN' in reason or 'DESTROY' in reason or reason == 'ROOTS_REMOVED'

def findFirstMajorGC(result, majorFields, majorData):
    timestampField = majorFields.get('Timestamp')
    sizeField = majorFields.get('SizeKB')
    totalField = majorFields.get('total')
    statesField = majorFields.get('States')

    for line in majorData:
        # Skip collections where we don't collect anything.
        if float(line[totalField]) == 0 and line[statesField] == "0 -> 0":
            continue

        result[FIRST_MAJOR_GC] = float(line[timestampField])
        result[HEAP_SIZE_KB_AT_FIRST_MAJOR_GC] = int(line[sizeField])
        break

def summarisePhaseTimes(result, majorFields, majorData):
    reasonField = majorFields.get('Reason')
    fieldNames = PHASE_FIELD_NAMES
    fields = [majorFields.get(name) for name in fieldNames]
    totals = [0 for name in fieldNames]

    for line in majorData:
        assert not isShutdownReason(line[reasonField])
        for i in range(len(fields)):
            value = line[fields[i]]
            if value:
                totals[i] += float(value)

    for i in range(len(fields)):
        result[TOTAL_MAJOR_GC_TIME_IN_PHASE[fieldNames[i]]] = totals[i]

def countMajorGCs(result, majorFields, majorData):
    statesField = majorFields.get('States')
    reasonField = majorFields.get('Reason')

    count = 0
    for line in majorData:
        assert not isShutdownReason(line[reasonField])
        if "0 ->" in line[statesField]:
            count += 1

    result[MAJOR_GC_COUNT] = count

def summariseIncrementalGCDuration(majorFields, majorData):
    statesField = majorFields.get('States')
    reasonField = majorFields.get('Reason')
    timestampField = majorFields.get('Timestamp')

    count = 0
    totalTime = 0.0
    inGC = False
    startTime = None
    for line in majorData:
        if "0 ->" in line[statesField]:
            assert not inGC
            inGC = True
            startTime = float(line[timestampField])
        if "-> 0" in line[statesField]:
            assert inGC
            inGC = False
            count += 1
            duration = float(line[timestampField]) - startTime
            totalTime += duration
            startTime = None

    return count, totalTime * 1000

def extractHeapSizeData(text):
    majorFields, majorData, _, _, _ = parseOutput(text)

    pidField = majorFields.get('PID')
    runtimeField = majorFields.get('Runtime')
    timestampField = majorFields.get('Timestamp')
    sizeField = majorFields.get('SizeKB')
    assert pidField is not None
    assert runtimeField is not None
    assert sizeField is not None

    runtimes = dict()

    # Estimate global time from times in previous traces.
    latestTimestamp = None
    startTimes = dict()

    for line in majorData:
        key = (line[pidField], line[runtimeField])
        timestamp = float(line[timestampField])
        size = int(line[sizeField])

        if key not in runtimes:
            runtimes[key] = list()
            if latestTimestamp is None:
                startTimes[key] = 0
                latestTimestamp = timestamp
            else:
                startTimes[key] = max(latestTimestamp - timestamp, 0)
            runtimes[key].append((startTimes[key], 0))

        timestamp += startTimes[key]
        latestTimestamp = timestamp

        runtimes[key].append((timestamp, size))

    return runtimes

def parseOutput(text):
    majorFields = None
    majorSpans = None
    majorData = list()
    minorFields = None
    minorSpans = None
    minorData = list()

    inTest = False
    testCount = 0
    testNum = 0

    for line in text.splitlines():
        if StartTestText in line:
            assert not inTest
            inTest = True
            testCount += 1
            testNum = testCount
            continue

        if inTest and EndTestText in line:
            inTest = False
            testNum = 0
            continue

        if 'MajorGC:' in line:
            line = line.split('MajorGC: ', maxsplit=1)[1]

            if 'TOTALS:' in line:
                continue
            elif line.startswith('PID'):
                if not majorFields:
                    majorFields, majorSpans = parseHeaderLine(line)
                continue
            else:
                fields = splitWithSpans(line, majorSpans)

            fields.append(testNum)
            if len(fields) != len(majorFields):
                print("Skipping garbled profile line")
                continue

            majorData.append(fields)
            continue

        if 'MinorGC:' in line:
            line = line.split('MinorGC: ', maxsplit=1)[1]

            if 'TOTALS:' in line:
                continue
            elif line.startswith('PID'):
                if not minorFields:
                    minorFields, minorSpans = parseHeaderLine(line)
                continue
            else:
                fields = splitWithSpans(line, minorSpans)

            fields.append(testNum)
            if len(fields) != len(minorFields):
                print("Skipping garbled profile line")
                continue

            minorData.append(fields)
            continue

    return majorFields, majorData, minorFields, minorData, testCount

def parseHeaderLine(line):
    fieldMap = dict()
    fieldSpans = list()

    for match in re.finditer(r"(\w+)\s*", line):
        name = match.group(1)
        span = match.span()
        fieldMap[name] = len(fieldMap)
        fieldSpans.append(span)

    # Assumed by findMostActiveRuntime
    assert fieldMap.get('PID') == 0
    assert fieldMap.get('Runtime') == 1

    # Add our generated field:
    fieldMap['testNum'] = len(fieldMap)

    return fieldMap, fieldSpans

def splitWithSpans(line, spans):
    fields = []
    for span in spans:
        field = line[span[0]:span[1]].strip()
        fields.append(field)

    # Fix up broken printing of runtime address
    match = re.match(r"0x\s+([\w\d]+)", fields[1])
    if match:
        fields[1] = "0x" + match.group(1)

    return fields

def summariseAllData(result,
                     majorFields,
                     majorData,
                     minorFields,
                     minorData,
                     categories):
    summariseMajorMinorData(result, majorFields, majorData, minorFields,
                            minorData, categories)

    if 'major' in categories:
        result[TOTAL_BUDGET_OVERRUN] = \
        calculateBudgetOverrun(majorFields, majorData)

    if 'major' in categories and 'size' in categories:
        result[MAX_GC_HEAP_SIZE_KB] = \
            findMax(majorFields, majorData, 'SizeKB')
        result[MEDIAN_GC_HEAP_SIZE_KB] = \
            calcMedian(majorFields, majorData, 'SizeKB')
        result[MAX_MALLOC_HEAP_SIZE_KB] = \
            findMax(majorFields, majorData, 'MllcKB')
        result[MEDIAN_MALLOC_HEAP_SIZE_KB] = \
            calcMedian(majorFields, majorData, 'MllcKB')

    if 'minor' in categories and 'size' in categories:
        result[MAX_NURSERY_SIZE_KB] = \
            findMax(minorFields, minorData, 'NewKB')
        result[MEDIAN_NURSERY_SIZE_KB] = \
            calcMedian(minorFields, minorData, 'NewKB')

    if 'major' in categories and 'reason' in categories:
        result[ALLOC_TRIGGER_SLICES] = \
            len(filterByReason(majorFields, majorData, 'ALLOC_TRIGGER'))
        result[TOO_MUCH_MALLOC_SLICES] = \
            len(filterByReason(majorFields, majorData, 'TOO_MUCH_MALLOC'))

    if 'minor' in categories and 'reason' in categories:
        result[FULL_STORE_BUFFER_NURSERY_COLLECTIONS] = \
            len(filterByFullStoreBufferReason(minorFields, minorData))

    if 'minor' in categories:
        result[MEAN_FULL_NURSERY_PROMOTION_RATE] = \
            meanPromotionRate(minorFields,
                              filterByReason(minorFields, minorData, 'OUT_OF_NURSERY'))


def summariseMajorMinorData(result, majorFields, majorData, minorFields,
                            minorData, categories):
    majorCount, majorTime = summariseData(majorFields, majorData)
    minorCount, minorTime = summariseData(minorFields, minorData)
    minorTime /= 1000
    totalTime = majorTime + minorTime

    if 'major' in categories:
        incrementalCount, incrementalTime = \
            summariseIncrementalGCDuration(majorFields, majorData)
        if incrementalCount:
            result[MAJOR_GC_CYCLE_COUNT] = incrementalCount
            result[MEAN_MAJOR_GC_CYCLE_DURATION] = \
                incrementalTime / incrementalCount

        result[MAJOR_GC_SLICE_COUNT] = majorCount
        result[MAJOR_GC_TIME] = majorTime
        if majorCount:
            result[MEAN_MAJOR_GC_SLICE_TIME] = majorTime / majorCount


    if 'minor' in categories:
        result[MINOR_GC_COUNT] = minorCount
        result[MINOR_GC_TIME] = minorTime
        if minorCount:
            result[MEAN_MINOR_GC_TIME] = minorTime / minorCount

    result[TOTAL_GC_TIME] = majorTime + minorTime

def summariseData(fieldMap, data):
    reasonField = fieldMap['Reason']
    totalField = fieldMap['total']
    count = 0
    totalTime = 0
    for fields in data:
        time = float(fields[totalField])
        totalTime += time
        # experiment: skip these very short slices for major GC count
        if fields[reasonField] != 'BG_TASK_FINISHED':
            count += 1
    return count, totalTime

def calculateBudgetOverrun(majorFields, majorData):
    totalField = majorFields['total']
    budgetField = majorFields['Budget']
    totalOverrun = 0
    for record in majorData:
        total = float(record[totalField])
        if record[budgetField]:
            budget = float(record[budgetField])
            if total > budget:
                totalOverrun += total - budget
    return totalOverrun

def summariseParallelMarking(result, majorFields, majorData):
    if 'pmDons' not in majorFields or 'mkRate' not in majorFields:
        return  # No parallel marking data in profile

    donationsField = majorFields['pmDons']
    markRateField = majorFields['mkRate']

    count = 0
    donationResults = []
    markRateResults = []
    donationsTotal = 0
    logMarkRateTotal = 0
    for record in majorData:
        markRate = int(record[markRateField])
        donations = int(record[donationsField])

        # Only reported at the end of GC, otherwise zero.
        if markRate == 0:
            assert donations == 0
            continue

        count += 1
        donationResults.append(donations)
        markRateResults.append(markRate)
        donationsTotal += donations
        logMarkRateTotal += math.log(markRate)

    if count == 0:
        return

    result[PARALLEL_MARKING_DONATIONS_PER_COLLECTION] = donationsTotal / count
    result[GEOMETRIC_MEAN_MARK_RATE] = math.exp(logMarkRateTotal / count)


def summariseBufferAllocatorData(result, majorFields, majorData):
    if 'BuffKB' not in majorFields or 'BuffDns' not in majorFields:
        return

    statesField = majorFields.get('States')
    buffKBField = majorFields['BuffKB']
    buffDnsField = majorFields['BuffDns']

    sizeKBValues = []
    densityValues = []
    for record in majorData:
        if "-> 0" in record[statesField]:
            sizeKBValues.append(int(record[buffKBField]))
            densityValues.append(float(record[buffDnsField][:-1]))

    if sizeKBValues:
        result[MAX_BUFFER_HEAP_SIZE_KB] = max(sizeKBValues)
        result[MEDIAN_BUFFER_HEAP_SIZE_KB] = statistics.median(sizeKBValues)
        result[MEDIAN_BUFFER_HEAP_DENSITY_PERCENT] = statistics.median(densityValues)

# Work out which runtime we're interested in. This is a heuristic that
# may not always work.
def findMostActiveRuntimeByFrequency(data):
    lineCount = dict()
    for fields in data:
        runtime = (fields[0], fields[1])

        if runtime not in lineCount:
            lineCount[runtime] = 0

        lineCount[runtime] += 1

    mostActive = None
    maxCount = 0
    for runtime in lineCount:
        if lineCount[runtime] > maxCount:
            mostActive = runtime
            maxCount = lineCount[runtime]

    assert mostActive
    return mostActive

def filterByRuntime(data, runtime):
    return list(
        filter(lambda f: f[0] == runtime[0] and f[1] == runtime[1], data))

def filterByInTest(fields, data, inTest):
    i = fields['testNum']
    return list(filter(lambda f: (f[i] != 0) == inTest, data))

def filterByReason(fields, data, reason):
    i = fields['Reason']
    return list(filter(lambda f: f[i] == reason, data))

def filterByFullStoreBufferReason(fields, data):
    i = fields['Reason']
    return list(
        filter(lambda f: f[i].startswith('FULL') and f[i].endswith('BUFFER'),
               data))

def meanPromotionRate(fields, data):
    if len(data) == 0:
        return 0

    i = fields['PRate']
    sum = 0
    for line in data:
        rate = line[i]
        ensure(rate.endswith('%'), "Bad promotion rate" + rate)
        rate = float(rate[:-1])
        sum += rate

    return sum / len(data)

def findMax(fields, data, key):
    i = fields[key]
    result = 0

    for line in data:
        result = max(result, float(line[i]))

    return result

def calcMedian(fields, data, key):
    field = fields[key]
    samples = list(map(lambda line: float(line[field]), data))
    count = len(samples)
    if count == 0:
        return 0

    i = count // 2
    if count % 2 == 1:
        return samples[i]

    return (samples[i - 1] + samples[i]) / 2

def ensure(condition, error):
    if not condition:
        sys.exit(error)
