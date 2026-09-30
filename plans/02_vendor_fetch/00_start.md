---
status: draft
priority: 0
description: |
  `scripts/webapp/cdn_load.sh` reports success when it has written a 404 page
  into an asset file, pins two of its four downloads and lets the other two
  drift, and duplicates version numbers the package already ships inside its own
  wheel. It also points at a guide that does not exist.
comment: |
  Found 2026-09-30 while reading the script as prior art for vendoring the same
  assets elsewhere. Independent of 01_python_floor: different fault, different
  file, neither waits on the other.
---

# The vendor fetch reports success when it fails

## The script

`scripts/webapp/cdn_load.sh`, 21 lines, fetches four assets into `static/`:

```bash
curl -sL "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js" -o static/swagger/swagger-ui-bundle.js
curl -sL "https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"    -o static/swagger/redoc.standalone.js
curl -sL "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.4/css/bulma.min.css" -o static/css/bulma.min.css
curl -sL "https://unpkg.com/htmx.org@1.9.2"                                     -o static/js/htmx.min.js
echo "Swagger, ReDoc, Bulma, and HTMX assets downloaded successfully."
```

## What is wrong with it

**It cannot fail.** `curl -sL` without `-f` treats an HTTP error as a successful transfer of an
error page. A 404, a CDN outage, a captive portal or a typo in a URL all end with the error body
written into the asset file, `curl` exiting 0, and the script printing that everything downloaded
successfully. The failure then surfaces much later and somewhere else, as a page with no styling or
a script that does not parse, which is a long way from the cause. `-sSfL` is the fix: `-f` fails on
an error status and `-S` prints why.

**Two of the four downloads drift.** Bulma is pinned at 0.9.4 and htmx at 1.9.2. Swagger UI is
`@5` and ReDoc is `@2`, which are major-version ranges: the bytes that arrive depend on the day. A
vendored asset whose version is decided by when you ran the script is not vendored.

**The htmx URL has no path.** `https://unpkg.com/htmx.org@1.9.2` resolves through the package's
entry point rather than naming a file. It happens to land on `dist/htmx.min.js`. Naming the file is
one path segment and removes the dependency on a packaging field.

**Three CDNs for four files.** jsdelivr, cdnjs and unpkg, with nothing choosing between them. Each
is a separate origin that can fail separately.

**Nothing verifies what arrived.** No checksum, so a correct-looking download of the wrong thing
passes. This matters more than usual for assets that are executed in a browser.

**It re-downloads every time.** There is no check for a file already present, so the script is four
network round trips whether or not there is anything to do. That is what makes it awkward to call
from a setup step that runs often.

**It only works from the repository root.** The paths are relative to the working directory, with no
guard, so running it from anywhere else quietly creates a `static/` tree in the wrong place.

**It points at a guide that does not exist.** The header says "References in docs:
docs/guides/webapp_setup.md". `docs/guides/` holds `pre_commit.md` and `uv.md`. Nothing else in the
repository mentions the script, `/vendor`, or `static/css`.

## The structural question underneath

The package ships its own copies of these assets inside the wheel, at
`src/fastapi_tools/_static/`, and `factory.py` mounts that directory at `/vendor`. Those copies are
htmx 1.9.2 and Bulma 0.9.4 today, which is exactly what the script fetches.

So the same two version numbers are written down twice, in a shell script and in a set of committed
binaries, with nothing keeping them in step. Bump one and the other drifts silently: a consumer
using `/vendor` and a consumer that ran the script would then be on different versions of Bulma, and
nothing would say so.

That raises the question of who the script is still for. A project that depends on this package gets
the assets mounted at `/vendor` and never needs it. A project that borrowed the shape without taking
the dependency does need it, and is the reason it should keep working. Which of those is supported
decides whether this is a script to fix or a script to delete in favour of a documented one-liner.

## Proposed phases

Written out when this is picked up. Expected shape:

1. **Make it fail properly.** `-sSfL`, pin all four, name the htmx file, one CDN, and a working
   directory guard. Small, and it is the whole bug.
2. **Make it skip what is there**, so it can be called from a setup step without four round trips.
3. **Decide who it is for**, per the section above, and either document it or remove it. This is
   where the duplicate version numbers get one home instead of two.

## Open questions

- Q1: What the versions are pinned to. a. exactly what the wheel already ships, so the two copies
  agree today and the drift question is at least visible. b. current upstream for all four, which
  means moving Bulma and htmx as well as the two unpinned ones.
  - Recommended: a. Matching what is already shipped is the change with no behaviour in it; bumping
    versions is a separate decision that deserves its own reason.
  - NEW_ANS:
- Q2: Whether the versions live in one place. They are in the script and in the committed binaries,
  and one of the two is going to move without the other.
  - Recommended: a single variable block at the top of the script, and a check in the test suite that
    the shipped `_static/` files match those versions. A comment asking people to remember is what is
    there now, in effect, and it has already produced a doc reference to a file that was never
    written.
  - NEW_ANS:
- Q3: Integrity. Whether each download is checked against a recorded sha256.
  - Recommended: yes, in the same variable block as the version. These files are executed in a
    browser, the cost is one `sha256sum -c` per asset, and it turns "the CDN returned something" into
    "the CDN returned the thing we vendored".
  - NEW_ANS:
- Q4: Who the script serves, and therefore whether it survives phase 3: projects that depend on this
  package and get `/vendor` for free, or projects that copied the shape and fetch for themselves.
  - Recommended: the second, explicitly, and say so in its header and in a guide that exists. The
    first case is already served by the wheel.
  - NEW_ANS:
- Q5: Whether a `make` target replaces the script outright. The recent makefiles in the ecosystem are
  phony task runners, but file targets would give the skip in Q2 and phase 2 for free, since make
  does not rebuild a file that is already there.
  - Recommended: keep the script as the thing that fetches one asset correctly, and let a caller
    decide how to invoke it. A repository with no Makefile today should not grow one for four curl
    lines.
  - NEW_ANS:
