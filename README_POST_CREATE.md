# Template instructions

## Set up a new Python project

Clone the `fastapi-tools` repo.

```bash
git clone git@github.com:Pitrified/fastapi-tools.git
```

Enter the repo folder:

```bash
cd fastapi-tools
```

Install the dependencies (including the ones needed for the renaming script):

```bash
uv sync --group dev
```

Run the [rename_project.py](meta/rename_project.py) script to rename the project.
This will create a new folder next to the current one (sibling directory).

```bash
# Syntax: uv run rename-project <fastapi_tools> [--repo-name <repo-name>]
uv run rename-project my_new_project
```

By this point, the project is already set up with the new name.
This README file will be copied in `README_POST_CREATE.md`,
with the name of the project updated.

Go to the new folder:

```bash
cd ../fastapi-tools
```

Install the project:

```bash
uv sync --all-extras --all-groups
```


<!-- Install the optional dependencies with the following command: -->
<!-- {{optional_dependencies}} -->
<!-- TODO automagically generate the optional dependencies list -->

Install the required dependencies:
(already done by the `uv sync` command, as the existing dependencies of the template project are kept in the `pyproject.toml` file)
To bump the versions of dependencies, use:

```bash
uv add loguru
uv add --group dev pytest
```

You can update dependencies with:

```bash
uv add loguru --upgrade-package loguru
```

Initialize the git repository, set the identity, and make the first commit:

```bash
git init
git add .
git add **/.gitkeep -f
# gitid ...
git commit -m "Initial commit"
```

## Set up github pages

Visit the
[github pages settings](https://github.com/Pitrified/fastapi-tools/settings/pages)
and enable github pages, setting deploy from action.

## Install additional dependencies

Install the dependencies you want with the following commands


Log and formatting dependencies

```bash
uv add loguru rich tqdm
```

LLM dependencies

```bash
uv add transformers accelerate
uv add torch
uv add \
    chromadb \
    langchain \
    langchain-chroma \
    langchain-community \
    langchain-huggingface \
    langchain-ollama ollama \
    langchain-openai \
    langgraph \
    sentence_transformers
```

Data dependencies

```bash
uv add \
    pandas numpy matplotlib seaborn scikit-learn \
    plotly altair bokeh
    kaleido==0.2.1
```

Web dependencies

```bash
uv add fastapi uvicorn
uv add streamlit
```

Notebook dependencies

```bash
uv add ipykernel ipywidgets nbformat
```

Scraping dependencies

```bash
uv add \
    beautifulsoup4 lxml \
    httpx \
    requests \
    scrapy \
    aiohttp
```

Test dependencies

```bash
uv add --group dev pytest
uv add --group dev pytest-cov
```
