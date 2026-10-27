"""read 工具的测试：check（放不放行）+ run（读出来的内容）。

所有测试都把 tmp_path 下的 ws/ 当成工作目录，不会碰到你真实的文件。
"""
import pytest
from tools import path_policy, read


@pytest.fixture(autouse=True)
def ws(tmp_path, monkeypatch):
    """每条测试都有一个全新的、空的工作目录。check 和 run 都会用到它。"""
    ws = (tmp_path / "ws").resolve()
    ws.mkdir()
    monkeypatch.setattr(path_policy, "WORKSPACE", ws)
    return ws


def touch(ws, rel, content="x"):
    f = ws / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")
    return f


def decide(path):
    return read.check({"path": path})


# ---------------------------------------------------------------------------
# check：放行
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rel", [
    "notes.txt",
    "src/main.py",
    ".github/workflows/ci.yml",   # 读可以，写不行（见 test_write）
    "pyproject.toml",
])
def test_check_allows_normal_files(ws, rel):
    touch(ws, rel)
    decision, reason = decide(rel)
    assert decision == "allow", reason


# ---------------------------------------------------------------------------
# check：拒绝
# ---------------------------------------------------------------------------
def test_check_denies_missing_file_without_crashing(ws):
    decision, reason = decide("nope.txt")
    assert decision == "deny"
    assert "does not exist" in reason


def test_check_denies_missing_path_key(ws):
    # Claude 漏了 path：不能 KeyError，要 deny
    decision, _ = read.check({})
    assert decision == "deny"


@pytest.mark.parametrize("path", ["", "   ", None, 123])
def test_check_denies_bad_path(ws, path):
    decision, _ = decide(path)
    assert decision == "deny"


def test_check_denies_env_file(ws):
    touch(ws, ".env", "API_KEY=123")
    decision, _ = decide(".env")
    assert decision == "deny"


def test_check_denies_outside_workspace(ws):
    touch(ws.parent, "outside.txt")
    decision, _ = decide("../outside.txt")
    assert decision == "deny"


def test_check_denies_directory(ws):
    (ws / "folder").mkdir()
    decision, _ = decide("folder")
    assert decision == "deny"


def test_check_denies_huge_file(ws, monkeypatch):
    monkeypatch.setattr(path_policy, "MAX_READ_BYTES", 10)
    touch(ws, "big.txt", "a" * 50)
    decision, reason = decide("big.txt")
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def test_run_returns_content(ws):
    touch(ws, "hello.txt", "hi\nthere\n")
    assert read.run(path="hello.txt") == "hi\nthere\n"


def test_run_reads_unicode(ws):
    touch(ws, "zh.txt", "你好，蘑菇")
    assert read.run(path="zh.txt") == "你好，蘑菇"


def test_run_short_file_not_truncated(ws, monkeypatch):
    monkeypatch.setattr(read, "MAX_CHARS", 10)
    touch(ws, "short.txt", "a" * 10)          # 刚好等于上限
    out = read.run(path="short.txt")
    assert out == "a" * 10
    assert "truncated" not in out


def test_truncation(ws, monkeypatch):
    monkeypatch.setattr(read, "MAX_CHARS", 10)
    f = touch(ws, "long.txt", "a" * 50)
    out = read.run(path=str(f))
    assert out.startswith("a" * 10)
    assert "truncated" in out
    assert "50" in out


def test_run_binary_file_returns_error(ws):
    (ws / "img.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe\x00\x00")
    out = read.run(path="img.png")
    assert out.startswith("Error")