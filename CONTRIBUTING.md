# Contributing to Doraemon

感谢你考虑为 doraemon 贡献代码！本文档描述了开发流程和代码质量要求。

## 🛠 开发环境

```bash
git clone https://github.com/Oligarchy-with-DeamoV/doraemon.git
cd doraemon
poetry install
poetry shell
```

## ✅ 提交前的检查清单

本仓库使用 **pre-commit** 来自动运行所有的代码质量检查。一次性安装钩子：

```bash
poetry run pre-commit install              # commit 时触发 ruff/mypy/bandit
poetry run pre-commit install --hook-type pre-push   # push 时跑 pytest
```

之后每次 `git commit` 都会自动运行 ruff、ruff-format、mypy、bandit；
`git push` 会额外运行测试套件。如果想在提交之前手动跑一遍：

```bash
# 跑全部钩子（与 CI 一致）
poetry run pre-commit run --all-files

# 或单独跑某个工具
poetry run ruff check src tests
poetry run ruff format src tests
poetry run mypy src
poetry run pytest --cov=src --cov-report=term
poetry run bandit -r src/
```

CI (`.github/workflows/ci.yml`) 通过 `pre-commit run --all-files` 调用同一组
钩子，再额外运行 `pytest --cov`，因此 **本地通过 = CI 通过**。

## 📐 代码风格

- 行长度上限 88 字符（由 `ruff format` 强制执行）。
- 公共 API 使用类型注解；优先 `dict[str, X]` / `X | None`（PEP 585/604），
  在 Python 3.9 文件中需要 `from __future__ import annotations`。
- 关键性更改请同步更新 `CHANGELOG.md` 的 `[Unreleased]` 部分。
- 优先使用 `slogger`（结构化日志）而不是 `print` 或标准 `logging`。

## 🧪 写测试

- 测试位于 `tests/`，目录结构镜像 `src/`。
- 使用 `responses` (sync) / `aioresponses` (async) 来 mock HTTP。
- `tests/doraemon/services/conftest.py` 中的 `_reset_service_state` fixture
  自动清理 `ServiceRegistry`、`ConnectionManager` 等单例的状态，避免
  测试用例之间相互污染。
- 标记需要外部中间件的测试： `@pytest.mark.need_middlewares`。

## 🔐 安全

- **永远不要**提交真实的密码、API token、或内部 IP。如不慎泄露，
  请通过 git 历史以外的方式（如 BFG Repo-Cleaner 或 git-filter-repo）
  清理，并按 `SECURITY.md` 的指引轮换凭据。
- 报告安全漏洞请直接联系维护者，而不是公开 issue。

## 📝 提交信息

请遵循 Conventional Commits 风格：

- `feat: ...` 新功能
- `fix: ...` Bug 修复
- `docs: ...` 仅文档变更
- `test: ...` 仅测试变更
- `refactor: ...` 重构
- `chore: ...` 构建系统、依赖等

## 🚢 发布流程

1. 在 PR 中更新 `CHANGELOG.md` 的 `[Unreleased]` 部分。
2. 合并后由维护者执行 `poetry version <new>` 并打 git tag。
3. CI 自动构建并发布到 PyPI（如已配置 trusted publisher）。
