"""Benchmark / evaluation harness for aesthetics-compiler.

These tools measure how well the compiler's predicted aesthetic dimensions
agree with *human* aesthetic judgements from public datasets (primarily AADB).

Nothing here is imported by the compiler itself — it is a standalone eval
layer.  Run it with:

    python -m benchmarks.run_aadb            # uses bundled sample data
    python -m benchmarks.run_aadb --data path/to/aadb_labels.csv
"""
