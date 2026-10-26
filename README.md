# Deterministic policy-routing prototype

This small standard-library-only prototype tests one design boundary suggested by a local model's failures on synthetic customer-support cases: choose a versioned policy with explicit subject and channel gates plus date interval logic before asking a language model to draft customer-facing wording.

It accompanies the article [My Local Model Chose a Return Policy Too Early](https://williamlab.dev/articles/my-local-model-chose-a-return-policy-too-early). `route_cases.py` reprints the router table from that article.

## Run

From the repository root, Python 3.9 or later, no dependencies:

```
python3 -m unittest -v
python3 route_cases.py
python3 capture_examples.py
```

- `python3 -m unittest -v` runs the ten boundary tests in `test_policy_router.py`.
- `python3 route_cases.py` runs the six synthetic cases in `cases.json` through `resolve_policy` and prints the result next to the expected source that was written before any model run. It exits non-zero if any case does not match.
- `python3 capture_examples.py` writes `trace-examples.json`: seven boundary scenarios with the router's full decision, plus SHA-256 hashes of the data, router and generator files.


## Files

- `policy_router.py`: `resolve_policy`, the router.
- `test_policy_router.py`: boundary tests.
- `cases.json`: the two synthetic policy versions (RET-V1, RET-V2) and the six synthetic case inputs with their expected source. `subject_covered` is a hand label; see below.
- `route_cases.py`, `capture_examples.py`: scripts described above.

## Scope and limits

The selector assumes `subject_covered` has already been established by an upstream trusted workflow or reviewed classification. It does not infer intent from free text, resolve legal meaning, calculate eligibility from a duration clause, write a reply, or execute a refund. Missing dates, unsupported channels/subjects, future dates, and gaps return no selected policy. Intervals are start-inclusive and end-exclusive; overlap fails closed. A date that is not a canonical `YYYY-MM-DD` string raises `ValueError` instead of returning a status.

The case inputs have a free-text question and no subject field. In `cases.json`, `subject_covered` is `false` for CS-02 (a warranty question) because it was set by hand. The router does not decide that.

The router was written after the six model failures had been seen, so the six cases matching is a consistency check, not held-out evidence.

These tests validate only deterministic routing behavior against the synthetic RET-V1/V2 examples. They do not prove retrieval quality, model drafting quality, enterprise fitness, reduced human work, or production security.

## License

MIT. See `LICENSE`.
