"""bash 工具的测试：check 的决定 + run 的输出。

第 3 天以后的规则：读写文件一律走 read / write 工具，bash 不再负责读写文件。

跑法（在项目根目录）：  pytest tests/test_bash.py -v
                       pytest -k bypass      只跑「绕过」那几组

两种断言：
  == "deny" / "allow" / "ask"   规则很明确的
  != "allow"                    只要求「不能自动放行」；deny 还是 ask 由你的设计决定
"""
import pytest
from tools import bash


def decide(command):
    decision, reason = bash.check({"command": command})
    return decision, reason


# ---------------------------------------------------------------------------
# 1. 串联 / 重定向 / 变量：不管第一个词是什么，一律 deny
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "ls; rm x",
    "ls && pwd",
    "ls || pwd",
    "ls | head",
    "echo hi > f.txt",            # 以前写文件的方式
    "echo hi >> f.txt",
    "wc < f.txt",
    "echo $HOME",
    "echo `whoami`",
    "echo $(whoami)",
    "ls &",
    # Claude 真的试过的
    'which faketool && faketool; echo "exit: $?"',
    'python3 -c "from tools.eat import run; print(run(5))"',
])
def test_shell_operators_denied(command):
    decision, reason = decide(command)
    assert decision == "deny", reason


# ---------------------------------------------------------------------------
# 2. 通配符：shell 会先展开，挡了 ".env" 这个字也没用
#    （需要 SHELL_METACHARS 里有 * ? [ ] ~）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "wc .en?",
    "wc .e*",
    "wc .[e]nv",
    "ls ~/.ssh",
])
def test_glob_bypass_not_allowed(command):
    decision, reason = decide(command)
    assert decision != "allow", reason


# ---------------------------------------------------------------------------
# 3. DENY 名单：就算按了 y 也不能跑
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    # 解释器
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
# 4. 用完整路径绕过：check 里要用 os.path.basename
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "/bin/rm x",
    "/usr/bin/python3 -c 'print(1)'",
    "/bin/bash -c 'ls'",
])
def test_full_path_cannot_bypass_deny(command):
    decision, reason = decide(command)
    assert decision == "deny", reason


@pytest.mark.parametrize("command", [
    "/bin/cat .env",
    "/usr/bin/grep KEY .env",
])
def test_full_path_cannot_bypass_read_rules(command):
    decision, reason = decide(command)
    assert decision != "allow", reason


# ---------------------------------------------------------------------------
# 5. 安全的命令：自动通过
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "ls",
    "ls -la tools",
    "pwd",
    "echo hello",
    "wc -l main.py",
    'find . -maxdepth 3 -iname "eat.py"',
    "git status",
    "git log",
    "git diff",
])
def test_safe_commands_allowed(command):
    decision, reason = decide(command)
    assert decision == "allow", reason


# ---------------------------------------------------------------------------
# 6. 要问你的：不在名单里、git 写操作、解析不了
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "some_unknown_program",
    "pytest",                   # 合理但不在名单里
    "git push",
    "git reset --hard",
    "git commit -m x",
    "git",                      # 没有子命令
    'ls "unterminated',         # shlex 解析失败
])
def test_needs_approval(command):
    decision, reason = decide(command)
    assert decision == "ask", reason


# ---------------------------------------------------------------------------
# 7. 读文件：现在归 read 工具管，bash 不能自动放行
#    以前在 SAFE 里的 cat / head / tail / grep / rg 拿掉了
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "cat main.py",              # 以前是 allow，现在不是
    "cat .env",
    "head .env",
    "tail .env",
    "grep KEY .env",
    "grep '' .env",
    "rg KEY",
    "less .env",
    "more .env",
])
def test_old_read_commands_not_allowed(command):
    decision, reason = decide(command)
    assert decision != "allow", reason


@pytest.mark.parametrize("command", [
    # 不像「读文件」，但都会把整个文件印出来
    "sort .env",
    "uniq .env",
    "nl .env",
    "tac .env",
    "rev .env",
    "diff .env main.py",
    "sed -n p .env",
    "awk 1 .env",
    "strings .env",
    "xxd .env",
    "od -c .env",
    "base64 .env",
    "hexdump -C .env",
    "column .env",
    "fold .env",
    "cut -c1- .env",
    "paste .env",
])
def test_sneaky_read_bypass_not_allowed(command):
    decision, reason = decide(command)
    assert decision != "allow", reason


@pytest.mark.parametrize("command", [
    # git 是 SAFE，但这些能印出任何文件，不只是 git 管理的
    "git diff --no-index .env main.py",
    "git show HEAD:.env",
    "git grep KEY",
    "git cat-file -p HEAD",
])
def test_git_read_bypass_not_allowed(command):
    decision, reason = decide(command)
    assert decision != "allow", reason


# ---------------------------------------------------------------------------
# 8. 写文件：现在归 write 工具管（它有确认 + 路径检查）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", [
    "touch a.txt",
    "mkdir notes",
    "cp main.py backup.py",
    "mv main.py old.py",
    "tee a.txt",
    "ln -s .env notes.txt",     # 做一个指向 .env 的软链接
    "sed -i s/a/b/ main.py",
    "truncate -s 0 main.py",
    "dd if=/dev/zero of=main.py",
])
def test_write_bypass_not_allowed(command):
    decision, reason = decide(command)
    assert decision != "allow", reason


@pytest.mark.parametrize("command", [
    # SAFE 里的命令，加了这些参数就会写文件或执行别的程序
    "find . -delete",
    "find . -exec rm {} ;",
    "find . -execdir ls ;",
    "find . -ok rm {} ;",
    "find . -fprint out.txt",
    "find . -fls out.txt",
    "git log --output=out.txt",
    "git diff --output=out.txt",
])
def test_dangerous_flags_not_allowed(command):
    decision, reason = decide(command)
    assert decision != "allow", reason


# ---------------------------------------------------------------------------
# 9. 奇怪的输入
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", ["", "   "])
def test_empty_command_denied(command):
    decision, reason = decide(command)
    assert decision == "deny", reason


def test_missing_command_key_does_not_crash():
    # Claude 漏了 command：不能 KeyError
    decision, _ = bash.check({})
    assert decision == "deny"


def test_check_returns_two_strings():
    """之前 'too many values to unpack' 的 bug 就是这里没守住。"""
    result = bash.check({"command": "ls"})
    assert isinstance(result, tuple) and len(result) == 2
    assert all(isinstance(x, str) for x in result)


# ---------------------------------------------------------------------------
# 10. description：要叫 Claude 用 read / write，而且名字要对得上
# ---------------------------------------------------------------------------
def test_description_points_to_file_tools():
    desc = bash.SCHEMA["description"]
    assert "read" in desc and "write" in desc
    assert "read_file" not in desc and "write_file" not in desc   # 改名前的旧名字


# ---------------------------------------------------------------------------
# 11. run：真的执行（只用无害命令）
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


def test_run_returns_string():
    assert isinstance(bash.run("pwd"), str)