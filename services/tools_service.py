import os
import shutil
import subprocess

import utils


class ToolsService:
    @staticmethod
    def adb_ready():
        return bool(utils.ADB_PATH) and os.path.exists(utils.ADB_PATH)

    @staticmethod
    def restart_adb():
        utils.adb_log("restart_adb requested")
        utils.run_adb(["kill-server"])
        return utils.run_adb(["start-server"])

    @staticmethod
    def uninstall_adb():
        utils.adb_log("uninstall_adb requested")
        return utils.uninstall_adb()

    @staticmethod
    def download_and_install_adb(target_dir=None, progress_callback=None):
        utils.adb_log(f"download_and_install_adb requested target_dir={target_dir!r}")
        return utils.download_and_install_adb(target_dir, progress_callback)

    @staticmethod
    def screenshot(device_id):
        return utils.run_adb(["-s", device_id, "shell", "screencap", "-p", "/sdcard/s.png"])

    @staticmethod
    def pull_screenshot(device_id, local_path):
        return utils.run_adb(["-s", device_id, "pull", "/sdcard/s.png", local_path])

    @staticmethod
    def reboot(device_id):
        return utils.run_adb(["-s", device_id, "reboot"])

    @staticmethod
    def input_text(device_id, text):
        safe_txt = text.replace(" ", "%s").replace('"', '\\"')
        return utils.run_adb(["-s", device_id, "shell", "input", "text", f'"{safe_txt}"'])

    @staticmethod
    def toggle_show_touches(device_id):
        current = utils.run_adb(["-s", device_id, "shell", "settings", "get", "system", "show_touches"])
        value = "0" if current and "1" in current else "1"
        result = utils.run_adb(["-s", device_id, "shell", "settings", "put", "system", "show_touches", value])
        return value, result

    @staticmethod
    def open_url(device_id, url):
        if not url.startswith("http"):
            url = "https://" + url
        return utils.run_adb([
            "-s",
            device_id,
            "shell",
            "am",
            "start",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            f'"{url}"',
        ])

    @staticmethod
    def build_scrcpy_command(device_id, turn_screen_off=False, stay_awake=True, no_audio=False, max_fps=False):
        cmd = ["scrcpy", "-s", device_id]
        if turn_screen_off:
            cmd.append("--turn-screen-off")
        if stay_awake:
            cmd.append("--stay-awake")
        if no_audio:
            cmd.append("--no-audio")
        if max_fps:
            cmd.extend(["--max-fps", "30"])
        return cmd

    @staticmethod
    def launch_scrcpy(cmd):
        try:
            return subprocess.Popen(cmd)
        except Exception as exc:
            utils.adb_log(f"launch_scrcpy failed: {exc!r}")
            return None