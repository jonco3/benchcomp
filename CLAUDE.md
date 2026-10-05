# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`benchcomp` is a Python 3 CLI that repeatedly runs a benchmark against multiple Mozilla SpiderMonkey builds (JS shell or browser via Raptor) and interactively displays statistical comparisons against the first build. See README.md for the output column meanings.

There is no test suite or build step. Dependency: `pip3 install ansi==0.3.6` (Android support also needs `adb` and `adbsync`; `--perf` needs `perf`/`simpleperf`).

- Run: `./benchcomp <build-dir> [<build-dir>...] -t <test>` (build args can be appended inside a quoted spec, e.g. `"build/ --foo"`)
- Run a single benchmark once with the same options: `./benchrun <build> -t <test>`
- Format: `scripts/format.sh` (runs `yapf -i benchcomp lib/*.py`; style in `.style.yapf`). Note `benchrun` is not covered by the script.

## Architecture

Two extensionless executable scripts (`benchcomp`, `benchrun`) add `lib/` to `sys.path` and import flat modules from it.

`benchcomp` flow: `parseArgs` → `buildsToTest` (builds `Build` objects, applies `--args`, `--gc-param`, and expands `--repeat-with-gc-params` / `--repeat-with-prefs` by deep-copying each build per value) → `testsToRun` → `runTests`.

`runTests` is an event loop over a `queue.Queue` fed by two threads:
- test runner thread (`testRunnerThread`) iterates `generateTestRuns` (shuffled build/test order), calls `runBenchmark`, and posts `TestResults`; posts `None` when done or on exception.
- keyboard thread (only on a tty) posts `KeyPress` events; `handleKeyPress` mutates `args` live (q quit, c/C compare key, s summary mode, l layout, r reverse, f significant-only).

After each event, `displayResults` re-renders to a `display.Terminal` (clearable, truncated to terminal size) and/or `display.File` (`--output`). Results are a nested dict keyed by result key then by build.

`lib/` modules:
- `test.py`: `Test` hierarchy (`ShellTest` → `OctaneTest`, `SunspiderTest`, `SixSpeedTest`, `LocalTest`; `BrowserTest` → `RaptorTest`). `getKnownTests()` is the registry; `-t` matches a known name, otherwise is treated as a path to a local JS file (optionally with args). First known test (octane) is the default. Known shell tests locate files via `utils.path_to_source_root()` (cwd is assumed to be within a mozilla-central checkout, e.g. `js/src`).
- `build.py`: `Build` resolves a build dir to a shell binary or browser config by probing predefined paths.
- `stats.py`, `format.py`: significance tests (p-value) and result formatting/histogram/range rendering.
- `gcprofile.py`: parses GC profile logs (`--gc-profile`) into per-category results.
- `perf.py`, `android.py`: wrap commands for `perf`/`simpleperf` and for running on Android devices via adb (android currently supports only octane).
- `getch.py`: raw single-keypress terminal input context manager.
