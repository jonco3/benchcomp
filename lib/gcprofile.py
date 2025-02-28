# gcprofile
#
# Summarise GC profiling information from log data.

import math
import re

# Detect whether we're currently running a raptor test, or between
# tests.
StartTestText = 'Testing url'
EndTestText = 'PageCompleteCheck returned true'

def summariseProfile(text, result, categories, filterMostActiveRuntime=True):
    majorFields, majorData, minorFields, minorData, testCount = parseOutput(
        text)

    if filterMostActiveRuntime:
        runtime = findMostActiveRuntimeByFrequency(majorData + minorData)
        majorData = filterByRuntime(majorData, runtime)
        minorData = filterByRuntime(minorData, runtime)

    removeShutdownGCs(majorFields, majorData, minorFields, minorData)

    if 'major' in categories:
        countMajorGCs(result, majorFields, majorData)

    summariseAllData(result, majorFields, majorData, minorFields, minorData, categories)
    if testCount != 0:
        summariseAllDataByInTest(result, majorFields, majorData, minorFields,
                                 minorData, categories, True)

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

        result['First major GC'] = float(line[timestampField])
        result['Heap size / KB at first major GC'] = int(line[sizeField])
        break

def summarisePhaseTimes(result, majorFields, majorData):
    reasonField = majorFields.get('Reason')
    fieldNames = ['bgwrk', 'waitBG', 'prep', 'mark', 'sweep', 'cmpct']
    fields = [majorFields.get(name) for name in fieldNames]
    totals = [0 for name in fieldNames]

    for line in majorData:
        assert not isShutdownReason(line[reasonField])
        for i in range(len(fields)):
            value = line[fields[i]]
            if value:
                totals[i] += float(value)

    for i in range(len(fields)):
        key = 'Total major GC time in phase ' + fieldNames[i]
        result[key] = totals[i]

def countMajorGCs(result, majorFields, majorData):
    statesField = majorFields.get('States')
    reasonField = majorFields.get('Reason')

    count = 0
    for line in majorData:
        assert not isShutdownReason(line[reasonField])
        if "0 ->" in line[statesField]:
            count += 1

    result['Major GC count'] = count

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

    assert len(minorData) != 0 or len(
        majorData) != 0, "No profile data present"

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

    return fields

def summariseAllDataByInTest(result, majorFields, majorData, minorFields,
                             minorData, categories, inTest):
    majorData = filterByInTest(majorFields, majorData, inTest)
    minorData = filterByInTest(minorFields, minorData, inTest)

    suffix = ' in test' if inTest else ' outside test'

    summariseAllData(result, majorFields, majorData, minorFields, minorData,
                     categories, suffix)

def summariseAllData(result,
                     majorFields,
                     majorData,
                     minorFields,
                     minorData,
                     categories,
                     keySuffix=''):
    summariseMajorMinorData(result, majorFields, majorData, minorFields,
                            minorData, categories, keySuffix)

    if 'major' in categories and 'size' in categories:
        result['Max GC heap size / KB' + keySuffix] = \
            findMax(majorFields, majorData, 'SizeKB')
        result['Median GC heap size / KB' + keySuffix] = \
            calcMedian(majorFields, majorData, 'SizeKB')
        result['Max malloc heap size / KB' + keySuffix] = \
            findMax(majorFields, majorData, 'MllcKB')
        result['Median malloc heap size / KB' + keySuffix] = \
            calcMedian(majorFields, majorData, 'MllcKB')

    if 'minor' in categories and 'size' in categories:
        result['Max nursery size / KB' + keySuffix] = \
            findMax(minorFields, minorData, 'NewKB')
        result['Median nursery size / KB' + keySuffix] = \
            calcMedian(minorFields, minorData, 'NewKB')

    if 'major' in categories and 'reason' in categories:
        result['ALLOC_TRIGGER slices' + keySuffix] = \
            len(filterByReason(majorFields, majorData, 'ALLOC_TRIGGER'))
        result['TOO_MUCH_MALLOC slices' + keySuffix] = \
            len(filterByReason(majorFields, majorData, 'TOO_MUCH_MALLOC'))

    if 'minor' in categories and 'reason' in categories:
        result['Full store buffer nursery collections' + keySuffix] = \
            len(filterByFullStoreBufferReason(minorFields, minorData))

    if 'minor' in categories:
        result['Mean full nusery promotion rate' + keySuffix] = \
            meanPromotionRate(minorFields,
                              filterByReason(minorFields, minorData, 'OUT_OF_NURSERY'))


def summariseMajorMinorData(result, majorFields, majorData, minorFields,
                            minorData, categories, keySuffix):
    majorCount, majorTime = summariseData(majorFields, majorData)
    minorCount, minorTime = summariseData(minorFields, minorData)
    minorTime /= 1000
    totalTime = majorTime + minorTime

    if 'major' in categories:
        result['Major GC slices' + keySuffix] = majorCount
        result['Major GC time' + keySuffix] = majorTime
        if majorCount:
            result['Mean major GC slice time'] = majorTime / majorCount

    if 'minor' in categories:
        result['Minor GC count' + keySuffix] = minorCount
        result['Minor GC time' + keySuffix] = minorTime
        if minorCount:
            result['Mean minor GC time'] = minorTime / minorCount

    result['Total GC time' + keySuffix] = majorTime + minorTime

def summariseData(fieldMap, data):
    count = 0
    totalTime = 0
    for fields in data:
        time = float(fields[fieldMap['total']])
        totalTime += time
        # experiment: don't count zero length slices/collections
        if time != 0:
            count += 1
    return count, totalTime

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

    result[
        'Parallel marking donations per collection'] = donationsTotal / count
    result['Geometric mean mark rate'] = math.exp(logMarkRateTotal / count)

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
