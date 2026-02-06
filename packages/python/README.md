# Python Packages

This directory contains Python packages for the III Engine.

## Packages

### iii

The core SDK for communicating with the III Engine via WebSocket. The package is installed as `iii-sdk`.

```bash
cd iii
pip install -e .
```

## Examples

### iii-example

Basic example demonstrating the III SDK.

```bash
cd iii-example
pip install -e ../iii
python src/main.py
```

## Development

### Install package in development mode

```bash
pip install -e iii
```

### Type checking

```bash
cd iii && mypy src
```

### Linting

```bash
cd iii && ruff check src
```
