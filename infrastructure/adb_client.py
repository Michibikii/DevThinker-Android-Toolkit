import io
import os
import platform
import shutil
import ssl
import subprocess
import time
import urllib.request
import zipfile

from .config import ConfigManager


def find_adb():
    data = ConfigManager.load_config()
    saved = data.get("adb_path")
    if saved and os.path.exists(saved):
        return saved

    adb_path = shutil.which("adb")
    if adb_path:
        return adb_path

    possible = [
        os.path.expanduser("~\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"),
        "C:\\Android\\platform-tools\\adb.exe",
        "/usr/local/bin/adb",
    ]
    for p in possible:
        if os.path.exists(p):
            return p
    return None


ADB_PATH = find_adb()


def refresh_adb_path():
    global ADB_PATH
    ADB_PATH = find_adb()
    return ADB_PATH


def get_adb_url_and_sys():
    system = platform.system().lower()
    if system == "windows":
        return "https://dl.google.com/android/repository/platform-tools-latest-windows.zip", "adb.exe"
    if system == "darwin":
        return "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip", "adb"
    return "https://dl.google.com/android/repository/platform-tools-latest-linux.zip", "adb"


def check_adb_update():
    if not ADB_PATH or not os.path.exists(ADB_PATH):
        return False, None
    url, _ = get_adb_url_and_sys()
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            remote_ver = response.headers.get("ETag") or response.headers.get("Last-Modified")
            local_ver = ConfigManager.load_config().get("adb_version")
            return (remote_ver != local_ver), remote_ver
    except:
        return False, None


def _kill_adb_process():
    try:
        if platform.system().lower() == "windows":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=si)
        else:
            subprocess.run(["killall", "adb"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass
    time.sleep(1)


def download_and_install_adb(target_dir=None, progress_callback=None):
    global ADB_PATH
    url, exe_name = get_adb_url_and_sys()
    if not target_dir:
        target_dir = os.path.join(os.path.expanduser("~"), ".devthinker")

    tools_dir = os.path.join(target_dir, "platform-tools")
    adb_path = os.path.join(tools_dir, exe_name)

    try:
        if progress_callback:
            progress_callback(0, 0, 0, "Preparando el sistema...")

        _kill_adb_process()

        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={"User-Agent": "DevThinker/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
            total_size = int(response.headers.get("content-length", 0))
            remote_ver = response.headers.get("ETag") or response.headers.get("Last-Modified")

            downloaded = 0
            chunk_size = 16384
            data = bytearray()
            start_time = time.time()
            last_update = 0

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                data.extend(chunk)
                downloaded += len(chunk)

                current_time = time.time()
                if progress_callback and (current_time - last_update > 0.1):
                    elapsed = current_time - start_time
                    speed = (downloaded / 1048576) / elapsed if elapsed > 0 else 0
                    progress_callback(downloaded, total_size, speed, "Descargando binarios...")
                    last_update = current_time

        if progress_callback:
            progress_callback(total_size, total_size, 0, "Extrayendo motor...")
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(target_dir)

        if platform.system().lower() != "windows":
            os.chmod(adb_path, 0o755)

        ConfigManager.save_config("adb_path", adb_path)
        if remote_ver:
            ConfigManager.save_config("adb_version", remote_ver)

        ADB_PATH = adb_path
        return True
    except:
        return False


def uninstall_adb():
    global ADB_PATH
    if not ADB_PATH or not os.path.exists(ADB_PATH):
        ADB_PATH = None
        return True
    try:
        _kill_adb_process()

        adb_dir = os.path.dirname(ADB_PATH)
        if os.path.basename(adb_dir) == "platform-tools" and os.path.exists(adb_dir):
            shutil.rmtree(adb_dir, ignore_errors=True)

        ConfigManager.save_config("adb_path", None)
        ConfigManager.save_config("adb_version", None)
        ADB_PATH = None
        return True
    except:
        return False


def set_manual_adb_path():
    from tkinter import filedialog

    global ADB_PATH
    path = filedialog.askopenfilename(title="Seleccionar ADB", filetypes=[("exe", "*.exe"), ("all", "*.*")])
    if path and os.path.exists(path):
        ConfigManager.save_config("adb_path", path)
        ADB_PATH = path
        return True
    return False


def run_adb(args, timeout=15, encoding="utf-8"):
    if not ADB_PATH or not os.path.exists(ADB_PATH):
        return None
    try:
        cmd = [ADB_PATH] + args
        si = None
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=si, encoding=encoding, errors="replace")
        stdout = (res.stdout or "").strip()
        stderr = (res.stderr or "").strip()
        if stdout:
            return stdout
        if stderr:
            return stderr
        return ""
    except:
        return None
