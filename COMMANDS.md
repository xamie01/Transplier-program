**Transpiler Commands**

This document lists the most common commands for using the transpiler in this repository.

**Quick Notes**
- Project root: all commands assume your current working directory is the repository root where `bin/transpile` lives.
- Python: use the repository Python environment (create a venv if needed) and install `requirements.txt`.

**Setup**
- Create and activate a virtual environment (optional but recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Transpile a file**
- Basic usage: convert `input` to `target` language and write output:

```bash
python bin/transpile <input> -t <target> -o <output>
# Example: convert a Python (Freqtrade) strategy to Pine Script
python bin/transpile EOVIE.py -t pine -o EOVIE_output.pine
```

- If `-o` is provided, the tool will also export a normalized IR JSON file next to the output:

```
# With the example above you'll get:
EOVIE_output.pine
EOVIE_output.ir.json   # normalized IR exported
```

- If you omit `-o`, the generated code is printed to stdout and the IR JSON is written using the input stem:

```bash
python bin/transpile EOVIE.py -t pine
# prints Pine to stdout and writes EOVIE.ir.json
```

**Flags and options**
- `-t, --target`: target language; supported values (examples): `python`, `pine`.
- `-o, --output`: output file path; if omitted, output prints to stdout.
- `--normalize-only`: produce and print the normalized IR JSON (no code generation).

```bash
python bin/transpile EOVIE.py --normalize-only
```

- `--check-equivalence`: after generation, the CLI attempts to parse the generated code back and checks IR equivalence (best-effort).

```bash
python bin/transpile EOVIE.py -t pine -o out.pine --check-equivalence
```

- `--with-ai`: opt-in translator hook (stub provided). If enabled, the translator will attempt to convert complex condition expressions before generation.

```bash
python bin/transpile EOVIE.py -t pine -o out.pine --with-ai
```

**Inspect exported IR**
- The normalized IR is JSON and includes metadata, `indicators`, `conditions`, `orders`, `position_sizing`, and `mappings` (e.g., `mappings.column_to_indicator`) to help translation.

```bash
cat EOVIE_output.ir.json
```

**Round-trip equivalence test (pytest)**
- Run the repository tests including the round-trip equivalence test:

```bash
pytest -q
# Or run the specific test
pytest tests/test_roundtrip_equivalence.py -q
```

- On failure, the test writes debugging files to `tests/debug_outputs/py_norm.json` and `tests/debug_outputs/pine_norm.json` for easy diffing.

**Development / debugging**
- Transpile and view both outputs and IR in one step:

```bash
python bin/transpile EOVIE.py -t pine -o EOVIE_output.pine --check-equivalence --with-ai
# Then inspect:
less EOVIE_output.pine
less EOVIE_output.ir.json
```

- If you need to feed the normalized IR into another tool or an LLM, use the `.ir.json` file produced by the previous command.

**Stdin / stdout mode**
- Read code from stdin and write to stdout (useful for piping):

```bash
cat EOVIE.py | python bin/transpile - -t pine > out.pine
```

**Translator integration notes (`--with-ai`)**
- The repository includes a translator scaffold at `src/ai/translator.py` that:
  - Replaces `dataframe['col']` occurrences with `ind:<id>` tokens using `mappings.column_to_indicator` in the IR.
  - Produces `expr_translated` entries inside the IR for each condition when invoked.
- The scaffold is a stub — to use an LLM:
  1. Implement a backend inside `src/ai/translator.py` that calls your chosen LLM API.
  2. Use the IR JSON as context in the prompt and ask for target-language equivalents.
  3. Respect rate limits, caching and validation (the current stub does not call external services).

**Best practices**
- Normalize before generation: use `--normalize-only` to inspect the IR before converting.
- When translating complex strategies, review `expr_translated` values manually before relying on them.
- Use `--check-equivalence` to catch obvious mismatches quickly; it is a conservative check and may need enhancements for complex strategies.

**Common troubleshooting**
- If tests fail with IR differences, run the round-trip test and inspect `tests/debug_outputs/*_norm.json`.
- If output contains DataFrame-style references (e.g., `dataframe['close']`), check `mappings` in the IR JSON to confirm column→indicator mapping.

**Example workflow**
1. Inspect normalized IR:

```bash
python bin/transpile EOVIE.py --normalize-only
```

2. Generate Pine with AI assisted translation (optional):

```bash
python bin/transpile EOVIE.py -t pine -o EOVIE_output.pine --with-ai --check-equivalence
```

3. Run tests:

```bash
pytest tests/test_roundtrip_equivalence.py -q
```

4. If failing, inspect debug outputs and IR files:

```bash
ls -l tests/debug_outputs
jq . tests/debug_outputs/py_norm.json
jq . tests/debug_outputs/pine_norm.json
```

**Contact / next steps**
- To enable fully automated LLM-driven translation, extend `src/ai/translator.py` with your LLM client and add safe prompt templates. I can add an example OpenAI integration if you want.

---
Generated by the transpiler team — place this file at the repository root as `COMMANDS.md` for quick reference.
