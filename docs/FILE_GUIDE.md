# File-by-file guide

This document is a compact index of what every tracked source/test/configuration file is responsible for and where a developer should look when extending the project.

| File | Responsibility | Change this when... |
|---|---|---|
| `.github/workflows/ci.yml` | CI pipeline | Python versions, browser install, or CI checks change |
| `.ruff.toml` | Ruff settings | lint/format policy changes |
| `pyproject.toml` | package/build/tooling metadata | dependencies, package metadata, CLI entry point, mypy/ruff settings change |
| `requirements.txt` | runtime dependencies | a runtime library is added/removed |
| `requirements-dev.txt` | development dependencies | test/lint/type tooling changes |
| `src/offline_article/__init__.py` | version/package identity | release version changes |
| `src/offline_article/__main__.py` | module entry point | module execution behavior changes |
| `src/offline_article/app.py` | end-to-end capture orchestration | capture sequencing, failure policy, resource flow changes |
| `src/offline_article/cli.py` | user-facing commands/options | CLI syntax or defaults change |
| `src/offline_article/config.py` | configuration schema | new capture settings are added |
| `src/offline_article/exceptions.py` | domain errors | new error classes are needed |
| `src/offline_article/logging.py` | logging setup | log formatting/verbosity changes |
| `src/offline_article/types.py` | shared types | common type aliases/contracts change |
| `src/offline_article/browser/cookies.py` | cookie import/export | cookie formats or serialization changes |
| `src/offline_article/browser/manager.py` | browser lifecycle | browser launch/context behavior changes |
| `src/offline_article/render/loader.py` | navigation/render stabilization | wait/scroll/login/render behavior changes |
| `src/offline_article/discover/html.py` | HTML resource graph extraction | new HTML resource attributes/tags are supported |
| `src/offline_article/discover/css.py` | CSS resource graph extraction | new CSS URL/import patterns are supported |
| `src/offline_article/discover/resources.py` | discovery orchestration | recursion/graph traversal changes |
| `src/offline_article/fetch/client.py` | network asset retrieval | retries, pooling, concurrency, HTTP behavior changes |
| `src/offline_article/fetch/cache.py` | persistent cache | cache format or storage behavior changes |
| `src/offline_article/rewrite/html.py` | HTML offline transformation | HTML references need new rewrite/removal behavior |
| `src/offline_article/rewrite/css.py` | CSS offline transformation | CSS URL rewriting changes |
| `src/offline_article/archive/base.py` | archive strategy contract | a format writer needs a new common capability |
| `src/offline_article/archive/factory.py` | format selection | a new output format is added |
| `src/offline_article/archive/html_writer.py` | single-file HTML | HTML archive generation changes |
| `src/offline_article/archive/dir_writer.py` | directory archive | directory/asset layout changes |
| `src/offline_article/archive/zip_writer.py` | ZIP packaging | ZIP packaging changes |
| `src/offline_article/archive/mhtml_writer.py` | MHTML packaging | MHTML behavior changes |
| `tests/conftest.py` | common test fixtures | shared test resources/server behavior changes |
| `tests/unit/test_app.py` | app integration tests | capture pipeline changes |
| `tests/unit/test_archive.py` | archive tests | writer behavior changes |
| `tests/unit/test_auth.py` | auth/cookie/browser tests | browser sessions/cookies change |
| `tests/unit/test_cli.py` | CLI tests | command flags or output change |
| `tests/unit/test_config.py` | config tests | defaults/validation change |
| `tests/unit/test_discover.py` | discovery tests | resource graph extraction changes |
| `tests/unit/test_fetch.py` | fetch/cache/concurrency tests | HTTP fetching or concurrency changes |
| `tests/unit/test_hard_sites.py` | difficult-page tests | Shadow DOM/iframe behavior changes |
| `tests/unit/test_login_workflow.py` | login tests | login detection/flow changes |
| `tests/unit/test_mhtml.py` | MHTML tests | MIME archive changes |
| `tests/unit/test_rewrite.py` | HTML/CSS rewrite tests | offline rewriting changes |
| `README.md` | user documentation | command usage/features/release behavior changes |
| `docs/ENGINEERING.md` | architecture/development documentation | architecture or developer workflow changes |
| `docs/FILE_GUIDE.md` | file map | repository structure changes |
