import os
import subprocess

import utils


class LiveLogService:
    @staticmethod
    def adb_ready():
        return bool(utils.ADB_PATH) and os.path.exists(utils.ADB_PATH)

    @staticmethod
    def build_logcat_command(device_id):
        return [utils.ADB_PATH, "-s", device_id, "logcat", "-v", "time"]

    @staticmethod
    def should_keep_line(line, errors_only=False, filter_text=""):
        is_error_or_warn = (" E/" in line or "FATAL" in line or " W/" in line)
        if errors_only and not is_error_or_warn:
            return False, None

        if filter_text and filter_text.lower() not in line.lower():
            return False, None

        tag = "error" if (" E/" in line or "FATAL" in line) else "warn" if " W/" in line else "normal"
        return True, tag

    @staticmethod
    def start_logcat_process(cmd):
        si = None
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, startupinfo=si, encoding="utf-8", errors="replace")

    @staticmethod
    def clear_logcat(device_id):
        return utils.run_adb(["-s", device_id, "logcat", "-c"])