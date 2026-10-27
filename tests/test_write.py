"""write 工具的测试：check（deny 还是 ask、reason 写了什么）+ run（文件真的被写对了）。

所有测试都把 tmp_path 下的 ws/ 当成工作目录，不会碰到你真实的文件。
"""
import pytest
from tools import path_policy, read, write


@pytest.fixture(autouse=True)
def ws(tmp_path, monkeypatch):
    ws = (tmp_path / "ws").resolve()
    ws.mkdir()
    monkeypatch.setattr(path_policy, "WORKSPACE", ws)
    return ws


def touch(ws, rel, content="x"):
    f = ws / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")
    return f


def decide(path, content="hi\n"):
    return write.check({"path": path, "content": content})


# ---------------------------------------------------------------------------
# check：正常情况一律 ask，reason 写清楚新建还是覆盖
# ---------------------------------------------------------------------------
def test_check_new_file_asks_create(ws):
    decision, reason = decide("hello.txt")
    assert decision == "ask"
    assert "create" in reason


def test_check_existing_file_asks_overwrite(ws):
    touch(ws, "hello.txt")
    decision, reason = decide("hello.txt")
    assert decision == "ask"
    assert "overwrite" in reason


def test_check_new_nested_folder_asks(ws):
    decision, reason = decide("src/utils/new.py")
    assert decision == "ask", reason


def test_check_main_py_in_subfolder_is_not_blocked(ws):
    # 只有根目录的 main.py（harness 自己）被挡，src/main.py 是普通文件
    decision, reason = decide("src/main.py")
    assert decision == "ask", reason


def test_check_empty_content_asks(ws):
    # 空文件是正常需求，比如 __init__.py
    decision, reason = decide("pkg/__init__.py", content="")
    assert decision == "ask", reason


# ---------------------------------------------------------------------------
# check：warn 名单，ask 但 reason 里有 ⚠
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rel", ["pyproject.toml", "requirements.txt", "tests/conftest.py"])
def test_check_warn_files(ws, rel):
    decision, reason = decide(rel)
    assert decision == "ask"
    assert "⚠" in reason


# ---------------------------------------------------------------------------
# check：deny
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", [
    "../outside.txt",              # 工作目录外
    "~/.zshrc",                    # ~ 展开后在家目录
    "/dev/null",                   # 系统路径
    ".env", ".ENV", "config/.env.local",   # 敏感，大小写
    "id_rsa",                      # 私钥
    ".git/hooks/pre-commit",       # 读写都挡
    ".github/workflows/ci.yml",    # 只挡写
    ".vscode/tasks.json",
    ".pre-commit-config.yaml",
    "main.py", "tools/bash.py", "utils/core.py", "pytest.ini",   # harness 自己
])
def test_check_denies(ws, path):
    decision, reason = decide(path)
    assert decision == "deny", f"{path}: {reason}"


def test_check_denies_directory(ws):
    (ws / "src").mkdir()
    decision, _ = decide("src")
    assert decision == "deny"


def test_check_denies_symlink_to_outside(ws):
    secret = touch(ws.parent, "secret.txt", "top secret")
    (ws / "notes.txt").symlink_to(secret)
    decision, _ = decide("notes.txt")
    assert decision == "deny"


@pytest.mark.parametrize("content", [None, 123, ["a"], b"bytes"])
def test_check_denies_non_string_content(ws, content):
    decision, _ = decide("hello.txt", content=content)
    assert decision == "deny"


@pytest.mark.parametrize("inp", [{}, {"path": "a.txt"}, {"content": "hi"}])
def test_check_denies_missing_keys(ws, inp):
    # Claude 漏了 key：不能 KeyError，要 deny
    decision, _ = write.check(inp)
    assert decision == "deny"


# ---------------------------------------------------------------------------
# read 和 write 的权限真的不一样
# ---------------------------------------------------------------------------
def test_github_workflow_readable_but_not_writable(ws):
    touch(ws, ".github/workflows/ci.yml", "on: push")
    assert read.check({"path": ".github/workflows/ci.yml"})[0] == "allow"
    assert write.check({"path": ".github/workflows/ci.yml", "content": "x"})[0] == "deny"


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def test_run_creates_file(ws):
    out = write.run(path="hello.txt", content="hi\n")
    assert "Created" in out
    assert (ws / "hello.txt").read_text(encoding="utf-8") == "hi\n"


def test_run_creates_parent_folders(ws):
    out = write.run(path="src/utils/new.py", content="x = 1\n")
    assert "Created" in out
    assert (ws / "src/utils/new.py").read_text(encoding="utf-8") == "x = 1\n"


def test_run_overwrites(ws):
    touch(ws, "hello.txt", "old content that is longer")
    out = write.run(path="hello.txt", content="new")
    assert "Overwrote" in out
    assert (ws / "hello.txt").read_text(encoding="utf-8") == "new"   # 旧内容完全没了


def test_run_writes_unicode(ws):
    write.run(path="zh.txt", content="你好，蘑菇 🍄")
    assert (ws / "zh.txt").read_text(encoding="utf-8") == "你好，蘑菇 🍄"


def test_run_writes_empty_file(ws):
    write.run(path="pkg/__init__.py", content="")
    assert (ws / "pkg/__init__.py").read_text(encoding="utf-8") == ""


def test_run_returns_string(ws):
    # Claude 只看得到返回值，成功时也必须返回字符串，不能是 None
    assert isinstance(write.run(path="a.txt", content="x"), str)


def test_run_directory_returns_error(ws):
    (ws / "src").mkdir()
    out = write.run(path="src", content="x")
    assert out.startswith("Error")


def test_write_then_read_roundtrip(ws):
    write.run(path="note.md", content="# title\nbody\n")
    assert read.run(path="note.md") == "# title\nbody\n"