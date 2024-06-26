# benchcomp

Run and compare JS shell benchmarks across builds.

`benchcomp` takes one or more builds and repeatedly runs a benchmark on them,
displaying the results as they become available available.

For example:

`benchcomp pre-buld/ post-build/ -t splay`

## Builds

Builds are specified by passing the build directory. The shell to execute is
found by checking several pre-defined paths under this directory. This is to
make command lines shorter.

The first build is special as the results from other builds are compared against
it.

## Tests

The benchmark to run is passed using the `-t` option. If not specified, this
runs the octane benchmark suite (the current directory is assumed to be js/src
for this).

This option accepts a path to a JS source file or the name of one of the
octane subtests.

## Output

Running the program will run the benchmark repeatedly and summarise the
results. For example it might produce output like this:

```
$ benchcomp pre-build post-build -t splay
                        Min       Mean      Max       CofV    Runs  Change    %       P-value
=============================================================================================
Splay:
             pre-build     33500  33984.85     34438    0.7%    20                                  |-------------===O=====-----------|
            post-build     33346   33952.4     34373    0.7%    20    -32.45   -0.1%     0.81  |-----------------===O====----------|
SplayLatency:
             pre-build     49325  49916.95     50535    0.5%    20                             |--------------====O====---------------|
            post-build     49692  49983.95     50294    0.4%    20        67    0.1%     0.31             |-------==O===------|
```

The columns have the following meaning:

 -  Min: Minimum result value seen
 -  Mean: Mean result value
 -  Maximum: Minimum result value seen
 -  CofV: Coefficient of variation, the ratio of the standard deviation to the mean. An idication of how noisy the results are.
 -  Runs: The number of runs performed so far
 -  Change: Absolule difference between the mean result for this build and the mean result of the first build.
 -  %: Percentage difference between the mean result for this build and the mean result of the first build.
 -  P-Value: Result of a statistical significance test comparing the results for this build against those of the first build.

# Installation requirements

$ pip3 install ansi==0.3.6
