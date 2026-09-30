---
status: draft
priority: 0
description: |
  `requires-python` says `==3.14.*` while ruff lints the code at `py313` and
  nothing in the source needs 3.14. The pin is inherited from the project
  template, and it shuts out any consumer pinned to an older interpreter for
  reasons of its own. Work out what the real floor is, lower it to that, and
  release it.
comment: |
  Raised 2026-09-30 by a project that could not add this library because its own
  interpreter is pinned below 3.14 by a binary dependency. It went ahead without
  the library, so nothing is waiting on this folder; it is here because the next
  consumer will hit the same wall.
---

# What version of Python does this actually need

## The situation

`pyproject.toml` declares:

```toml
requires-python = "==3.14.*"
```

`ruff.toml` declares:

```toml
target-version = "py313"
```

Those disagree. The first says the package refuses to install on anything but 3.14. The second says
the linter has been holding the code to what 3.13 can run, and passing.

The declaration is the one that gets enforced. A project pinned to 3.13 cannot add this library at
all: `uv` compares the two `requires-python` ranges, finds them disjoint, and refuses to resolve
before anything is downloaded or imported. There is no partial success and no warning to work
around. The library is simply unavailable to that project, on the strength of a line that appears to
be inherited rather than chosen.

## Where the pin came from

It is not specific to this repository. Every package in the ecosystem carries the same pair:

| repo | `requires-python` | ruff `target-version` |
| --- | --- | --- |
| python-project-template | `==3.14.*` | py313 |
| fastapi-tools | `==3.14.*` | py313 |
| llm-core | `==3.14.*` | py313 |
| media-downloader | `==3.14.*` | py313 |
| lang-tools | `==3.14.*` | py313 |

The template sets it, every project generated from the template keeps it, and none of them has had a
reason to look at it. That makes this a template question with a library-shaped symptom, which is
why the last phase below is about the template rather than about this package.

`==3.14.*` is also stricter than it looks. It is not a floor, it is a window: it excludes 3.15 as
firmly as it excludes 3.13, so the same wall arrives again from the other side at the next release.

## What the code appears to need

A read of the source, which is evidence and not a test:

- No 3.14-only construct anywhere in `src/`. The newest syntax in the package is a `match` statement,
  which is 3.10.
- Every module opens with `from __future__ import annotations`, so the annotation spellings are
  strings at runtime and cost nothing on an older interpreter.
- The one thing worth checking rather than eyeballing is `AsyncGenerator[None]` in the factory's
  lifespan, written with one parameter where the ABC has two. That form relies on the type parameter
  defaults added in 3.13, so it is fine at 3.13 and not below.
- The runtime dependencies are fastapi, uvicorn, starlette, pydantic, httpx, itsdangerous,
  email-validator, python-dotenv and loguru. All of them support 3.13. None of them is the reason for
  the pin.

So the expected answer is that the real floor is 3.13, and the honest expression of it is
`>=3.13,<3.15` or simply `>=3.13`. That is a hypothesis to test, not a change to make on the strength
of a grep.

## How to test it

Four rungs, cheapest first. The first three inspect this package's own source; only the fourth
exercises the dependency tree, which is where a surprise would actually come from.

1. **Syntax.** `python3.13 -m compileall -q src/`. Catches grammar 3.13 cannot parse and nothing
   else. Seconds.
2. **Inferred floor.** `uvx vermin src/`, which reads the source and reports the minimum version it
   can deduce. Fast, occasionally wrong in both directions, good for spotting a single stray call.
3. **Types and stdlib.** pyright with `pythonVersion = "3.13"`, either in `[tool.pyright]` or as
   `--pythonversion 3.13`. This is the rung that catches a stdlib member or typing feature that
   exists in 3.14 and not in 3.13, which rungs 1 and 2 will both miss.
4. **The one that settles it.** Change the pin on a branch, then `uv sync --python 3.13` and run this
   package's own test suite, `tests/webapp/test_factory.py` included, since it builds an app. This is
   the only rung that proves the resolver can satisfy the dependency tree on 3.13 rather than proving
   that the source parses.

**None of this needs a push or a tag.** The git-tag release exists so that consumers can name a
version; testing happens on a local branch with a local sync. The tag is the last step, after rung 4
passes, not a prerequisite for finding out.

Running the suite on both interpreters and not only the new floor is the point of phase 2 below: a
floor that is lowered and only ever tested at the bottom is half-tested.

## Proposed phases

Written out when this is picked up. The shape is expected to be:

1. **Find the floor.** Rungs 1 to 4 on a branch, at 3.13 and at 3.12, and record where it actually
   breaks. The output is a number and the evidence for it, not a released package.
2. **Lower and verify.** Set `requires-python` to what phase 1 found, and get the test suite passing
   on the floor and on the current interpreter, so the range that is declared is the range that is
   covered. CI, if it grows one, runs both.
3. **Release.** `CHANGELOG.md`, a version bump, an annotated tag and a push, per the release
   checklist in the box documentation. Widening a `requires-python` is backwards compatible for
   every existing consumer, so this is a minor version.
4. **Upstream.** The same pin is in the template and in the other packages. Fixing it here fixes one
   symptom; fixing the template stops it being reissued to everything generated from it afterwards.
   Probably its own folder over there rather than a phase here.

## Open questions

- Q1: What the floor should be once it is known. a. `>=3.13,<3.15`, a tested window with an upper
  bound. b. `>=3.13`, a floor with no ceiling, so a new interpreter never needs a release here to be
  usable. c. lower still, 3.12 or 3.11, if the tests pass there.
  - Recommended: b. An upper bound is a promise to cut a release on someone else's schedule, and
    `==3.14.*` is precisely how that promise was broken this time. A floor with a tested lower end and
    no ceiling fails loudly at the point of use rather than silently at resolution.
  - NEW_ANS:
- Q2: How far down to test. Trying 3.12 and 3.11 costs one command each on top of the ladder, and a
  wider range is only worth declaring if something is actually going to use it.
  - Recommended: measure down to 3.12 for the information, declare 3.13 unless there is a consumer
    asking for lower. A declared range that nothing exercises is a claim, not a fact.
  - NEW_ANS:
- Q3: Whether the test suite runs on more than one interpreter from here on, and where. A matrix is
  the only thing that keeps a widened range true six months from now, and this repository has no CI
  today.
  - Recommended: at minimum a documented two-command local check in phase 2. A CI matrix is worth its
    own decision, since it is the first CI this repository would have.
  - NEW_ANS:
- Q4: Whether the template is fixed as part of this or separately. The template is the source of the
  pin, and four other packages carry the same line.
  - Recommended: separately, as its own folder there, once the floor here is known and the reasoning
    is written down. This folder does not wait for it.
  - NEW_ANS:
