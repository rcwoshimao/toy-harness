"""bash 工具的测试：check 的决定 + run 的输出。

跑法（在项目根目录）：  pytest            全部
                       pytest -v         看每一条
                       pytest -k deny    只跑名字里有 deny 的
"""
import pytest
from tools import bash


def decide(command):
    decision, reason = bash.check({"command": command})
    return decision, reason


# ---------------------------------------------------------------------------
# 1. 串联 / 重定向：不管第一个词是什么，一律 deny
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "ls; rm x",
    "ls && pwd",
    "ls || pwd",
    "cat a | head",
    "echo hi > f.txt",
    "cat < f.txt",
    "echo $HOME",
    "ls &",
    # 今晚 Claude 真的试过的
    'which faketool && faketool; echo "exit: $?"',
    'python3 -c "from tools.eat import run; print(run(5))"',
])
def test_shell_operators_denied(command):
    decision, reason = decide(command)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 2. DENY 名单：就算按了 y 也不能跑
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    # 解释器（今晚的漏洞）
    "python3 -c 'print(1)'",
    "python -c 'print(1)'",
    "node -e 'console.log(1)'",
    "bash -c 'ls'",
    "sh -c 'ls'",
    "osascript -e 'beep'",
    # 包装器
    "env rm x",
    "xargs rm",
    "nohup ls",
    # 提权
    "sudo ls",
    # 删除
    "rm x",
    "rm -rf /",
    # 网络
    "curl https://example.com",
    "wget https://example.com",
    # 装东西
    "pip install requests",
])
def test_deny_list(command):
    decision, reason = decide(command)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 3. 用完整路径绕过 DENY：需要在 check_command 里用 os.path.basename
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "/bin/rm x",
    "/usr/bin/python3 -c 'print(1)'",
    "/bin/bash -c 'ls'",
])
def test_full_path_cannot_bypass_deny(command):
    decision, reason = decide(command)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 4. 安全的只读命令：自动通过
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "ls",
    "ls -la tools",
    'find . -maxdepth 3 -iname "*eat*"',
    "git status",
    "git log",
    "git diff",
])
def test_safe_commands_allowed(command):
    decision, reason = decide(command)
    assert decision == "allow", reason


# ---------------------------------------------------------------------------
# 5. 要问你的：不在名单里、git 写操作、危险参数、解析不了
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "some_unknown_program",
    "git push",
    "git reset --hard",
    "git",                      # 没有子命令
    "find . -delete",           # 需要 UNSAFE_FLAGS 里有 find 的 -delete
    'echo "unterminated',       # shlex 解析失败
])
def test_needs_approval(command):
    decision, reason = decide(command)
    assert decision == "ask", reason


def test_empty_command_denied():
    decision, reason = decide("")
    assert decision == "deny", reason


def test_check_returns_two_strings():
    """今晚那个 'too many values to unpack' 的 bug 就是这里没守住。"""
    result = bash.check({"command": "ls"})
    assert isinstance(result, tuple) and len(result) == 2
    assert all(isinstance(x, str) for x in result)


# ---------------------------------------------------------------------------
# 6. run：真的执行（只用无害命令）
# ---------------------------------------------------------------------------
def test_run_success():
    out = bash.run("echo hello")
    assert "succeed" in out
    assert "hello" in out
    assert "return code = 0" in out


def test_run_failure_reports_return_code():
    out = bash.run("ls /definitely/not/a/real/path")
    assert "failed" in out
    assert "return code = 0" not in out


def test_run_timeout():
    out = bash.run("sleep 3", timeout=1)
    assert "timed out" in out