from utils.core import *
import subprocess
import shlex
import time

DENY = {
    # 1. 执行任意代码的解释器（今晚的漏洞）
    "python", "python3", "python3.12", "node", "ruby", "perl", "php",
    "osascript",          # macOS 的 AppleScript，能控制整台电脑
    "bash", "sh", "zsh", "fish", "dash",

    # 2. 包装器：能代替你去跑别的程序，用来绕过名单
    "env", "xargs", "exec", "eval", "command", "builtin",
    "nohup", "nice", "timeout", "time", "watch", "script",

    # 3. 提权
    "sudo", "su", "doas",

    # 4. 删除、破坏
    "rm", "rmdir", "shred", "dd", "mkfs", "diskutil", "truncate",

    # 5. 改权限、改归属
    "chmod", "chown", "chgrp", "chflags", "xattr",

    # 6. 网络：下载、上传、外传数据
    "curl", "wget", "nc", "ncat", "ssh", "scp", "sftp", "rsync", "ftp", "telnet",

    # 7. 进程、系统
    "kill", "killall", "pkill", "shutdown", "reboot", "launchctl", "crontab",
    "defaults",           # macOS 改系统设置

    # 8. 装东西
    "pip", "pip3", "npm", "npx", "brew", "conda", "mamba", "uv",
}

SAFE = {"ls", "pwd", "wc", "echo", "file", "stat",
        "which", "whoami", "date", "uname", "find", "git"}

# 有条件安全：命令本身 OK，但带了这些参数就不算安全
UNSAFE_FLAGS = {
    "find": {"-delete", "-exec", "-execdir", "-ok", "-okdir",
             "-fprint", "-fprint0", "-fprintf", "-fls"},
}

# git 的危险参数：能读任意文件，或者把输出写进文件
UNSAFE_GIT_FLAGS = {"--no-index", "--output", "--ext-diff"}

SAFE_GIT_SUBCOMMANDS = {"status", "log", "diff", "branch"}


log = get_logger(__name__)
log.debug(f"STARTED. IN {os.getcwd()}")

SCHEMA = {
    "name": "bash",
    "description": "Run a shell command. To read or write files, use the read and write tools instead of cat, echo > or similar.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The command given to run in shell. Will time out after 30 seconds.",
            }
        },
        "required": ["command"],
    },
}


def run(command, timeout=30):
    console.print(Panel(command, title="bash", border_style="yellow")) 
    start = time.monotonic()
    proc = subprocess.Popen(command, shell=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        try:
            stdout, stderr = proc.communicate(timeout=1)   # 最多等 1 秒
            break                                          # 跑完了
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                proc.kill()
                stdout, stderr = proc.communicate()
                print(f"\r  stopped after {elapsed:.0f}s")
                return f"Command timed out after {timeout} seconds and was stopped."
            print(f"\r  running for {elapsed:.0f}s...", end="", flush=True)

    print(f"\r  done in {time.monotonic() - start:.1f}s        ")
    # TODO: 用 stdout、stderr、proc.returncode 组装要送回给 Claude 的结果
    # " output = bash(command)" 
    returncode = proc.returncode
    if returncode != 0: # This is safer than == 1 
        return f"command failed. \n return code = {returncode}. \n stdout: {stdout}. \n stderr: {stderr}"
    else: 
        return f"command succeed. \n return code = {returncode}. \n stdout: {stdout}. \n stderr: {stderr}"

def check_command(command):
    """Return (decision, reason). decision is "allow", "deny", or "ask"."""

    # 1. 先挡串联命令。必须第一步做，不然 "ls; rm x" 会被当成 ls
    found = set(SHELL_METACHARS) & set(command)
    if found:
        chars = ", ".join(sorted(found))
        return "deny", f"contains shell operators ({chars}). Run one simple command at a time"

    # 2. 把命令拆成单词
    try:
        words = shlex.split(command)
    except ValueError:
        return "ask", "could not parse the command"
    if not words:
        return "deny", "empty command"

    program = os.path.basename(words[0])
    args = words[1:]

    # 3. 黑名单：直接拒绝
    if program in DENY:
        return "deny", f" '{program}' is never allowed"

    # 4. 不在白名单里：问你
    if program not in SAFE:
        return "ask", f" '{program}' is not in the safe list"

    # 5. 在白名单里，但带了危险参数：问你
    if program in UNSAFE_FLAGS:
        bad = UNSAFE_FLAGS[program] & set(args)
        if bad:
            return "ask", f"'{program}' with {', '.join(sorted(bad))} can change files"

    # 6. git 只放行只读的子命令
    if program == "git":
        if not args or args[0] not in SAFE_GIT_SUBCOMMANDS:
            return "ask", "only read-only git commands are auto-approved"
        
        # --output=out.txt 要先切掉 = 后面，才比得到 "--output"
        if any(a.split("=")[0] in UNSAFE_GIT_FLAGS for a in args):
            return "ask", "this git flag can read or write arbitrary files"

    return "allow", "known safe command"

def check(input):
    command = input.get("command")
    if not isinstance(command, str):
        return "deny", "command must be a string"
    return check_command(command)