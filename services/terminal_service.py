import os
import shlex

import utils


class TerminalService:
    GLOBAL_COMMANDS = {
        "connect",
        "devices",
        "disconnect",
        "help",
        "kill-server",
        "mdns",
        "pair",
        "start-server",
        "tcpip",
        "usb",
        "version",
        "wait-for-device",
    }

    @staticmethod
    def normalize_command(raw_cmd):
        cmd = (raw_cmd or "").strip()
        if cmd == "adb":
            return ""
        if cmd.startswith("adb "):
            cmd = cmd[4:].strip()
        return cmd

    @classmethod
    def execute(cls, raw_cmd, device_id=None):
        normalized = cls.normalize_command(raw_cmd)
        if not normalized:
            return {"command": "", "output": None, "error": "Ingresa un comando primero."}

        try:
            cmd_args = shlex.split(normalized)
        except Exception as exc:
            return {"command": normalized, "output": None, "error": f"Error de sintaxis en el comando: {exc}"}

        if not utils.ADB_PATH or not os.path.exists(utils.ADB_PATH):
            return {"command": normalized, "output": None, "error": "Error: No se encontró ADB en el sistema."}

        cmd_name = cmd_args[0].lower()
        needs_device = cmd_name not in cls.GLOBAL_COMMANDS
        if needs_device and not device_id:
            return {
                "command": normalized,
                "output": None,
                "error": "Error: Ningún dispositivo conectado o autorizado.",
            }

        utils.adb_log(f"terminal execute -> device_id={device_id!r} command={normalized!r}")
        if needs_device:
            output = utils.run_adb(["-s", device_id] + cmd_args, timeout=None)
        else:
            output = utils.run_adb(cmd_args, timeout=None)

        if output is None:
            return {
                "command": normalized,
                "output": None,
                "error": "Error interno: Falló la ejecución del comando o excedió el tiempo límite.",
            }

        return {"command": normalized, "output": output, "error": None}