# 📚 Documentation Index

Welcome to the Trading Strategy Transpiler! Here's where to find what you need.

## 🚀 Getting Started (Pick One)

- **5 minutes?** → Read [`QUICKSTART.md`](QUICKSTART.md)
- **Want details?** → Read [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
- **Just want to use it?** → Run `python bin/transpile examples/python/sma_crossover.py -t pine`

---

## 📖 Documentation Files

### Quick References
| Document | Time | Purpose |
|----------|------|---------|
| [`QUICKSTART.md`](QUICKSTART.md) | 5 min | 30-second overview and common commands |
| [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md) | 10 min | Architecture overview and feature summary |
| [`FILE_MANIFEST.md`](FILE_MANIFEST.md) | 5 min | Complete list of all files created |

### Detailed Guides
| Document | Time | Purpose |
|----------|------|---------|
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | 30 min | Comprehensive developer guide (500+ lines) |
| [`COMPLETION_CHECKLIST.md`](COMPLETION_CHECKLIST.md) | 10 min | Implementation status and verification |
| [`STATUS_REPORT.md`](STATUS_REPORT.md) | 10 min | Executive summary and metrics |

---

## 🎯 What Do You Want To Do?

### Convert Python to Pine Script
```bash
python bin/transpile my_strategy.py -t pine -o output.pine
```
📖 See: [`QUICKSTART.md`](QUICKSTART.md) → "Convert Python to Pine Script"

### Understand How It Works
📖 See: [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md) → "Architecture"

### Add a New Language
📖 See: [`IMPLEMENTATION.md`](IMPLEMENTATION.md) → "For Developers: Adding a New Generator"

### Run Tests
```bash
pytest tests/ -v
```
📖 See: [`IMPLEMENTATION.md`](IMPLEMENTATION.md) → "Running Tests"

### View the IR (Intermediate Representation)
```bash
python bin/transpile my_strategy.py --normalize-only
```
📖 See: [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md) → "Minimal Data Contract"

### Check Equivalence After Conversion
```bash
python bin/transpile my_strategy.py -t pine --check-equivalence
```
📖 See: [`QUICKSTART.md`](QUICKSTART.md) → "Verify Round-Trip Conversion"

---

## 🔧 Technical Resources

### For Users
- [`QUICKSTART.md`](QUICKSTART.md) — Commands and examples
- [`examples/`](examples/) — Working strategies in Python and Pine
- [`tests/`](tests/) — Test examples showing expected behavior

### For Developers
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md) — Complete API reference
- [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md) — Architecture deep-dive
- [`FILE_MANIFEST.md`](FILE_MANIFEST.md) — File-by-file documentation
- Docstrings in source code — Every function documented

### For Project Managers
- [`STATUS_REPORT.md`](STATUS_REPORT.md) — Implementation metrics
- [`COMPLETION_CHECKLIST.md`](COMPLETION_CHECKLIST.md) — Feature checklist

---

## 📂 Directory Guide

```
Project Root/
├── QUICKSTART.md              👈 Start here (5 min)
├── IMPLEMENTATION.md          👈 Full guide (30 min)
├── BUILD_SUMMARY.md           👈 Architecture (10 min)
├── COMPLETION_CHECKLIST.md    👈 Status (10 min)
├── STATUS_REPORT.md           👈 Metrics (10 min)
├── FILE_MANIFEST.md           👈 All files (5 min)
│
├── bin/transpile              👈 CLI tool
├── src/                       👈 Source code
│   ├── parsers/               👈 Input parsers
│   ├── generators/            👈 Output generators
│   ├── ir/                    👈 Intermediate representation
│   ├── indicators/            👈 Indicator registry
│   ├── position/              👈 Position sizing
│   └── utils/                 👈 Helper utilities
├── tests/                     👈 Test suite
└── examples/                  👈 Example strategies
```

---

## 🎓 Learning Path

### Level 1: User (Just Convert)
1. Read [`QUICKSTART.md`](QUICKSTART.md) (5 min)
2. Run an example (1 min): `python bin/transpile examples/python/sma_crossover.py -t pine`
3. Convert your own strategy (5 min)

**Total:** ~10 minutes to first conversion

### Level 2: Hobbyist (Understand How It Works)
1. Read [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md) (10 min)
2. Look at [`examples/python/sma_crossover_ir.json`](examples/python/sma_crossover_ir.json) (5 min)
3. Try `--normalize-only` mode to see IR (5 min)
4. Read about IR in [`IMPLEMENTATION.md`](IMPLEMENTATION.md) (10 min)

**Total:** ~30 minutes to understand architecture

### Level 3: Developer (Extend System)
1. Read [`IMPLEMENTATION.md`](IMPLEMENTATION.md) cover-to-cover (30 min)
2. Review source code in `src/` directory (30 min)
3. Run and modify tests in `tests/` (20 min)
4. Create new generator or parser (60+ min)

**Total:** ~2 hours to extend the system

### Level 4: Architect (Full System)
1. Read all documentation (1 hour)
2. Understand three-layer architecture (30 min)
3. Review design patterns in code (30 min)
4. Plan enhancements/Phase 2 work (1+ hour)

**Total:** ~3 hours to master system

---

## ❓ Common Questions

**Q: How do I convert Python to Pine?**  
A: `python bin/transpile strategy.py -t pine -o output.pine`  
📖 More in [`QUICKSTART.md`](QUICKSTART.md)

**Q: How do I understand what the transpiler does?**  
A: Read the architecture section in [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md)  
📖 Full details in [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

**Q: How do I add support for a new language?**  
A: Follow the template in [`IMPLEMENTATION.md`](IMPLEMENTATION.md) → "For Developers"

**Q: How do I run tests?**  
A: `pytest tests/ -v`  
📖 Details in [`IMPLEMENTATION.md`](IMPLEMENTATION.md) → "Running Tests"

**Q: What's the Intermediate Representation?**  
A: See data structure reference in [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md)  
📖 Full spec in [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

**Q: Can I verify my conversion is correct?**  
A: `python bin/transpile strategy.py -t pine --check-equivalence`  
📖 More in [`QUICKSTART.md`](QUICKSTART.md)

---

## 📊 Project Statistics

- **Total Files:** 19 (15 new, 4 updated)
- **Total Lines:** 1,800+ (production) + 300+ (tests) + 1,600+ (docs)
- **Test Coverage:** 300+ lines of tests
- **Documentation:** 1,600+ lines
- **Status:** ✅ 100% Complete

See [`STATUS_REPORT.md`](STATUS_REPORT.md) for full metrics.

---

## 🚀 Next Steps

### Immediate (Today)
1. ✅ Install: `pip install -r requirements.txt`
2. ✅ Try: `python bin/transpile examples/python/sma_crossover.py -t pine`
3. ✅ Read: [`QUICKSTART.md`](QUICKSTART.md)

### Short Term (This Week)
1. Convert your own strategies
2. Run tests: `pytest tests/ -v`
3. Read [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md) for deeper understanding

### Medium Term (This Month)
1. Read full [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
2. Review source code
3. Plan Phase 2 enhancements

### Long Term (Future)
1. Add new languages (JavaScript, MQL4/5, etc.)
2. LLM integration for edge cases
3. Web UI for visual strategy building
4. Backtesting integration

---

## 💡 Pro Tips

1. **Use `--normalize-only`** to debug what the parser extracts: `python bin/transpile strategy.py --normalize-only`

2. **Check equivalence** to validate round-trip: `python bin/transpile strategy.py -t pine --check-equivalence`

3. **Read docstrings** in source files for API details

4. **Look at tests** to understand expected behavior

5. **Check examples/` for working strategies to learn from

---

## 📞 Support

- **For quick answers:** Check [`QUICKSTART.md`](QUICKSTART.md)
- **For detailed info:** See [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
- **For architecture:** Read [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md)
- **For code docs:** See docstrings in `src/` files
- **For examples:** Check `examples/` directory
- **For test examples:** See `tests/` directory

---

## 📝 Document Map

```
Overview Layer
├── QUICKSTART.md ..................... 5-min user guide
├── BUILD_SUMMARY.md .................. Architecture overview
└── FILE_MANIFEST.md .................. All files created

Detailed Layer
├── IMPLEMENTATION.md ................. Complete 500+ line guide
├── COMPLETION_CHECKLIST.md ........... Feature verification
└── STATUS_REPORT.md .................. Implementation metrics

Code Layer
├── src/ ............................ Source code with docstrings
├── tests/ .......................... Test suite with examples
└── examples/ ....................... Working strategies
```

---

**Happy converting! 🚀**

Start with [`QUICKSTART.md`](QUICKSTART.md) or dive into [`IMPLEMENTATION.md`](IMPLEMENTATION.md) for details.
