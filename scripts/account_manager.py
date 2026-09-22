import sys
import os
import time
import subprocess
import ctypes
import json
import base64
from ctypes import wintypes
import unicodedata

if sys.platform == "win32":
    import msvcrt
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass

advapi32 = ctypes.windll.advapi32

ACCOUNTS_DIR = os.path.expanduser(r"~\.gemini\accounts")
os.makedirs(ACCOUNTS_DIR, exist_ok=True)

# ANSI Color codes
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_CYAN    = "\033[36m"
C_GREEN   = "\033[32m"
C_YELLOW  = "\033[33m"
C_GRAY    = "\033[90m"
C_MAGENTA = "\033[35m"

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]

def decode_jwt_claims(id_token):
    try:
        parts = id_token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            payload += "=" * (-len(payload) % 4)
            return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        pass
    return {}

def get_account_meta_from_blob(blob_str):
    try:
        data = json.loads(blob_str)
        email = "unknown"
        name = ""
        expiry = ""
        if "id_token" in data:
            claims = decode_jwt_claims(data["id_token"])
            email = claims.get("email", "unknown")
            name = claims.get("name", "")
        if "token" in data and isinstance(data["token"], dict):
            expiry = data["token"].get("expiry", "")
        return {
            "email": email,
            "name": name,
            "expiry": expiry,
            "auth_method": data.get("auth_method", "consumer"),
        }
    except Exception:
        return {"email": "unknown", "name": "", "expiry": "", "auth_method": "unknown"}

def read_current_cred():
    pcred = ctypes.POINTER(CREDENTIAL)()
    if advapi32.CredReadW("gemini:antigravity", 1, 0, ctypes.byref(pcred)):
        c = pcred.contents
        blob = ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize).decode("utf-8")
        advapi32.CredFree(pcred)
        meta = get_account_meta_from_blob(blob)
        return meta, blob
    return None, None

def write_cred(blob_str):
    raw_bytes = blob_str.encode("utf-8")
    c_out = CREDENTIAL()
    c_out.Type = 1  # CRED_TYPE_GENERIC
    c_out.TargetName = "gemini:antigravity"
    c_out.CredentialBlobSize = len(raw_bytes)
    c_out.CredentialBlob = (ctypes.c_byte * len(raw_bytes))(*raw_bytes)
    c_out.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
    c_out.UserName = "antigravity"
    return advapi32.CredWriteW(ctypes.byref(c_out), 0) != 0

def get_saved_accounts():
    files = [f for f in os.listdir(ACCOUNTS_DIR) if f.endswith(".json")]
    accounts = []
    for f in sorted(files):
        alias = f[:-5]
        with open(os.path.join(ACCOUNTS_DIR, f), "r", encoding="utf-8") as fp:
            meta = get_account_meta_from_blob(fp.read())
        accounts.append((alias, meta))
    return accounts

def str_disp_w(s):
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return w

def pad_str(s, target_width, align="left"):
    curr_w = str_disp_w(s)
    if curr_w >= target_width:
        return s
    diff = target_width - curr_w
    if align == "left":
        return s + " " * diff
    elif align == "right":
        return " " * diff + s
    else:
        left_pad = diff // 2
        right_pad = diff - left_pad
        return " " * left_pad + s + " " * right_pad

def make_card_line(styled_text, raw_text, width=66):
    inner_width = width - 2
    w = str_disp_w(raw_text)
    pad = max(0, inner_width - w)
    return f"{C_CYAN}│{C_RESET}{styled_text}" + " " * pad + f"{C_CYAN}│{C_RESET}"

def print_hud_card():
    current_meta, _ = read_current_cred()
    current_email = current_meta["email"] if current_meta else "未登录"
    accounts = get_saved_accounts()

    current_alias = "未关联别名"
    for alias, meta in accounts:
        if meta["email"] == current_email:
            current_alias = alias
            break

    width = 66
    inner = width - 2
    border_top = f"{C_CYAN}┌" + "─" * inner + f"┐{C_RESET}"
    border_mid = f"{C_CYAN}├" + "─" * inner + f"┤{C_RESET}"
    border_bot = f"{C_CYAN}└" + "─" * inner + f"┘{C_RESET}"

    title = " AGY 账号切换中心 (zh) "
    pad_t = (inner - str_disp_w(title)) // 2
    rem_t = inner - str_disp_w(title) - pad_t
    title_line = f"{C_CYAN}│{C_RESET}" + " " * pad_t + f"{C_BOLD}{C_CYAN}{title}{C_RESET}" + " " * rem_t + f"{C_CYAN}│{C_RESET}"

    print()
    print(border_top)
    print(title_line)
    print(border_mid)

    # Active line
    raw_active = f"  当前活跃: {current_email} [{current_alias}]"
    styled_active = f"  当前活跃: {C_GREEN}{current_email}{C_RESET} [{C_BOLD}{current_alias}{C_RESET}]"
    print(make_card_line(styled_active, raw_active, width))
    print(f"{C_CYAN}│" + " " * inner + f"│{C_RESET}")

    # Accounts header
    print(make_card_line(f"  {C_BOLD}已保存账号列表:{C_RESET}", "  已保存账号列表:", width))

    if not accounts:
        print(make_card_line(f"    {C_GRAY}(暂无保存的账号，输入 zh add 自动添加){C_RESET}", "    (暂无保存的账号，输入 zh add 自动添加)", width))
    else:
        for idx, (alias, meta) in enumerate(accounts, 1):
            is_active = (meta["email"] == current_email)
            mark = f"{C_GREEN}● [当前使用]{C_RESET}" if is_active else "           "
            raw_mark = "● [当前使用]" if is_active else "           "
            
            padded_alias = pad_str(alias, 12, "left")
            padded_email = pad_str(meta['email'], 26, "left")
            
            raw_line = f"    [{idx}] {padded_alias} {padded_email} {raw_mark}"
            styled_line = f"    [{idx}] {C_BOLD}{padded_alias}{C_RESET} {padded_email} {mark}"
            print(make_card_line(styled_line, raw_line, width))

    # Add line
    raw_add = "    [+] 自动添加新账号 (输入 zh add 或 zh 添加)"
    styled_add = f"    {C_YELLOW}[+]{C_RESET} 自动添加新账号 (输入 {C_YELLOW}zh add{C_RESET} 或 {C_YELLOW}zh 添加{C_RESET})"
    print(make_card_line(styled_add, raw_add, width))

    print(f"{C_CYAN}│" + " " * inner + f"│{C_RESET}")
    raw_hdr = "  快捷指令 (全面支持中英文，默认自动重载):"
    styled_hdr = f"  {C_GRAY}{raw_hdr}{C_RESET}"
    print(make_card_line(styled_hdr, raw_hdr, width))

    shortcuts = [
        ("zh <序号/别名>", "秒级切换 (例: zh 1 或 zh 主账号)"),
        ("zh 切换 <序号>", "中文切换 (例: zh 切换 1)"),
        ("zh 窗口 (zh ui)", "唤起方向键独立交互窗口"),
        ("zh 添加 [别名]", "一键自动添加账号 (唤起浏览器登录)"),
        ("zh 保存 <别名>", "保存当前账号为指定别名 (支持中文名)"),
        ("zh 重载 (reload)", "一键自动重新载入当前会话"),
        ("zh 删除 <别名>", "删除指定已保存账号"),
        ("zh 状态 (whoami)", "查看当前账号详细认证信息"),
    ]

    for cmd, desc in shortcuts:
        padded_cmd = pad_str(cmd, 18, "left")
        raw_sc = f"    {padded_cmd}  {desc}"
        styled_sc = f"    {C_CYAN}{padded_cmd}{C_RESET}  {desc}"
        print(make_card_line(styled_sc, raw_sc, width))

    print(border_bot)
    print()

def generate_auto_alias(email):
    import re
    base = email.split("@")[0] if "@" in email else "acc"
    clean_base = re.sub(r"[^\w\u4e00-\u9fa5-]", "", base)
    if not clean_base:
        clean_base = "acc"
    saved = [alias for alias, _ in get_saved_accounts()]
    if clean_base not in saved:
        return clean_base
    i = 2
    while f"{clean_base}_{i}" in saved:
        i += 1
    return f"{clean_base}_{i}"

def find_agy_pid():
    kernel32 = ctypes.windll.kernel32
    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ('dwSize', wintypes.DWORD),
            ('cntUsage', wintypes.DWORD),
            ('th32ProcessID', wintypes.DWORD),
            ('th32DefaultHeapID', ctypes.c_size_t),
            ('th32ModuleID', wintypes.DWORD),
            ('cntThreads', wintypes.DWORD),
            ('th32ParentProcessID', wintypes.DWORD),
            ('pcPriClassBase', wintypes.LONG),
            ('dwFlags', wintypes.DWORD),
            ('szExeFile', ctypes.c_char * 260)
        ]
    curr_pid = kernel32.GetCurrentProcessId()
    h = kernel32.CreateToolhelp32Snapshot(2, 0)
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    pids = {}
    if kernel32.Process32First(h, ctypes.byref(e)):
        while True:
            pids[e.th32ProcessID] = (e.th32ParentProcessID, e.szExeFile.decode('latin1', errors='ignore').lower())
            if not kernel32.Process32Next(h, ctypes.byref(e)):
                break
    kernel32.CloseHandle(h)

    pid = curr_pid
    while pid in pids:
        ppid, name = pids[pid]
        if 'agy' in name:
            return pid
        pid = ppid

    for p, (_, name) in pids.items():
        if name == 'agy.exe':
            return p
    return None

def get_current_conversation_id():
    history_file = os.path.expanduser(r"~\.gemini\antigravity-cli\history.jsonl")
    if not os.path.exists(history_file):
        return None
    try:
        with open(history_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in reversed(lines):
            try:
                data = json.loads(line)
                cid = data.get("conversationId")
                if cid:
                    return cid
            except Exception:
                continue
    except Exception:
        pass
    return None

def cmd_reload():
    agy_pid = find_agy_pid()
    cid = get_current_conversation_id()
    cwd = os.getcwd()

    print(f"\n{C_CYAN}[↻] 正在为您自动重新载入 Antigravity 会话并接续上下文...{C_RESET}")
    if cid:
        print(f"{C_GRAY}[*] 保留当前会话上下文: {cid}{C_RESET}")
    else:
        print(f"{C_GRAY}[*] 接续最近会话上下文 (--continue){C_RESET}")

    agy_exe = os.path.expanduser(r"~\AppData\Local\agy\bin\agy.exe")
    if not os.path.exists(agy_exe):
        agy_exe = "agy"

    if cid:
        arg_list = f'--conversation {cid} --dangerously-skip-permissions'
    else:
        arg_list = '--continue --dangerously-skip-permissions'

    ps_script = f"""
    Start-Sleep -Milliseconds 600
    if ({agy_pid or 0} -gt 0) {{
        Stop-Process -Id {agy_pid or 0} -Force -ErrorAction SilentlyContinue
    }}
    Start-Sleep -Milliseconds 400
    Start-Process -FilePath "{agy_exe}" -WorkingDirectory "{cwd}" -ArgumentList "{arg_list}"
    """

    try:
        subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", ps_script])
        print(f"{C_GREEN}[✓] 重载已触发！新会话将完整加载所有历史与上下文。{C_RESET}\n")
    except Exception as e:
        print(f"{C_YELLOW}[-] 自动重新载入失败: {e}，请手动运行 agy -c。{C_RESET}\n")

def cmd_use(target, auto_reload=True):
    accounts = get_saved_accounts()
    alias = target
    if target.isdigit():
        idx = int(target)
        if 1 <= idx <= len(accounts):
            alias = accounts[idx - 1][0]
        else:
            print(f"\n{C_YELLOW}[-] 序号 {target} 超出范围 (1 - {len(accounts)}){C_RESET}\n")
            return False

    path = os.path.join(ACCOUNTS_DIR, f"{alias}.json")
    if not os.path.exists(path):
        print(f"\n{C_YELLOW}[-] 账号别名 [{alias}] 不存在！可用 zh 查看已保存账号。{C_RESET}\n")
        return False

    with open(path, "r", encoding="utf-8") as f:
        blob = f.read()

    if write_cred(blob):
        meta = get_account_meta_from_blob(blob)
        print(f"\n{C_GREEN}{C_BOLD}[✓] 账号已成功切换至: [{alias}] ({meta['email']}){C_RESET}")
        print(f"{C_GREEN}[✓] 凭据已即时写入系统，HUD 状态栏已即时热重载！{C_RESET}")
        if auto_reload:
            cmd_reload()
        else:
            print(f"{C_GRAY}已完成切换（已跳过自动重载）。可随时输入 zh reload 或 zh 重载 手动重新载入。{C_RESET}\n")
        return True
    else:
        print(f"\n{C_YELLOW}[-] 写入凭据管理器失败，错误码: {ctypes.GetLastError()}{C_RESET}\n")
        return False

def cmd_save(alias):
    meta, blob = read_current_cred()
    if not blob:
        print(f"\n{C_YELLOW}[-] 当前未检测到登录凭据，请先在 agy 登录。{C_RESET}\n")
        return
    path = os.path.join(ACCOUNTS_DIR, f"{alias}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(blob)
    print(f"\n{C_GREEN}[✓] 成功保存当前账号为别名 [{alias}] -> {meta['email']}{C_RESET}\n")

def cmd_login(alias=None):
    # 1. 确保当前凭证已被安全备份
    curr_meta, curr_blob = read_current_cred()
    if curr_blob:
        saved = get_saved_accounts()
        already_saved = any(s_meta["email"] == curr_meta["email"] for _, s_meta in saved)
        if not already_saved:
            backup_path = os.path.join(ACCOUNTS_DIR, "default.json")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(curr_blob)
            print(f"{C_GRAY}[*] 当前账号 ({curr_meta['email']}) 已自动备份为 [default]{C_RESET}")

    title_tag = f": [{alias}]" if alias else ""
    print(f"\n{C_CYAN}=== 自动添加新账号{title_tag} ==={C_RESET}")
    print(f"{C_YELLOW}[1/3] 准备登录环境（正在清空钥匙串临时凭据）...{C_RESET}")

    # 删除当前凭据以触发 agy 登录流程
    advapi32.CredDeleteW("gemini:antigravity", 1, 0)

    print(f"{C_GREEN}[2/3] 正在启动登录向导窗口，请在弹出的浏览器中登录您的新 Google 账号...{C_RESET}")
    try:
        subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/c", "agy"])
    except Exception as e:
        print(f"{C_YELLOW}[-] 启动 agy 失败: {e}{C_RESET}")

    print(f"{C_GRAY}[*] 正在等待浏览器登录完成 (按 Ctrl+C 可取消并恢复原账号)...{C_RESET}")

    start_time = time.time()
    success = False
    try:
        while time.time() - start_time < 180:
            time.sleep(2)
            new_meta, new_blob = read_current_cred()
            if new_blob and new_meta.get("email") and new_meta.get("email") != "unknown":
                email = new_meta["email"]
                final_alias = alias if alias else generate_auto_alias(email)
                path = os.path.join(ACCOUNTS_DIR, f"{final_alias}.json")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_blob)
                print(f"\n{C_GREEN}{C_BOLD}[3/3] [✓] 新账号自动添加成功！{C_RESET}")
                print(f"      邮箱: {C_BOLD}{email}{C_RESET}")
                print(f"      别名: {C_BOLD}[{final_alias}]{C_RESET}")
                print(f"{C_CYAN}已自动存入账号库并设为活跃账号！{C_RESET}\n")
                cmd_reload()
                success = True
                break
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}[!] 用户取消登录。{C_RESET}")

    if not success:
        if curr_blob:
            print(f"{C_YELLOW}[!] 未检测到新账号登录，正在恢复原账号...{C_RESET}")
            write_cred(curr_blob)
            print(f"{C_GREEN}[✓] 已恢复原账号 ({curr_meta['email']})。{C_RESET}\n")
        else:
            print(f"{C_YELLOW}[!] 未检测到有效登录凭据。{C_RESET}\n")

def cmd_whoami():
    meta, _ = read_current_cred()
    if meta:
        print(f"\n{C_CYAN}=== Antigravity 活动账号 ==={C_RESET}")
        print(f"  邮箱 (Email)      : {C_GREEN}{meta['email']}{C_RESET}")
        if meta["name"]:
            print(f"  姓名 (Name)       : {meta['name']}")
        print(f"  认证方式 (Method) : {meta['auth_method']}")
        if meta["expiry"]:
            print(f"  令牌过期时间      : {meta['expiry']}")
        print()
    else:
        print(f"\n{C_YELLOW}[-] 当前 Windows 凭据管理器中未检测到有效凭据。{C_RESET}\n")

def cmd_remove(alias):
    path = os.path.join(ACCOUNTS_DIR, f"{alias}.json")
    if not os.path.exists(path):
        print(f"\n{C_YELLOW}[-] 账号别名 [{alias}] 不存在！{C_RESET}\n")
        return
    os.remove(path)
    print(f"\n{C_GREEN}[✓] 已删除账号别名: [{alias}]{C_RESET}\n")

def render_interactive_card_lines(accounts, current_email, options, selected):
    current_alias = "未关联别名"
    for alias, meta in accounts:
        if meta["email"] == current_email:
            current_alias = alias
            break

    width = 66
    inner = width - 2
    lines = []
    lines.append(f"{C_CYAN}┌" + "─" * inner + f"┐{C_RESET}")
    title = " AGY 账号切换中心 (zh) "
    pad_t = (inner - str_disp_w(title)) // 2
    rem_t = inner - str_disp_w(title) - pad_t
    lines.append(f"{C_CYAN}│{C_RESET}" + " " * pad_t + f"{C_BOLD}{C_CYAN}{title}{C_RESET}" + " " * rem_t + f"{C_CYAN}│{C_RESET}")
    lines.append(f"{C_CYAN}├" + "─" * inner + f"┤{C_RESET}")

    # Active line
    raw_active = f"  当前活跃: {current_email} [{current_alias}]"
    styled_active = f"  当前活跃: {C_GREEN}{current_email}{C_RESET} [{C_BOLD}{current_alias}{C_RESET}]"
    lines.append(make_card_line(styled_active, raw_active, width))
    lines.append(f"{C_CYAN}│" + " " * inner + f"│{C_RESET}")

    # Tip line
    tip = "  账号列表 (使用 ↑/↓ 选择，Enter 确认切换并自动重载):"
    lines.append(make_card_line(f"{C_BOLD}{tip}{C_RESET}", tip, width))

    for idx, (kind, alias, meta) in enumerate(options):
        is_sel = (idx == selected)
        ptr = f"{C_CYAN}{C_BOLD}> {C_RESET}" if is_sel else "  "
        raw_ptr = "> " if is_sel else "  "

        if kind == "account":
            is_active = (meta["email"] == current_email)
            raw_mark = "● [当前使用]" if is_active else "           "
            mark = f"{C_GREEN}● [当前使用]{C_RESET}" if is_active else "           "
            mail = meta["email"]

            padded_alias = pad_str(alias, 12, "left")
            padded_mail = pad_str(mail, 26, "left")

            raw_line = f"  {raw_ptr}[{idx+1}] {padded_alias} {padded_mail} {raw_mark}"
            hl = f"{C_CYAN}{C_BOLD}" if is_sel else ""
            hl_end = f"{C_RESET}" if is_sel else ""
            styled_line = f"  {ptr}[{idx+1}] {hl}{padded_alias}{hl_end} {padded_mail} {mark}"
            lines.append(make_card_line(styled_line, raw_line, width))
        else:
            raw_line = f"  {raw_ptr}[+] 自动添加新账号 (唤起浏览器登录)"
            hl = f"{C_YELLOW}{C_BOLD}" if is_sel else f"{C_YELLOW}"
            styled_line = f"  {ptr}{hl}[+] 自动添加新账号{C_RESET} (唤起浏览器登录)"
            lines.append(make_card_line(styled_line, raw_line, width))

    lines.append(f"{C_CYAN}│" + " " * inner + f"│{C_RESET}")
    foot = "  快捷键: [↑/↓] 移动   [Enter] 确认切换   [+] 添加   [q] 退出"
    lines.append(make_card_line(f"{C_GRAY}{foot}{C_RESET}", foot, width))
    lines.append(f"{C_CYAN}└" + "─" * inner + f"┘{C_RESET}")
    return lines

def is_under_agy():
    kernel32 = ctypes.windll.kernel32
    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ('dwSize', wintypes.DWORD),
            ('cntUsage', wintypes.DWORD),
            ('th32ProcessID', wintypes.DWORD),
            ('th32DefaultHeapID', ctypes.c_size_t),
            ('th32ModuleID', wintypes.DWORD),
            ('cntThreads', wintypes.DWORD),
            ('th32ParentProcessID', wintypes.DWORD),
            ('pcPriClassBase', wintypes.LONG),
            ('dwFlags', wintypes.DWORD),
            ('szExeFile', ctypes.c_char * 260)
        ]
    curr_pid = kernel32.GetCurrentProcessId()
    h = kernel32.CreateToolhelp32Snapshot(2, 0)
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    pids = {}
    if kernel32.Process32First(h, ctypes.byref(e)):
        while True:
            pids[e.th32ProcessID] = (e.th32ParentProcessID, e.szExeFile.decode('latin1', errors='ignore').lower())
            if not kernel32.Process32Next(h, ctypes.byref(e)):
                break
    kernel32.CloseHandle(h)

    pid = curr_pid
    while pid in pids:
        ppid, name = pids[pid]
        if 'agy' in name:
            return True, pid
        pid = ppid
    return False, None

def run_arrow_selector(accounts):
    current_meta, _ = read_current_cred()
    current_email = current_meta["email"] if current_meta else ""

    options = []
    for alias, meta in accounts:
        options.append(("account", alias, meta))
    options.append(("add", "自动添加新账号", None))

    selected = 0
    for i, (kind, alias, meta) in enumerate(options):
        if kind == "account" and meta["email"] == current_email:
            selected = i
            break

    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        first_render = True
        total_lines = 0

        while True:
            card_lines = render_interactive_card_lines(accounts, current_email, options, selected)
            if first_render:
                print()
                for l in card_lines:
                    print(l)
                total_lines = len(card_lines)
                first_render = False
            else:
                sys.stdout.write(f"\r\033[{total_lines}A")
                for l in card_lines:
                    sys.stdout.write(l + "\n")
                sys.stdout.flush()

            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                ext = msvcrt.getwch()
                if ext == "H":  # Up arrow
                    selected = (selected - 1) % len(options)
                elif ext == "P":  # Down arrow
                    selected = (selected + 1) % len(options)
            elif key in ("k", "K", "w", "W"):
                selected = (selected - 1) % len(options)
            elif key in ("j", "J", "s", "S"):
                selected = (selected + 1) % len(options)
            elif key in ("\r", "\n"):
                break
            elif key in ("\x1b", "q", "Q"):
                selected = -1
                break
            elif key in ("+", "a", "A"):
                selected = len(options) - 1
                break
            elif key.isdigit():
                num = int(key)
                if 1 <= num <= len(accounts):
                    selected = num - 1
                    break

    except (KeyboardInterrupt, EOFError):
        selected = -1
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    if selected == -1:
        print(f"\n{C_GRAY}已退出账号切换。{C_RESET}\n")
        return

    kind, alias, meta = options[selected]
    if kind == "account":
        cmd_use(alias, auto_reload=True)
    elif kind == "add":
        cmd_login(None)

def cmd_ui_popup():
    script_path = os.path.abspath(__file__)
    print(f"\n{C_CYAN}[↻] 正在唤起独立方向键交互窗口...{C_RESET}")
    try:
        subprocess.Popen(f'cmd.exe /c start "AGY 账号选择器 (zh)" cmd /c "chcp 65001 >nul && python \"{script_path}\" ui_window"', shell=True)
        print(f"{C_GREEN}[✓] 独立选择窗口已弹出！使用方向键 ↑/↓ 选择并按回车即可自动重载。{C_RESET}\n")
    except Exception as e:
        print(f"{C_YELLOW}[-] 唤起窗口失败: {e}{C_RESET}\n")

def interactive_mode():
    accounts = get_saved_accounts()
    under_agy, _ = is_under_agy()

    # If running inside agy session or not in a standalone tty, print card instantly without blocking!
    if under_agy or not sys.stdin.isatty():
        print_hud_card()
        return

    # Running in standalone PowerShell/CMD, run interactive selector
    run_arrow_selector(accounts)

def main():
    if len(sys.argv) < 2:
        interactive_mode()
        return

    arg1 = sys.argv[1].lower()

    # Help
    if arg1 in ("-h", "--help", "help", "帮助", "说明"):
        print_hud_card()
    # Whoami / Status
    elif arg1 in ("whoami", "current", "status", "当前", "谁", "状态"):
        cmd_whoami()
    # List
    elif arg1 in ("list", "ls", "列表", "账号"):
        print_hud_card()
    # UI / Popup window
    elif arg1 in ("ui", "popup", "select", "窗口", "交互", "选号"):
        cmd_ui_popup()
    elif arg1 in ("ui_window", "selector"):
        accounts = get_saved_accounts()
        run_arrow_selector(accounts)
    # Reload
    elif arg1 in ("reload", "restart", "r", "重载", "重启", "刷新"):
        cmd_reload()
    # Add / Login
    elif arg1 in ("add", "login", "new", "添加", "登录", "新建", "加"):
        alias = sys.argv[2] if len(sys.argv) >= 3 else None
        cmd_login(alias)
    # Save
    elif arg1 in ("save", "保存", "存") and len(sys.argv) >= 3:
        cmd_save(sys.argv[2])
    # Use / Switch
    elif arg1 in ("use", "switch", "切换", "使用", "切") and len(sys.argv) >= 3:
        no_reload = any(x in sys.argv for x in ("--no-reload", "-n", "--不重载"))
        cmd_use(sys.argv[2], auto_reload=not no_reload)
    # Remove / Delete
    elif arg1 in ("rm", "remove", "del", "delete", "删除", "移除", "删") and len(sys.argv) >= 3:
        cmd_remove(sys.argv[2])
    else:
        no_reload = any(x in sys.argv for x in ("--no-reload", "-n", "--不重载"))
        if not cmd_use(sys.argv[1], auto_reload=not no_reload):
            print(f"{C_GRAY}提示: 输入 'zh 帮助' 或直接运行 'zh' 打开可视化面板。{C_RESET}\n")

if __name__ == "__main__":
    main()
