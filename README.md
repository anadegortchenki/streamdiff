# streamdiff

A CLI tool for diffing large streaming datasets without loading them fully into memory.

---

## Installation

```bash
pip install streamdiff
```

Or install from source:

```bash
git clone https://github.com/yourusername/streamdiff.git
cd streamdiff && pip install -e .
```

---

## Usage

Compare two large CSV or newline-delimited files line by line:

```bash
streamdiff file_a.csv file_b.csv
```

Output only lines added or removed:

```bash
streamdiff --only-changes file_a.csv file_b.csv
```

Pipe from stdin:

```bash
cat file_a.csv | streamdiff - file_b.csv
```

### Options

| Flag | Description |
|------|-------------|
| `--only-changes` | Show only added/removed lines |
| `--key COLUMN` | Diff by a specific column key |
| `--format [text\|json]` | Output format (default: text) |
| `--ignore-order` | Compare sets, ignoring line order |

---

## Why streamdiff?

Standard `diff` loads both files into memory. `streamdiff` processes data in a streaming fashion, making it suitable for files that are gigabytes in size or data piped from external sources.

---

## License

MIT © 2024 [Your Name](https://github.com/yourusername)