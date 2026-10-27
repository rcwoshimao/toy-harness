"""path_policy 的测试：上面列的每个情况各一条。

所有测试都把 tmp_path 当成工作目录，不会碰到你真实的文件。
"""
import os
import pytest
from tools import path_policy
from tools.path_policy import check_read


@pytest.fixture
def ws(tmp_path):
    return tmp_path.resolve()


def decide(path, ws):
    decision, reason =check_read(str(path), workspace=ws)
    return decision, reason


def touch(ws, rel, content="x"):
    f = ws / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content)
    return f


# ---------------------------------------------------------------------------
# 正常情况
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rel", [
    "notes.txt",
    "src/main.py",
    "id_rsa.pub",                   # 公钥放行
    ".gitignore",
    ".github/workflows/ci.yml",
    ".vscode/settings.json",
    ".eslintrc.json",
    "environment.txt",              # 名字里有 env 但不是 env 文件
])
def test_allowed(ws, rel):
    touch(ws, rel)
    decision, reason = decide(ws / rel, ws)
    assert decision == "allow", reason


def test_relative_path_allowed(ws):
    touch(ws, "a/b.txt")
    decision, reason = check_read("a/b.txt", workspace=ws)
    assert decision == "allow", reason

# ---------------------------------------------------------------------------
# 敏感文件名
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rel", [
    # env
    ".env", ".env.local", ".env.production", "config/.env",
    "production.env", ".envrc",
    # 陷阱 3：大小写
    ".ENV", ".Env.Local", "SERVER.PEM",
    # 私钥、证书
    "id_rsa", "id_ed25519", "id_rsa_backup", "server.pem", "tls.key",
    "cert.p12", "cert.pfx",
    # 云凭证
    "credentials.json", "service-account-prod.json",
    "application_default_credentials.json",
    "terraform.tfstate", "terraform.tfstate.backup", "prod.tfvars",
    # 工具 token
    ".npmrc", ".netrc", ".git-credentials", ".pypirc", ".my.cnf", ".pgpass",
    # 通用 secrets
    "secrets.yaml", "secrets.json", "secrets/db.txt",
    # 历史
    ".zsh_history", ".bash_history", ".python_history",
    # macOS
    "login.keychain-db",
])
def test_sensitive_names_denied(ws, rel):
    decision, reason = decide(ws / rel, ws)
    assert decision == "deny", f"{rel}: {reason}"


# ---------------------------------------------------------------------------
# 陷阱 1：敏感的是上层目录，不是文件名
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rel", [
    ".ssh/config",
    ".ssh/known_hosts",
    ".aws/config",
    ".kube/config",
    ".docker/config.json",
    ".config/gh/hosts.yml",
    ".git/config",
    ".claude/.credentials.json",
    "Library/Keychains/login.keychain-db",
    "Library/Application Support/Google/Chrome/Default/Login Data",
    "deep/nested/.ssh/id_rsa",
])
def test_sensitive_dirs_denied(ws, rel):
    decision, reason = decide(ws / rel, ws)
    assert decision == "deny", f"{rel}: {reason}"


def test_unknown_dotfile_denied(ws):
    decision, reason = decide(ws / ".some_secret_config", ws)
    assert decision == "deny", reason


def test_file_inside_allowed_dot_dir_still_checked(ws):
    decision, reason = decide(ws / ".github/.env", ws)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 工作目录以外
# ---------------------------------------------------------------------------
def test_outside_workspace_denied(ws):
    decision, reason = decide(ws.parent / "other.txt", ws)
    assert decision == "deny", reason


def test_dotdot_escape_denied(ws):
    decision, reason =check_read("sub/../../escape.txt", workspace=ws)
    assert decision == "deny", reason


def test_absolute_system_file_denied(ws):
    decision, reason =check_read("/etc/passwd", workspace=ws)
    assert decision == "deny", reason


# 陷阱 4：~ 要展开
@pytest.mark.parametrize("path", ["~/.ssh/id_rsa", "~/.aws/credentials", "~/.zsh_history"])
def test_home_paths_denied(ws, path):
    decision, reason =check_read(path, workspace=ws)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 陷阱 2：软链接
# ---------------------------------------------------------------------------
def test_symlink_pointing_outside_denied(ws, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "secret.txt"
    outside.write_text("secret")
    link = ws / "notes.txt"
    link.symlink_to(outside)
    decision, reason = decide(link, ws)
    assert decision == "deny", reason


def test_innocent_name_symlink_to_env_denied(ws):
    touch(ws, ".env", "API_KEY=123")
    link = ws / "notes.txt"
    link.symlink_to(ws / ".env")
    decision, reason = decide(link, ws)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 陷阱 5：不是普通文件
# ---------------------------------------------------------------------------
def test_directory_denied(ws):
    (ws / "folder").mkdir()
    decision, reason = decide(ws / "folder", ws)
    assert decision == "deny", reason


@pytest.mark.parametrize("path", ["/dev/zero", "/dev/urandom", "/proc/self/environ"])
def test_system_special_files_denied(ws, path):
    decision, reason =check_read(path, workspace=ws)
    assert decision == "deny", reason


def test_fifo_inside_workspace_denied(ws):
    fifo = ws / "pipe"
    os.mkfifo(fifo)
    decision, reason = decide(fifo, ws)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 陷阱 6：超大文件
# ---------------------------------------------------------------------------
def test_huge_file_denied(ws, monkeypatch):
    monkeypatch.setattr(path_policy, "MAX_READ_BYTES", 10)
    touch(ws, "big.txt", "a" * 50)
    decision, reason = decide(ws / "big.txt", ws)
    assert decision == "deny", reason


def test_file_at_limit_allowed(ws, monkeypatch):
    monkeypatch.setattr(path_policy, "MAX_READ_BYTES", 10)
    touch(ws, "ok.txt", "a" * 10)
    decision, reason = decide(ws / "ok.txt", ws)
    assert decision == "allow", reason


# ---------------------------------------------------------------------------
# 奇怪的输入
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", ["", "   ", "a\x00b", None, 123])
def test_bad_input_denied(ws, path):
    decision, reason =check_read(path, workspace=ws)
    assert decision == "deny", reason


def test_returns_two_strings(ws):
    result =check_read("notes.txt", workspace=ws)
    assert isinstance(result, tuple) and len(result) == 2
    assert all(isinstance(x, str) for x in result)