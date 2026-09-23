#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agy-accounts (zh) - Antigravity CLI 多账号秒级极速切换与可视化管理中心
支持 Windows 凭据管理器原生交互、零 Token 损耗、保留历史上下文秒级接续重载
"""

import os
import sys
import json
import time
import ctypes
import base64
import subprocess
import unicodedata
from ctypes import wintypes

if sys.platform == "win32":
    import msvcrt
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", write_through=True)
        sys.stderr.reconfigure(encoding="utf-8", errors="replace", write_through=True)
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
        hOut = kernel32.GetStdHandle(-11)
        if hOut and hOut != -1:
            mode = wintypes.DWORD()
            if kernel32.GetConsoleMode(hOut, ctypes.byref(mode)):
                kernel32.SetConsoleMode(hOut, mode.value | 0x0004 | 0x0008)
    except Exception:
        pass

C_RESET  = "\033[0m"
C_CYAN   = "\033[36m"
C_GREEN  = "\033[32m"
C_YELLOW = "\033[33m"
C_RED    = "\033[31m"
C_BOLD   = "\033[1m"
C_GRAY   = "\033[90m"

ACCOUNTS_DIR = os.path.expanduser(r"~\.gemini\accounts")
ALT_ACCOUNTS_DIR = os.path.expanduser(r"~\.gemini\antigravity-cli\plugin_data\agy-accounts")
os.makedirs(ACCOUNTS_DIR, exist_ok=True)


advapi32 = ctypes.windll.advapi32

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

def sync_oauth_creds_file(blob_str):
    """同步更新 ~/.gemini/oauth_creds.json，确保文件式鉴权读取器与系统凭据完全同步"""
    try:
        data = json.loads(blob_str)
        token_info = data.get("token", {})
        oauth_path = os.path.expanduser(r"~\.gemini\oauth_creds.json")
        curr_oauth = {}
        if os.path.exists(oauth_path):
            try:
                with open(oauth_path, "r", encoding="utf-8") as f:
                    curr_oauth = json.load(f)
            except Exception:
                curr_oauth = {}
        
        if "access_token" in token_info:
            curr_oauth["access_token"] = token_info.get("access_token", "")
        if "refresh_token" in token_info:
            curr_oauth["refresh_token"] = token_info.get("refresh_token", "")
        if "id_token" in data:
            curr_oauth["id_token"] = data.get("id_token", "")
        if "token_type" in token_info:
            curr_oauth["token_type"] = token_info.get("token_type", "Bearer")
        
        expiry_str = token_info.get("expiry", "")
        if expiry_str:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                curr_oauth["expiry_date"] = int(dt.timestamp() * 1000)
            except Exception:
                pass

        if "scope" not in curr_oauth:
            curr_oauth["scope"] = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid"

        with open(oauth_path, "w", encoding="utf-8") as f:
            json.dump(curr_oauth, f, indent=2)
    except Exception:
        pass

def write_cred(blob_str):
    raw_bytes = blob_str.encode("utf-8")
    c_out = CREDENTIAL()
    c_out.Type = 1  # CRED_TYPE_GENERIC
    c_out.TargetName = "gemini:antigravity"
    c_out.CredentialBlobSize = len(raw_bytes)
    c_out.CredentialBlob = (ctypes.c_byte * len(raw_bytes))(*raw_bytes)
    c_out.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
    c_out.UserName = "antigravity"
    ok = advapi32.CredWriteW(ctypes.byref(c_out), 0) != 0
    if ok:
        sync_oauth_creds_file(blob_str)
    return ok

def get_saved_accounts():
    accounts_dict = {}
    for d in (ACCOUNTS_DIR, ALT_ACCOUNTS_DIR):
        if os.path.exists(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".json"):
                    alias = f[:-5]
                    if alias not in accounts_dict:
                        try:
                            with open(os.path.join(d, f), "r", encoding="utf-8") as fp:
                                meta = get_account_meta_from_blob(fp.read())
                            accounts_dict[alias] = meta
                        except Exception:
                            pass
    return sorted(accounts_dict.items(), key=lambda x: x[0])


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

    under_agy, _ = is_under_agy()
    pfx = "!" if under_agy else ""
    raw_hdr = "  快捷指令 (在 agy 对话框中必须加 ! 前缀，默认自动接续重载生效):" if under_agy else "  快捷指令 (全面支持中英文，默认自动接续重载生效):"
    styled_hdr = f"  {C_YELLOW}{C_BOLD}{raw_hdr}{C_RESET}" if under_agy else f"  {C_GRAY}{raw_hdr}{C_RESET}"
    print(make_card_line(styled_hdr, raw_hdr, width))

    shortcuts = [
        (f"{pfx}zh <序号/别名>", f"秒级切换生效 (例: {pfx}zh 1 或 {pfx}zh 主账号)"),
        (f"{pfx}zh 切换 <序号>", f"中文切换 (例: {pfx}zh 切换 1)"),
        (f"{pfx}zh 窗口 ({pfx}zh ui)", "唤起方向键独立交互窗口"),
        (f"{pfx}zh 添加 [别名]", "一键自动添加账号 (唤起浏览器登录)"),
        (f"{pfx}zh 保存 <别名>", "保存当前账号为指定别名 (支持中文名)"),
        (f"{pfx}zh 重载 (reload)", "一键平滑重新载入当前会话上下文"),
        (f"{pfx}zh 删除 <别名>", "删除指定已保存账号"),
        (f"{pfx}zh 状态 (whoami)", "查看当前账号详细认证信息"),
    ]

    for cmd, desc in shortcuts:
        padded_cmd = pad_str(cmd, 21, "left")
        raw_sc = f"    {padded_cmd}  {desc}"
        styled_sc = f"    {C_CYAN}{padded_cmd}{C_RESET}  {desc}"
        print(make_card_line(styled_sc, raw_sc, width))

    if under_agy:
        tip_raw = "  ★ 重点提示: 在 agy 聊天框内输入必须以 ! 开头执行本地命令"
        tip_styled = f"  {C_YELLOW}★ 重点提示:{C_RESET} {C_BOLD}在 agy 聊天框内输入必须以 ! 开头执行本地命令{C_RESET}"
        print(f"{C_CYAN}│" + " " * inner + f"│{C_RESET}")
        print(make_card_line(tip_styled, tip_raw, width))

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

    # 优先沿当前进程树向上查找直接父辈中的 agy 进程
    pid = curr_pid
    while pid in pids and pid != 0:
        ppid, name = pids[pid]
        if 'agy' in name and pid != curr_pid:
            return pid
        pid = ppid

    # 如果是从独立弹窗或间接启动，扫描系统中所有活动的 agy 实例
    for p, (_, name) in pids.items():
        if name in ('agy.exe', 'agy') and p != curr_pid:
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

    if not agy_pid:
        print(f"\n{C_GREEN}[✓] 凭据已即时写入系统 Windows 凭据管理器 (gemini:antigravity){C_RESET}")
        print(f"{C_GRAY}[i] 当前未检测到运行中的 agy 会话，下次启动 agy 时将自动以新账号登录。{C_RESET}\n")
        return True

    print(f"\n{C_CYAN}[↻] 正在为您无缝重新载入 Antigravity 会话并保留全部上下文...{C_RESET}")
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

    # 使用 PowerShell 进行毫秒级平滑重载：释放旧进程并秒级接续拉起新会话
    ps_script = f"""
    Start-Sleep -Milliseconds 500
    if ({agy_pid} -gt 0) {{
        Stop-Process -Id {agy_pid} -Force -ErrorAction SilentlyContinue
    }}
    Start-Sleep -Milliseconds 300
    $started = $false
    if (Get-Process -Name "WindowsTerminal" -ErrorAction SilentlyContinue) {{
        try {{
            Start-Process "wt.exe" -ArgumentList "-w 0 nt -d `"{cwd}`" `"{agy_exe}`" {arg_list}" -ErrorAction Stop
            $started = $true
        }} catch {{}}
    }}
    if (-not $started) {{
        Start-Process -FilePath "{agy_exe}" -WorkingDirectory "{cwd}" -ArgumentList "{arg_list}"
    }}
    """

    try:
        subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", ps_script])
        print(f"{C_GREEN}[✓] 重载已触发！新会话将完整保留所有对话历史并立即启用新账号！{C_RESET}\n")
        return True
    except Exception as e:
        print(f"{C_YELLOW}[-] 自动重新载入失败: {e}，请手动运行 agy -c。{C_RESET}\n")
        return False

def notify_cockpit_ws(email):
    """如果本地运行了 Cockpit-Tools 或 IDE 联动扩展 (ws://127.0.0.1:19528)，静默异步广播切号事件"""
    def _worker():
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.08)
            if s.connect_ex(('127.0.0.1', 19528)) != 0:
                s.close()
                return
            key = base64.b64encode(os.urandom(16)).decode('utf-8')
            handshake = (
                f"GET / HTTP/1.1\r\n"
                f"Host: 127.0.0.1:19528\r\n"
                f"Upgrade: websocket\r\n"
                f"Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                f"Sec-WebSocket-Version: 13\r\n\r\n"
            )
            s.sendall(handshake.encode('utf-8'))
            resp = s.recv(1024)
            if b"101 Switching Protocols" in resp:
                payload = json.dumps({
                    "type": "event.plugin_switch_account",
                    "target_email": email,
                    "switch_mode": "seamless",
                    "trigger_type": "manual",
                    "trigger_source": "zh.hot_switch",
                    "reason": "zh_cli_hot_switch"
                }).encode('utf-8')
                length = len(payload)
                mask = os.urandom(4)
                masked_payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
                if length <= 125:
                    header = bytes([0x81, 0x80 | length]) + mask
                elif length <= 65535:
                    header = bytes([0x81, 0x80 | 126, (length >> 8) & 0xff, length & 0xff]) + mask
                else:
                    header = bytes([0x81, 0x80 | 127]) + length.to_bytes(8, 'big') + mask
                s.sendall(header + masked_payload)
            s.close()
        except Exception:
            pass

    import threading
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

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
        notify_cockpit_ws(meta.get("email", ""))

        print(f"\n{C_GREEN}{C_BOLD}[✓] 账号已成功切换至: [{alias}] ({meta['email']}){C_RESET}")
        print(f"{C_GREEN}[✓] 凭据已即时写入系统 Windows 凭据管理器 (gemini:antigravity){C_RESET}")
        
        if auto_reload:
            cmd_reload()
        else:
            print(f"{C_YELLOW}[!] 提示: 已跳过自动重载。{C_RESET}")
            print(f"{C_GRAY}    当前运行中的 agy 内存保留了旧会话 Token，请随时输入 '!zh reload' 刷新生效。{C_RESET}")
            print(f"{C_GRAY}    或在会话中输入 '/exit' 后使用 'agy -c' 0秒保留历史接续。{C_RESET}\n")
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

    # 2. 临时清空当前凭证，触发 agy 登录
    print(f"\n{C_CYAN}[↻] 正在拉起 Antigravity 官方浏览器登录页面...{C_RESET}")
    advapi32.CredDeleteW("gemini:antigravity", 1, 0)

    agy_exe = os.path.expanduser(r"~\AppData\Local\agy\bin\agy.exe")
    if not os.path.exists(agy_exe):
        agy_exe = "agy"

    try:
        proc = subprocess.Popen([agy_exe, "--prompt", "hi"])
        proc.wait()
    except Exception as e:
        print(f"{C_YELLOW}[-] 启动登录失败: {e}{C_RESET}\n")
        if curr_blob:
            write_cred(curr_blob)
        return

    # 3. 读取新写入的凭证
    new_meta, new_blob = read_current_cred()
    if not new_blob or new_meta["email"] == "unknown":
        print(f"\n{C_YELLOW}[-] 未能获取新账号凭证，登录可能已取消。{C_RESET}\n")
        if curr_blob:
            write_cred(curr_blob)
            print(f"{C_GRAY}[*] 已安全恢复之前的登录状态。{C_RESET}\n")
        return

    # 4. 保存新凭证
    target_alias = alias if alias else generate_auto_alias(new_meta["email"])
    save_path = os.path.join(ACCOUNTS_DIR, f"{target_alias}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(new_blob)

    print(f"\n{C_GREEN}{C_BOLD}[✓] 新账号登录成功！{C_RESET}")
    print(f"{C_GREEN}[✓] 已存入账号库: [{target_alias}] -> {new_meta['email']}{C_RESET}\n")

def cmd_remove(target):
    accounts = get_saved_accounts()
    alias = target
    if target.isdigit():
        idx = int(target)
        if 1 <= idx <= len(accounts):
            alias = accounts[idx - 1][0]
        else:
            print(f"\n{C_YELLOW}[-] 序号 {target} 超出范围 (1 - {len(accounts)}){C_RESET}\n")
            return

    path = os.path.join(ACCOUNTS_DIR, f"{alias}.json")
    if not os.path.exists(path):
        print(f"\n{C_YELLOW}[-] 账号别名 [{alias}] 不存在。{C_RESET}\n")
        return

    os.remove(path)
    print(f"\n{C_GREEN}[✓] 成功删除账号: [{alias}]{C_RESET}\n")

def cmd_whoami():
    meta, blob = read_current_cred()
    if not meta or meta["email"] == "unknown":
        print(f"\n{C_YELLOW}[-] 当前未检测到活跃的 Antigravity 登录凭证。{C_RESET}\n")
        return

    print(f"\n{C_CYAN}─── 当前活跃账号状态 (WhoAmI) ───{C_RESET}")
    print(f"  邮箱 (Email):     {C_GREEN}{meta['email']}{C_RESET}")
    print(f"  姓名 (Name):      {meta['name'] or '未提供'}")
    print(f"  授权方式:         {meta['auth_method']}")
    print(f"  Token 过期时间:   {meta['expiry'] or '长期有效'}")

    accounts = get_saved_accounts()
    matched = [a for a, m in accounts if m["email"] == meta["email"]]
    if matched:
        print(f"  关联别名:         {C_BOLD}{matched[0]}{C_RESET}")
    else:
        print(f"  关联别名:         {C_YELLOW}(未保存到列表，可用 zh save <别名> 保存){C_RESET}")
    print()

def render_interactive_card_lines(accounts, current_email, options, selected):
    width = 66
    inner = width - 2
    lines = []
    lines.append(f"{C_CYAN}┌" + "─" * inner + f"┐{C_RESET}")

    title = " AGY 账号切换中心 (zh) "
    pad_t = (inner - str_disp_w(title)) // 2
    rem_t = inner - str_disp_w(title) - pad_t
    lines.append(f"{C_CYAN}│{C_RESET}" + " " * pad_t + f"{C_BOLD}{C_CYAN}{title}{C_RESET}" + " " * rem_t + f"{C_CYAN}│{C_RESET}")
    lines.append(f"{C_CYAN}├" + "─" * inner + f"┤{C_RESET}")

    cur_alias = "未关联别名"
    for a, m in accounts:
        if m["email"] == current_email:
            cur_alias = a
            break
    raw_active = f"  当前活跃: {current_email} [{cur_alias}]" if current_email else "  当前活跃: 未登录"
    styled_active = f"  当前活跃: {C_GREEN}{current_email}{C_RESET} [{C_BOLD}{cur_alias}{C_RESET}]" if current_email else f"  当前活跃: {C_YELLOW}未登录{C_RESET}"
    lines.append(make_card_line(styled_active, raw_active, width))
    lines.append(f"{C_CYAN}│" + " " * inner + f"│{C_RESET}")

    tip = "  账号列表 (↑/↓ 选择，Enter 立即切换生效，n 仅切凭据):"
    lines.append(make_card_line(f"{C_BOLD}{tip}{C_RESET}", tip, width))

    for idx, (kind, alias, meta) in enumerate(options):
        is_sel = (idx == selected)
        pfx = " ► " if is_sel else "   "
        if kind == "account":
            is_active = (meta["email"] == current_email)
            mark = "● [当前使用]" if is_active else "           "
            styled_mark = f"{C_GREEN}● [当前使用]{C_RESET}" if is_active else "           "
            
            padded_alias = pad_str(alias, 12, "left")
            padded_email = pad_str(meta['email'], 26, "left")
            
            raw_line = f" {pfx}[{idx+1}] {padded_alias} {padded_email} {mark}"
            if is_sel:
                styled_line = f" {C_YELLOW}{C_BOLD}{pfx}[{idx+1}] {padded_alias} {padded_email} {styled_mark}{C_RESET}"
            else:
                styled_line = f" {pfx}[{idx+1}] {padded_alias} {padded_email} {styled_mark}"
            lines.append(make_card_line(styled_line, raw_line, width))
        else:
            raw_line = f" {pfx}[+] 自动添加新账号 (唤起浏览器登录)"
            if is_sel:
                styled_line = f" {C_YELLOW}{C_BOLD}{pfx}[+] 自动添加新账号 (唤起浏览器登录){C_RESET}"
            else:
                styled_line = f" {pfx}{C_YELLOW}[+]{C_RESET} 自动添加新账号 (唤起浏览器登录)"
            lines.append(make_card_line(styled_line, raw_line, width))

    lines.append(f"{C_CYAN}│" + " " * inner + f"│{C_RESET}")
    foot = "  快捷键: [↑/↓] 移动   [Enter] 立即切换生效   [n] 仅切凭据   [q] 退出"
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
    while pid in pids and pid != 0:
        ppid, name = pids[pid]
        if 'agy' in name and pid != curr_pid:
            return True, pid
        pid = ppid
    return False, None

def flush_input_buffer():
    try:
        kernel32 = ctypes.windll.kernel32
        hIn = kernel32.CreateFileW('CONIN$', 0xC0000000, 3, None, 3, 0, 0)
        if hIn and hIn != -1:
            kernel32.FlushConsoleInputBuffer(hIn)
            kernel32.CloseHandle(hIn)
    except Exception:
        pass
    while msvcrt.kbhit():
        try:
            msvcrt.getwch()
        except Exception:
            break

def read_key():
    ch = msvcrt.getwch()
    if ch in ('\x00', '\xe0'):
        ext = msvcrt.getwch()
        if ext in ('H', 'K'): return 'up'
        if ext in ('P', 'M'): return 'down'
        return 'other'
    if ch == '\x1b':
        seq = ''
        for _ in range(25):
            if msvcrt.kbhit():
                break
            time.sleep(0.004)
        while msvcrt.kbhit():
            seq += msvcrt.getwch()
            time.sleep(0.002)
        if seq:
            if seq in ('[A', 'OA', '[D', 'OD'): return 'up'
            if seq in ('[B', 'OB', '[C', 'OC'): return 'down'
            if seq in ('[Z',): return 'up'
            return 'esc'
        return 'esc'
    if ch in ('\r', '\n', ' '):
        return 'enter'
    if ch in ('k', 'K', 'w', 'W'):
        return 'up'
    if ch in ('j', 'J', 's', 'S', '\t'):
        return 'down'
    if ch in ('r', 'R'):
        return 'enter'
    if ch in ('n', 'N'):
        return 'no_reload'
    if ch in ('q', 'Q'):
        return 'quit'
    if ch in ('+', 'a', 'A'):
        return 'add'
    if ch.isdigit():
        return ch
    return 'other'

def run_arrow_selector(accounts, is_popup=False):
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

    # Flush leftover keystrokes from typing the command
    time.sleep(0.05)
    flush_input_buffer()

    ready_time = time.time()
    user_has_navigated = False
    action = "reload"

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
                sys.stdout.flush()
            else:
                sys.stdout.write(f"\r\033[{total_lines}A")
                for l in card_lines:
                    sys.stdout.write(l + "\n")
                sys.stdout.flush()

            key = read_key()
            if key == 'up':
                user_has_navigated = True
                selected = (selected - 1) % len(options)
            elif key == 'down':
                user_has_navigated = True
                selected = (selected + 1) % len(options)
            elif key == 'enter':
                if not user_has_navigated and (time.time() - ready_time < 0.35):
                    continue
                action = "reload"
                break
            elif key == 'no_reload':
                action = "no_reload"
                break
            elif key in ('quit', 'esc'):
                selected = -1
                break
            elif key == 'add':
                selected = len(options) - 1
                action = "reload"
                break
            elif key.isdigit():
                num = int(key)
                if 1 <= num <= len(accounts):
                    selected = num - 1
                    action = "reload"
                    break

    except (KeyboardInterrupt, EOFError):
        selected = -1
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    if selected == -1:
        print(f"\n{C_GRAY}已退出账号切换。{C_RESET}\n")
        if is_popup:
            time.sleep(0.5)
        return

    kind, alias, meta = options[selected]
    if kind == "account":
        cmd_use(alias, auto_reload=(action == "reload"))
        if is_popup:
            print(f"\n{C_GREEN}[✓] 切换完成，窗口将在 1 秒后自动关闭...{C_RESET}")
            time.sleep(1.0)
    elif kind == "add":
        cmd_login(None)
        if is_popup:
            print(f"\n{C_GREEN}[✓] 登录流程结束，窗口将在 1 秒后自动关闭...{C_RESET}")
            time.sleep(1.0)

def run_gui_selector():
    import tkinter as tk

    accounts = get_saved_accounts()
    current_meta, _ = read_current_cred()
    current_email = current_meta["email"] if current_meta else ""

    root = tk.Tk()
    root.title("AGY 账号切换中心 (zh)")
    root.geometry("520x460")
    root.minsize(520, 460)
    root.configure(bg="#1e1e2e")
    root.attributes("-topmost", True)

    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = max(0, (sw - 520) // 2)
    y = max(0, (sh - 460) // 2)
    root.geometry(f"520x460+{x}+{y}")

    options = []
    for alias, meta in accounts:
        options.append(("account", alias, meta))
    options.append(("add", "自动添加新账号", None))

    init_idx = 0
    for i, (kind, alias, meta) in enumerate(options):
        if kind == "account" and meta["email"] == current_email:
            init_idx = i
            break

    # Header frame
    header = tk.Frame(root, bg="#181825", padx=20, pady=16)
    header.pack(fill=tk.X)

    title_lbl = tk.Label(header, text="AGY 账号切换中心 (zh)", font=("Segoe UI", 13, "bold"), fg="#89b4fa", bg="#181825")
    title_lbl.pack(anchor="w")

    cur_alias = "未关联别名"
    for a, m in accounts:
        if m["email"] == current_email:
            cur_alias = a
            break
    cur_text = f"当前活跃:  ● {current_email} [{cur_alias}]" if current_email else "当前活跃: 未登录"
    cur_lbl = tk.Label(header, text=cur_text, font=("Segoe UI", 10), fg="#a6e3a1", bg="#181825")
    cur_lbl.pack(anchor="w", pady=(4, 0))

    # List frame
    list_frame = tk.Frame(root, bg="#1e1e2e", padx=20, pady=12)
    list_frame.pack(fill=tk.BOTH, expand=True)

    list_hint = tk.Label(list_frame, text="支持方向键 [↑/↓] 移动，[Enter] 立即切换生效，双击直接切换：", font=("Segoe UI", 9), fg="#9399b2", bg="#1e1e2e")
    list_hint.pack(anchor="w", pady=(0, 6))

    listbox = tk.Listbox(
        list_frame,
        font=("Consolas", 11),
        bg="#181825",
        fg="#cdd6f4",
        selectbackground="#45475a",
        selectforeground="#ffffff",
        highlightthickness=1,
        highlightcolor="#89b4fa",
        highlightbackground="#313244",
        activestyle="none",
        relief=tk.FLAT,
        bd=4
    )
    listbox.pack(fill=tk.BOTH, expand=True)

    for idx, (kind, alias, meta) in enumerate(options):
        if kind == "account":
            is_active = (meta["email"] == current_email)
            mark = "● [当前使用]" if is_active else ""
            line = f" [{idx+1}] {alias:<14} {meta['email']:<26} {mark}"
            listbox.insert(tk.END, line)
        else:
            listbox.insert(tk.END, " [+] 自动添加新账号 (唤起浏览器登录)")

    listbox.selection_set(init_idx)
    listbox.activate(init_idx)
    listbox.focus_set()

    status_var = tk.StringVar(value="快捷键: [↑/↓] 选择   [Enter] 立即切换生效   [n] 仅切凭据   [Esc] 退出")
    status_lbl = tk.Label(root, textvariable=status_var, font=("Segoe UI", 9), fg="#a6adc8", bg="#181825", pady=8)
    status_lbl.pack(fill=tk.X, side=tk.BOTTOM)

    def do_switch(auto_reload=True):
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        kind, alias, meta = options[idx]
        if kind == "account":
            status_var.set(f"正在切换至 [{alias}] 并接续重载...")
            root.update()
            ok = cmd_use(alias, auto_reload=auto_reload)
            if ok:
                msg = f"✓ 成功切换至 [{alias}]！会话已平滑接续！" if auto_reload else f"✓ 成功切换至 [{alias}]！凭据已保存。"
                status_var.set(msg)
                status_lbl.config(fg="#a6e3a1")
                root.update()
                root.after(500, root.destroy)
            else:
                status_var.set("[-] 切换失败，请重试")
                status_lbl.config(fg="#f38ba8")
        elif kind == "add":
            root.destroy()
            cmd_login(None)

    btn_frame = tk.Frame(root, bg="#1e1e2e", padx=20, pady=8)
    btn_frame.pack(fill=tk.X)

    btn_switch = tk.Button(
        btn_frame, text="⚡ 切换并重载生效 (Enter)", font=("Segoe UI", 10, "bold"),
        bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
        relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
        command=lambda: do_switch(auto_reload=True)
    )
    btn_switch.pack(side=tk.LEFT, padx=(0, 10))

    btn_no_reload = tk.Button(
        btn_frame, text="📋 仅切凭据 (n)", font=("Segoe UI", 10),
        bg="#89b4fa", fg="#11111b", activebackground="#74c7ec",
        relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
        command=lambda: do_switch(auto_reload=False)
    )
    btn_no_reload.pack(side=tk.LEFT, padx=(0, 10))

    btn_cancel = tk.Button(
        btn_frame, text="✕ 取消 (Esc)", font=("Segoe UI", 10),
        bg="#313244", fg="#cdd6f4", activebackground="#45475a",
        relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
        command=root.destroy
    )
    btn_cancel.pack(side=tk.RIGHT)

    root.bind("<Return>", lambda e: do_switch(auto_reload=True))
    root.bind("<KP_Enter>", lambda e: do_switch(auto_reload=True))
    root.bind("<space>", lambda e: do_switch(auto_reload=True))
    root.bind("r", lambda e: do_switch(auto_reload=True))
    root.bind("R", lambda e: do_switch(auto_reload=True))
    root.bind("n", lambda e: do_switch(auto_reload=False))
    root.bind("N", lambda e: do_switch(auto_reload=False))
    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("q", lambda e: root.destroy())
    root.bind("Q", lambda e: root.destroy())
    listbox.bind("<Double-Button-1>", lambda e: do_switch(auto_reload=True))

    root.mainloop()

def run_ui_window():
    try:
        run_gui_selector()
    except Exception:
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("AGY 账号切换中心 (zh)")
        except Exception:
            pass
        accounts = get_saved_accounts()
        try:
            run_arrow_selector(accounts, is_popup=True)
        except Exception:
            import traceback
            traceback.print_exc()
            input("\n按 Enter 键关闭窗口...")

def cmd_ui_popup():
    script_path = os.path.abspath(__file__)
    print(f"\n{C_CYAN}[↻] 正在唤起交互选择窗口...{C_RESET}")
    try:
        py_exe = sys.executable
        pyw_exe = os.path.join(os.path.dirname(py_exe), "pythonw.exe")
        launcher = pyw_exe if os.path.exists(pyw_exe) else py_exe

        proc = subprocess.Popen(
            [launcher, script_path, "ui_window"],
            creationflags=subprocess.DETACHED_PROCESS if launcher == pyw_exe else subprocess.CREATE_NEW_CONSOLE
        )
        print(f"{C_GREEN}[✓] 交互窗口已打开！{C_RESET}")
        print(f"{C_GRAY}    在弹出的窗口中使用方向键 [↑/↓] 选择，[Enter] 确认切换并自动接续生效。{C_RESET}")
        print(f"{C_GRAY}    或者在此直接输入 '!zh <序号>' (如 !zh 1) 立即秒级切换。{C_RESET}\n")
    except Exception as e:
        print(f"{C_YELLOW}[-] 唤起窗口失败: {e}{C_RESET}")
        print(f"{C_GRAY}提示: 可直接输入 'zh 1' 或 'zh <别名>' 进行切换。{C_RESET}\n")

def interactive_mode():
    accounts = get_saved_accounts()

    if sys.stdin.isatty() and sys.stdout.isatty():
        run_arrow_selector(accounts, is_popup=False)
        return

    print_hud_card()
    cmd_ui_popup()

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
    elif arg1 in ("ui", "popup", "select", "窗口", "交互", "选号", "gui"):
        cmd_ui_popup()
    elif arg1 in ("ui_window", "selector"):
        run_ui_window()
    elif arg1 in ("console", "term", "终端"):
        accounts = get_saved_accounts()
        run_arrow_selector(accounts, is_popup=False)
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
        no_reload = any(x in sys.argv for x in ("--no-reload", "-n", "--不重载", "--仅凭据"))
        cmd_use(sys.argv[2], auto_reload=not no_reload)
    # Remove / Delete
    elif arg1 in ("rm", "remove", "del", "delete", "删除", "移除", "删") and len(sys.argv) >= 3:
        cmd_remove(sys.argv[2])
    else:
        no_reload = any(x in sys.argv for x in ("--no-reload", "-n", "--不重载", "--仅凭据"))
        if not cmd_use(sys.argv[1], auto_reload=not no_reload):
            print(f"{C_GRAY}提示: 输入 'zh 帮助' 或直接运行 'zh' 打开可视化面板。{C_RESET}\n")

if __name__ == "__main__":
    main()
