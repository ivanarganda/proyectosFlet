# ivbox

[![PyPI version](https://img.shields.io/pypi/v/ivbox.svg)](https://pypi.org/project/ivbox/)
[![Python](https://img.shields.io/pypi/pyversions/ivbox.svg)](https://pypi.org/project/ivbox/)
[![License](https://img.shields.io/pypi/l/ivbox.svg)](LICENSE)

ivbox is a Python utility framework focused on improving developer productivity through **better project structure** and **reusable utility functions**, built from real-world usage and repetition.

It is designed to grow organically, introducing abstractions **only when patterns prove useful**.

> Current version: **0.2.0**

---

## Why ivbox?

When you build real projects, you quickly notice the same pain points repeating:

- You rewrite the same helpers again and again
- UI code grows fast and becomes hard to maintain
- Small architectural decisions become expensive later
- You want *structure* without over-engineering

ivbox exists to reduce that friction with a simple rule:

> **Abstractions are created only when something is repeated.**

---

## Features

- Improved internal project structure (0.2.0 refactor)
- Reusable **general-purpose utilities**
- UI helper utilities for **Flet-based applications**
- Modular design: add what you need, keep it clean
- Built from real usage, not theoretical patterns

---

## Project Status

ivbox is under **active development**.

- The API may evolve until version `1.0.0`
- Changes are driven by real usage, not assumptions
- Stability increases progressively with each release

---

## Installation

```bash
pip install ivbox

```

## Quick Start
### General utilities

```python
from ivbox.utils import general

# Example usage (adapt to your real functions)
# general.slugify("Hello World") -> "hello-world"
# general.now_str() -> "2025-12-29 20:15:00"
```
### Flet utilities

```python
from ivbox.utils import flet as ivf
import flet as ft

def main(page: ft.Page):
    # Example usage (adapt to your real helpers)
    # page.add(ivf.section_title("Dashboard"))
    pass

ft.app(target=main)

```

## Utilities
### General-purpose utilities

These helpers are framework-agnostic and intended to reduce repetitive code across projects:

- strings and formatting helpers

- date/time helpers

- validation helpers

- file/path helpers

- misc productivity utilities

### Flet UI utilities

Helpers focused on reducing repetition in Flet apps:

- reusable layout patterns

- UI composition helpers

- common components wrappers (only when repeated)

- navigation and page composition helpers (if applicable)

ivbox does not replace Flet — it helps you work with it more efficiently.

### Versioning

ivbox follows semantic versioning with the usual meaning:

- 0.x → active development, API may change

- 1.0.0 → stable and committed API

### Contributing

Contributions are welcome if they:

- solve a real, repeated problem

- keep the project simple and understandable

- respect the philosophy of “repeat first, abstract later”

Suggested flow:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**1.** Open an issue describing the repeated pain point

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**2.** Propose a minimal helper/abstraction

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**3.** Add a small example + tests if applicable

## Author

### Ivan Gonzalez Valles
**GitHub**: https://github.com/ivanarganda

## Inspiration

ivbox is inspired by developer pain points and by frameworks that grew through real usage, like Laravel.
Build what hurts. Keep what repeats