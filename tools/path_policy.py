"""文件工具共用的路径规则：哪些路径可以碰，哪些不行。

检查顺序（任何一步不过就 deny）：
  0. 输入本身合法（非空字符串、没有 \\0）
  1. 展开 ~，相对路径接到工作目录下，resolve()（处理 .. 和软链接）
  2. 不是 /dev /proc /sys 这类系统特殊路径
  3. 在工作目录以内（允许名单，最重要的一层）
  4. 不是敏感文件（文件名、目录、点开头的文件），全部小写比对
  5. 如果文件存在：必须是普通文件（挡文件夹、设备、FIFO），而且不能太大
任何意外（权限、奇怪的路径）都当成 deny：宁可错挡，不可错放。
"""
import os
from fnmatch import fnmatch
from pathlib import Path

# None 表示「当前工作目录」。用 python main.py 从项目根目录跑，就是项目根目录。
WORKSPACE = None

# 超过这个大小直接拒绝。read_text 会先把整个文件读进内存才截断，所以要在读之前挡。
MAX_READ_BYTES = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------------------------
# 陷阱 5：不是普通文件的「文件」，读起来可能永远读不完
# ---------------------------------------------------------------------------
SYSTEM_PREFIXES = ("/dev", "/proc", "/sys")

# ---------------------------------------------------------------------------
# 敏感文件名（全部小写，fnmatch 通配）
# ---------------------------------------------------------------------------
# 私钥：.pub 结尾的公钥放行，所以单独一组
PRIVATE_KEY_PATTERNS = [
    "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*",
]

SENSITIVE_NAME_PATTERNS = [
    # 环境变量
    ".env", ".env.*", "*.env", ".envrc",
    # 证书、私钥（注意：macOS 的 Keynote 文件也是 .key，一起挡掉）
    "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore", "*.ppk",
    "*.gpg", "*.asc",
    # 云服务凭证
    "credentials", "credentials.json", "credentials.toml",
    "service-account*.json", "serviceaccount*.json",
    "application_default_credentials.json",
    # Terraform 状态文件经常有明文密码
    "*.tfstate", "*.tfstate.backup", "*.tfvars", "*.tfvars.json",
    # 各种工具的 token
    ".netrc", "_netrc", ".git-credentials", ".npmrc", ".yarnrc", ".yarnrc.yml",
    ".pypirc", ".my.cnf", ".pgpass",
    # 通用 secrets 文件
    "secrets.json", "secrets.yaml", "secrets.yml", "secrets.toml",
    # shell / REPL 历史（export API_KEY=... 会留在这里）
    ".*_history", ".lesshst", ".viminfo",
    # macOS 钥匙串、浏览器
    "*.keychain", "*.keychain-db", "cookies", "login data",
]

# 敏感目录：路径里任何一段（或连续几段）是这些，就 deny。全部小写。
SENSITIVE_DIRS = [
    ".ssh", ".aws", ".kube", ".gnupg", ".docker", ".azure", "gcloud",
    ".config/gh", ".claude", ".cargo", ".git",
    "secrets",
    "library/keychains", "library/messages", "library/mail",
    "library/cookies", "library/application support/google/chrome",
    "library/application support/firefox",
]

# 点开头但无害、Claude 写代码时常需要读的。只放行这些，其他点开头的一律挡。
ALLOWED_DOT_NAMES = [
    ".gitignore", ".gitattributes", ".gitkeep", ".github",
    ".vscode", ".editorconfig", ".pre-commit-config.yaml",
    ".dockerignore", ".python-version", ".nvmrc",
    ".prettierrc", ".prettierrc.*", ".prettierignore",
    ".eslintrc", ".eslintrc.*", ".eslintignore",
    ".flake8", ".pylintrc", ".ruff.toml",
]


# 只挡写入：写进去以后会被「执行」的文件。路径相对工作目录，全小写。
# （.git/hooks 已经被 SENSITIVE_DIRS 里的 .git 挡掉，读写都挡）
WRITE_DENY_PATTERNS = [
    ".github/*",                # CI：push 后在 GitHub 上跑
    ".vscode/*",                # tasks.json 能让编辑器跑命令
    ".pre-commit-config.yaml",  # commit 时跑
    # 你的 harness 自己：不让 Claude 改安全规则。按你的目录结构调整
    "main.py", "tools/*", "utils/*", "pytest.ini",
]

# 可以写，但 ask 时要特别提醒你：会改变项目怎么装、怎么跑、怎么测
WRITE_WARN_PATTERNS = [
    "pyproject.toml", "setup.py", "setup.cfg", "requirements*.txt",
    "package.json", "makefile", "dockerfile", "conftest.py", "*/conftest.py",
]

def _workspace(workspace=None) -> Path:
    ws = workspace if workspace is not None else WORKSPACE
    return Path(ws if ws is not None else os.getcwd()).resolve()


def resolve_path(path, workspace=None) -> Path:
    """把 Claude 给的路径变成真实的绝对路径。run() 也应该用这个，和 check 保持一致。

    陷阱 4：~ 不会自动展开，要 expanduser()
    陷阱 2：resolve() 会跟随软链接、消掉 ..，得到真正要读的文件
    """
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = _workspace(workspace) / p
    return p.resolve()


def sensitive_reason(parts):
    """parts：工作目录以下的每一段路径，已经小写。敏感就返回原因，否则返回 None。"""
    if not parts:
        return None
    name = parts[-1]

    # 陷阱 1：检查每一层目录，不只看文件名（~/.ssh/config 的名字只是 config）
    joined = "/" + "/".join(parts) + "/"
    for d in SENSITIVE_DIRS:
        if f"/{d}/" in joined:
            return f"'{d}' is a protected location"

    # 私钥（公钥 .pub 放行）
    if not name.endswith(".pub"):
        for pat in PRIVATE_KEY_PATTERNS:
            if fnmatch(name, pat):
                return f"'{name}' looks like a private key"

    for pat in SENSITIVE_NAME_PATTERNS:
        if fnmatch(name, pat):
            return f"'{name}' looks like a secret or credential file"

    # 点开头的文件或文件夹：除了允许名单都挡
    for part in parts:
        if part.startswith(".") and not any(fnmatch(part, a) for a in ALLOWED_DOT_NAMES):
            return f"hidden file or folder '{part}' is not allowed"
            

    return None


def check_read(path, workspace=None):
    # Basic check for everything 
    decision, reason = check_path(path, workspace)
    if decision == "deny":
        return decision, reason

    ws = _workspace(workspace)
    p = resolve_path(path, ws)
    if p.exists():
        size = p.stat().st_size
        if size > MAX_READ_BYTES:
            return "deny", f"'{path}' is {size} bytes, over the {MAX_READ_BYTES}-byte limit"
    else: 
        return "deny", f"'{path}' does not exist as a file."

    return "allow", "inside workspace and not sensitive"

def check_write(path, content, workspace=None):
    # Basic check for everything 
    decision, reason = check_path(path, workspace)
    if decision == "deny":
        return decision, reason 
    
    if not isinstance(content, str): 
        return "deny", "content must be a string"

    ws = _workspace(workspace)
    p = resolve_path(path, ws)
    parts = [part.lower() for part in p.relative_to(ws).parts]
    rel = "/".join(parts)          # 例如 "tools/bash.py"

    if any(fnmatch(rel, pat) for pat in WRITE_DENY_PATTERNS): 
        return "deny", f"'{rel}' is protected from writing (runs code or is part of the harness)"

    size = len(content.encode("utf-8"))

    reason =  f"{'overwrite' if p.exists() else 'create'} '{rel}' ({size} bytes)"
    if any(fnmatch(rel, pat) for pat in WRITE_WARN_PATTERNS): 
            reason += "⚠ changes how the project installs/runs/tests"
            return "ask", reason 
    
    return "ask", reason


def check_path(path, workspace=None):
    """返回 (decision, reason)，decision 是 "allow" 或 "deny"。"""
    # 0. 输入本身
    if not isinstance(path, str) or not path.strip():
        return "deny", "path must be a non-empty string"
    if "\x00" in path:
        return "deny", "path contains a null byte"
    try:
            ws = _workspace(workspace)
            p = resolve_path(path, ws)

            # 2. 系统特殊路径
            s = str(p)
            if any(s == pre or s.startswith(pre + "/") for pre in SYSTEM_PREFIXES):
                return "deny", f"'{s}' is a system path"

            # 3. 只能在工作目录以内（.. 和指向外面的软链接都在这里被挡）
            if not p.is_relative_to(ws):
                return "deny", f"'{path}' is outside the workspace ({ws})"

            # 4. 敏感文件。陷阱 3：macOS 不分大小写，.ENV 就是 .env，所以先小写
            parts = [part.lower() for part in p.relative_to(ws).parts]
            reason = sensitive_reason(parts)
            if reason:
                return "deny", reason

            # 5. 存在的话：必须是普通文件，而且不能太大
            if p.exists():
                if not p.is_file():
                    return "deny", f"'{path}' is not a regular file (directory, device or pipe)"
                
    except (OSError, ValueError, RuntimeError) as e:
        # 权限不够、路径太怪、软链接死循环……一律当成 deny
        return "deny", f"could not safely inspect '{path}': {e}"
    
    return "allow", "inside workspace and not sensitive"
    