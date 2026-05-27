from dataclasses import dataclass
import os
import re

import infrastructure.adb_client as adb_client
import utils


@dataclass(frozen=True)
class DeviceSnapshot:
    state: str
    device_id: str | None = None
    full_name: str = "🚫 Sin Dispositivo"
    sub1: str = "Esperando conexión..."
    sub2: str = ""
    bg_color: str = "#181D2B"
    title_color: str = "#F8FAFC"
    is_connected: bool = False
    market_name: str = ""
    cached_ver: str = "?"
    cached_api: str = "?"
    cached_cpu: str = "?"
    cached_battery: str = "?"
    adb_update_available: bool = False
    device_changed: bool = False
    battery_refreshed: bool = False


@dataclass(frozen=True)
class DeviceStatsSnapshot:
    total_ram: float = 0
    avail_ram: float = 0
    sto_pct: int = 0
    sto_used: str = "0"
    sto_total: str = "0"
    cpu_text: str = "No se pudo obtener información de la CPU."


class DeviceMonitorService:
    @staticmethod
    def adb_ready() -> bool:
        ready = bool(adb_client.ADB_PATH) and os.path.exists(adb_client.ADB_PATH)
        try:
            utils.device_log(f"adb_ready -> {ready} (ADB_PATH={adb_client.ADB_PATH})")
        except Exception:
            pass
        return ready

    @staticmethod
    def parse_device_line(line):
        if "unauthorized" in line:
            return "unauthorized", None
        if "offline" in line:
            return "offline", None
        if "device" in line:
            return "device", line.split()[0]
        return None, None

    @staticmethod
    def parse_props(props_raw):
        props = dict(re.findall(r'\[(.*?)\]:\s*\[(.*?)\]', props_raw or ""))
        brand = props.get("ro.product.brand", "Desconocido").capitalize()
        model = props.get("ro.product.model", "Dispositivo")
        ver = props.get("ro.build.version.release", "?")
        api = props.get("ro.build.version.sdk", "?")
        cpu = props.get("ro.product.cpu.abi", "?")
        market_name = props.get("ro.product.marketname", "") or props.get("ro.product.vendor.marketname", "")
        if not market_name:
            market_name = model
        full_name = f"📱 {brand} {model}" if brand != "Desconocido" else f"📱 {model}"
        return {
            "brand": brand,
            "model": model,
            "ver": ver,
            "api": api,
            "cpu": cpu,
            "market_name": market_name,
            "full_name": full_name,
        }

    @staticmethod
    def parse_battery(raw):
        if not raw:
            return "?"
        for line in raw.splitlines():
            if "level:" in line:
                return line.split(":", 1)[1].strip() + "%"
        return "?"

    @classmethod
    def build_system_stats(cls, device_id):
        if not device_id:
            return DeviceStatsSnapshot()

        total_ram, avail_ram = 0, 0
        ram_out = adb_client.run_adb(["-s", device_id, "shell", "cat", "/proc/meminfo"])
        if ram_out:
            m_total = re.search(r"MemTotal:\s+(\d+)", ram_out)
            m_avail = re.search(r"MemAvailable:\s+(\d+)", ram_out)
            if m_total and m_avail:
                total_ram = int(m_total.group(1)) / 1024
                avail_ram = int(m_avail.group(1)) / 1024

        sto_pct, sto_used, sto_total = 0, "0", "0"
        sto_out = adb_client.run_adb(["-s", device_id, "shell", "df", "/data"])
        if sto_out:
            lines = sto_out.split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    sto_total_raw = parts[1]
                    sto_used_raw = parts[2]
                    pct_str = parts[4].replace("%", "")
                    if pct_str.isdigit():
                        sto_pct = int(pct_str)
                        sto_total = f"{int(sto_total_raw) / 1048576:.1f} GB"
                        sto_used = f"{int(sto_used_raw) / 1048576:.1f} GB"

        cpu_text = "No se pudo obtener información de la CPU."
        cpu_out = adb_client.run_adb(["-s", device_id, "shell", "top", "-n", "1", "-b", "-m", "15"])
        if cpu_out:
            cpu_text = cpu_out

        return DeviceStatsSnapshot(
            total_ram=total_ram,
            avail_ram=avail_ram,
            sto_pct=sto_pct,
            sto_used=sto_used,
            sto_total=sto_total,
            cpu_text=cpu_text,
        )

    @classmethod
    def build_snapshot(cls, adb_cmd, cached_state=None, bat_counter=5, adb_update_available=False):
        cached_state = cached_state or {}
        cached_dev_id = cached_state.get("dev_id")
        cached_full_name = cached_state.get("full_name") or "🚫 Sin Dispositivo"
        cached_market_name = cached_state.get("market_name", "")
        cached_ver = cached_state.get("ver", "?")
        cached_api = cached_state.get("api", "?")
        cached_cpu = cached_state.get("cpu", "?")
        cached_battery = cached_state.get("battery", "?")

        if not cls.adb_ready():
            return DeviceSnapshot(
                state="adb_missing",
                bg_color="#3F1D1D",
                title_color="#EF4444",
                sub1="Vaya a Utilidades e instálelo\npara continuar.",
                is_connected=False,
            )

        out = adb_client.run_adb(["devices"])
        try:
            utils.device_log(f"adb devices output raw: {repr(out)}")
        except Exception:
            pass
        if out is None:
            return DeviceSnapshot(
                state="adb_error",
                bg_color="#3F1D1D",
                title_color="#EF4444",
                sub1="El motor falló o está corrupto.\nReinstálelo desde Utilidades.",
                is_connected=False,
            )

        lines = out.strip().split("\n")
        found_line = None
        for line in lines:
            if "List of devices" in line or not line.strip():
                continue
            kind, dev_id = cls.parse_device_line(line)
            try:
                utils.device_log(f"parse_device_line -> line={line!r}, kind={kind}, dev_id={dev_id}")
            except Exception:
                pass
            if kind == "unauthorized":
                return DeviceSnapshot(
                    state="unauthorized",
                    bg_color="#422C10",
                    title_color="#F59E0B",
                    sub1="Acepta el aviso en la\npantalla del celular.",
                    is_connected=False,
                )
            if kind == "offline":
                return DeviceSnapshot(
                    state="offline",
                    bg_color="#3F1D1D",
                    title_color="#EF4444",
                    sub1="Reinicia la conexión USB\no el Wi-Fi.",
                    is_connected=False,
                )
            if kind == "device" and dev_id:
                found_line = dev_id
                break

        if not found_line:
            return DeviceSnapshot(state="disconnected", is_connected=False)

        dev_id = found_line
        device_changed = dev_id != cached_dev_id
        try:
            utils.device_log(f"device found -> dev_id={dev_id}, cached_dev_id={cached_dev_id}, device_changed={device_changed}")
        except Exception:
            pass

        parsed = None
        if device_changed:
            try:
                props_raw = adb_client.run_adb(["-s", dev_id, "shell", "getprop"])
            except Exception:
                props_raw = None
            try:
                utils.device_log(f"getprop raw length: {len(props_raw) if props_raw else 0}")
            except Exception:
                pass
            parsed = cls.parse_props(props_raw) if props_raw else None

        if parsed is None:
            parsed = {
                "brand": "Desconocido",
                "model": cached_state.get("model", "Dispositivo"),
                "ver": cached_ver,
                "api": cached_api,
                "cpu": cached_cpu,
                "market_name": cached_market_name or cached_state.get("model", "Dispositivo"),
                "full_name": cached_full_name if cached_full_name and cached_full_name != "🚫 Sin Dispositivo" else "📱 Dispositivo",
            }

        battery_refreshed = device_changed or bat_counter >= 5
        battery = cached_battery
        if battery_refreshed:
            try:
                batt_raw = adb_client.run_adb(["-s", dev_id, "shell", "dumpsys", "battery"])
            except Exception:
                batt_raw = None
            try:
                utils.device_log(f"dumpsys battery raw: {repr(batt_raw)[:400]}")
            except Exception:
                pass
            battery = cls.parse_battery(batt_raw)

        online_info = f"✅ Modelo: {parsed['market_name']}"
        if adb_update_available:
            online_info += "\n🔔 ¡Actualización de ADB\nrecomendada en Utilidades!"

        try:
            utils.device_log(f"Returning DeviceSnapshot connected dev_id={dev_id} full_name={parsed.get('full_name') if parsed else None} battery={battery}")
        except Exception:
            pass

        return DeviceSnapshot(
            state="connected",
            device_id=dev_id,
            full_name=parsed["full_name"],
            sub1=f"🤖 Android {parsed['ver']}   |   🔋 {battery}",
            sub2=f"⚙️ API {parsed['api']} • {parsed['cpu']}\n{online_info}",
            bg_color="#132E25",
            title_color="#10B981",
            is_connected=True,
            market_name=parsed["market_name"],
            cached_ver=parsed["ver"],
            cached_api=parsed["api"],
            cached_cpu=parsed["cpu"],
            cached_battery=battery,
            adb_update_available=adb_update_available,
            device_changed=device_changed,
            battery_refreshed=battery_refreshed,
        )
