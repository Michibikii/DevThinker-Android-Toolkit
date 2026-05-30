import customtkinter as ctk
import os
import sys
import threading
import time
import traceback
from datetime import datetime

import utils
from utils import ToastNotification, run_adb

from core import AppState, frame_requires_device
from infrastructure.config import ConfigManager
from services import DeviceMonitorService
from ui.app_shell import build_shell, render_menu, show_frame, sync_connection_ui


def global_exception_handler(exc_type, exc_value, exc_traceback):
    try:
        utils.crash_log(f"FATAL CRASH: {exc_type.__name__}: {exc_value}")
        utils.crash_log("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    except Exception:
        pass


sys.excepthook = global_exception_handler
ctk.set_appearance_mode("Dark")


class DevThinkerApp(ctk.CTk):
    @property
    def current_device_id(self):
        return self.app_state.current_device_id

    @current_device_id.setter
    def current_device_id(self, value):
        self.app_state.current_device_id = value

    @property
    def current_tab(self):
        return self.app_state.current_tab

    @current_tab.setter
    def current_tab(self, value):
        self.app_state.current_tab = value

    @property
    def is_monitoring(self):
        return self.app_state.is_monitoring

    @is_monitoring.setter
    def is_monitoring(self, value):
        self.app_state.is_monitoring = value

    @property
    def adb_update_available(self):
        return self.app_state.adb_update_available

    @adb_update_available.setter
    def adb_update_available(self, value):
        self.app_state.adb_update_available = value

    @property
    def last_state(self):
        return self.app_state.last_state

    @last_state.setter
    def last_state(self, value):
        self.app_state.last_state = value

    @property
    def cached_dev_id(self):
        return self.app_state.cached_dev_id

    @cached_dev_id.setter
    def cached_dev_id(self, value):
        self.app_state.cached_dev_id = value

    @property
    def device_state(self):
        return self.app_state.device_state

    @device_state.setter
    def device_state(self, value):
        self.app_state.device_state = value

    @property
    def bat_counter(self):
        return self.app_state.bat_counter

    @bat_counter.setter
    def bat_counter(self, value):
        self.app_state.bat_counter = value

    @property
    def cached_full_name(self):
        return self.app_state.cached_full_name

    @cached_full_name.setter
    def cached_full_name(self, value):
        self.app_state.cached_full_name = value

    @property
    def cached_market_name(self):
        return self.app_state.cached_market_name

    @cached_market_name.setter
    def cached_market_name(self, value):
        self.app_state.cached_market_name = value

    @property
    def cached_ver(self):
        return self.app_state.cached_ver

    @cached_ver.setter
    def cached_ver(self, value):
        self.app_state.cached_ver = value

    @property
    def cached_api(self):
        return self.app_state.cached_api

    @cached_api.setter
    def cached_api(self, value):
        self.app_state.cached_api = value

    @property
    def cached_cpu(self):
        return self.app_state.cached_cpu

    @cached_cpu.setter
    def cached_cpu(self, value):
        self.app_state.cached_cpu = value

    @property
    def cached_battery(self):
        return self.app_state.cached_battery

    @cached_battery.setter
    def cached_battery(self, value):
        self.app_state.cached_battery = value

    def __init__(self):
        super().__init__()
        self.title("DevThinker - Android Toolkit")
        self.geometry("1200x800")
        self.configure(fg_color="#0B0F19")
        self.after(10, self.maximize_window)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.app_state = AppState()
        self.app_state.set_recent_tabs(ConfigManager.load_config().get("recent_tabs", []))
        self.current_tab = "welcome"

        build_shell(self)
        render_menu(self)
        self.show_frame("welcome")

        self.monitor_thread = threading.Thread(target=self.device_monitor_loop, daemon=True)
        self.monitor_thread.start()

    def report_callback_exception(self, exc, val, tb):
        global_exception_handler(exc, val, tb)
        try:
            self.show_toast("Error interno guardado en logs/crash.log", color="#EF4444")
        except Exception:
            pass

    def adb_cmd(self, command_list, timeout=15):
        if not self.current_device_id:
            try:
                self.show_toast("No hay dispositivo conectado", color="#EF4444")
            except Exception:
                pass
            return None
        return run_adb(["-s", self.current_device_id] + command_list, timeout=timeout)

    def maximize_window(self):
        try:
            self.state("zoomed")
        except Exception:
            pass

    def on_closing(self):
        self.is_monitoring = False
        if "live" in getattr(self, "frames", {}):
            self.frames["live"].stop()
        utils._kill_adb_process()
        self.destroy()
        sys.exit(0)

    def _frame_requires_device(self, name):
        return frame_requires_device(name)

    def _frame_is_enabled(self, name):
        return not self._frame_requires_device(name) or bool(self.current_device_id)

    def show_frame(self, name, record_recent=True):
        if not self._frame_is_enabled(name):
            return
        show_frame(self, name, record_recent=record_recent)

    def record_recent_tab(self, name):
        if not self.app_state.record_recent_tab(name):
            return

        ConfigManager.save_config("recent_tabs", self.app_state.recent_tabs)
        try:
            if "welcome" in getattr(self, "frames", {}):
                self.frames["welcome"].refresh_recent_options()
        except Exception:
            pass

    def disconnect_device(self):
        if not self.current_device_id:
            return
        try:
            utils.ui_log(f"disconnect_device called for {self.current_device_id}")
        except Exception:
            pass

        try:
            utils.ui_log("Showing toast: Desconectando...")
        except Exception:
            pass

        self.show_toast("Desconectando...", color="#F59E0B")
        utils.run_async(lambda: run_adb(["disconnect"]), lambda _res: None, self)
        self.current_device_id = None
        self.cached_dev_id = None
        self.device_state = {}
        self.thread_safe_update("🚫 Sin Dispositivo", "Esperando conexión...", "", "#181D2B", "#F8FAFC", False)
        render_menu(self)
        self.frames["tools"].refresh_feature_states()
        try:
            if "welcome" in getattr(self, "frames", {}):
                self.frames["welcome"].refresh_state()
        except Exception:
            pass
        self.show_frame("wireless", record_recent=False)

    def device_monitor_loop(self):
        while self.is_monitoring:
            snapshot = DeviceMonitorService.build_snapshot(
                self.adb_cmd,
                cached_state=getattr(self, "device_state", {}),
                bat_counter=getattr(self, "bat_counter", 5),
                adb_update_available=self.adb_update_available,
            )

            if snapshot.state == "adb_missing":
                self.current_device_id = None
                self.cached_dev_id = None
                self.device_state = {}
                self.thread_safe_update("⚠️ ADB no encontrado", snapshot.sub1, "", snapshot.bg_color, snapshot.title_color, False)
                time.sleep(3)
                continue

            if snapshot.state == "adb_error":
                self.current_device_id = None
                self.cached_dev_id = None
                self.device_state = {}
                self.thread_safe_update("⚠️ Error de ADB", snapshot.sub1, "", snapshot.bg_color, snapshot.title_color, False)
                time.sleep(3)
                continue

            if snapshot.state in {"unauthorized", "offline", "disconnected"}:
                self.current_device_id = None
                self.cached_dev_id = None
                self.device_state = {}
                self.thread_safe_update(snapshot.full_name, snapshot.sub1, snapshot.sub2, snapshot.bg_color, snapshot.title_color, False)
                time.sleep(2)
                continue

            if snapshot.is_connected and snapshot.device_id:
                self.current_device_id = snapshot.device_id
                try:
                    if "welcome" in getattr(self, "frames", {}):
                        self.frames["welcome"].refresh_state()
                except Exception:
                    pass
                self.cached_dev_id = snapshot.device_id
                self.cached_full_name = snapshot.full_name
                self.cached_market_name = snapshot.market_name
                self.cached_ver = snapshot.cached_ver
                self.cached_api = snapshot.cached_api
                self.cached_cpu = snapshot.cached_cpu
                self.cached_battery = snapshot.cached_battery
                self.device_state = {
                    "dev_id": snapshot.device_id,
                    "full_name": snapshot.full_name,
                    "market_name": snapshot.market_name,
                    "model": snapshot.market_name,
                    "ver": snapshot.cached_ver,
                    "api": snapshot.cached_api,
                    "cpu": snapshot.cached_cpu,
                    "battery": snapshot.cached_battery,
                }
                if snapshot.battery_refreshed:
                    self.bat_counter = 0
                else:
                    self.bat_counter = getattr(self, "bat_counter", 0) + 1

                self.thread_safe_update(snapshot.full_name, snapshot.sub1, snapshot.sub2, snapshot.bg_color, snapshot.title_color, True)

            time.sleep(3)

    def thread_safe_update(self, name, sub1, sub2, bg_color, title_color, is_conn):
        if self.is_monitoring:
            try:
                self.after(0, lambda: self._update_ui(name, sub1, sub2, bg_color, title_color, is_conn))
            except Exception:
                pass

    def _update_ui(self, name, sub1, sub2, bg_color, title_color, is_conn):
        try:
            try:
                utils.ui_log(f"_update_ui called: name={name!r}, sub1={sub1!r}, sub2={sub2!r}, is_conn={is_conn}")
            except Exception:
                pass

            try:
                utils.ui_log(f"_update_ui is_conn={is_conn} current_tab={self.current_tab!r} name={name!r}")
            except Exception:
                pass

            self.lbl_model.configure(text=name, text_color=title_color)
            self.lbl_sub1.configure(text=sub1)
            self.lbl_sub2.configure(text=sub2)
            self.info_card.configure(fg_color=bg_color)

            if is_conn and not self.last_state:
                self.last_state = True
                sync_connection_ui(self, True)
                if self.current_tab in {"wireless", "welcome"}:
                    self.show_frame("stats", record_recent=False)
            elif not is_conn and self.last_state:
                self.last_state = False
                sync_connection_ui(self, False)
                self.show_frame("wireless", record_recent=False)
        except Exception:
            pass

    def show_toast(self, msg, color="#10B981"):
        ToastNotification(self, msg, color)


if __name__ == "__main__":
    app = DevThinkerApp()
    app.mainloop()