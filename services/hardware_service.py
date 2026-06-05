from dataclasses import dataclass
import re
import infrastructure.adb_client as adb_client

@dataclass
class HardwareInfoSnapshot:
    # Battery
    battery_level: str = "Desconocido"
    battery_health: str = "Desconocido"
    battery_status: str = "Desconocido"
    battery_temp: str = "Desconocido"
    battery_voltage: str = "Desconocido"
    
    # Display
    screen_resolution: str = "Desconocido"
    screen_density: str = "Desconocido"
    
    # System & Hardware
    manufacturer: str = "Desconocido"
    model: str = "Desconocido"
    android_version: str = "Desconocido"
    cpu_platform: str = "Desconocido"
    
    # Sensors
    sensors_list: str = "No se pudieron obtener los sensores."

class HardwareService:
    @staticmethod
    def get_hardware_info(device_id: str) -> HardwareInfoSnapshot:
        if not device_id:
            return HardwareInfoSnapshot()
            
        info = HardwareInfoSnapshot()
        
        # 1. Fetch Battery Info
        batt_raw = adb_client.run_adb(["-s", device_id, "shell", "dumpsys", "battery"])
        if batt_raw:
            for line in batt_raw.splitlines():
                line = line.strip()
                if line.startswith("level:"):
                    info.battery_level = line.split(":")[1].strip() + "%"
                elif line.startswith("health:"):
                    h_val = line.split(":")[1].strip()
                    health_map = {"1": "Desconocido", "2": "Buena", "3": "Sobrecalentamiento", "4": "Muerta", "5": "Sobretensión", "6": "Fallo no especificado", "7": "Fría"}
                    info.battery_health = health_map.get(h_val, f"Código {h_val}")
                elif line.startswith("status:"):
                    s_val = line.split(":")[1].strip()
                    status_map = {"1": "Desconocido", "2": "Cargando", "3": "Descargando", "4": "No cargando", "5": "Llena"}
                    info.battery_status = status_map.get(s_val, f"Código {s_val}")
                elif line.startswith("temperature:"):
                    temp_val = int(line.split(":")[1].strip())
                    info.battery_temp = f"{temp_val / 10.0:.1f} °C"
                elif line.startswith("voltage:"):
                    volt_val = int(line.split(":")[1].strip())
                    info.battery_voltage = f"{volt_val / 1000.0:.2f} V"

        # 2. Fetch Display Info
        size_raw = adb_client.run_adb(["-s", device_id, "shell", "wm", "size"])
        if size_raw and "Physical size:" in size_raw:
            info.screen_resolution = size_raw.split("Physical size:")[1].strip()
            
        density_raw = adb_client.run_adb(["-s", device_id, "shell", "wm", "density"])
        if density_raw and "Physical density:" in density_raw:
            info.screen_density = density_raw.split("Physical density:")[1].strip() + " dpi"

        # 3. Fetch System & Hardware (getprop)
        props_raw = adb_client.run_adb(["-s", device_id, "shell", "getprop"])
        if props_raw:
            props = dict(re.findall(r'\[(.*?)\]:\s*\[(.*?)\]', props_raw))
            info.manufacturer = props.get("ro.product.manufacturer", "Desconocido").capitalize()
            info.model = props.get("ro.product.model", "Desconocido")
            info.android_version = props.get("ro.build.version.release", "Desconocido")
            info.cpu_platform = props.get("ro.board.platform", props.get("ro.product.board", "Desconocido"))

        # 4. Fetch Sensors Info
        sensors_raw = adb_client.run_adb(["-s", device_id, "shell", "dumpsys", "sensorservice"])
        if sensors_raw:
            sensor_lines = []
            capture = False
            for line in sensors_raw.splitlines():
                if "Sensor List:" in line:
                    capture = True
                    continue
                if capture:
                    if line.strip() == "" or "Connections:" in line or "Total Sensors:" in line:
                        break
                    # Typical line: "0x00000001) LSM6DS3 Accelerometer | STMicroelectronics | ver: 1 | type: android.sensor.accelerometer(1) | perm: n/a | flags: 0x00000000"
                    parts = line.split(')')
                    if len(parts) > 1:
                        name_part = parts[1].split('|')[0].strip()
                        sensor_lines.append(f"• {name_part}")
            
            if sensor_lines:
                info.sensors_list = "\n".join(sensor_lines)
            else:
                info.sensors_list = "No se detectaron sensores o no se pudo parsear la lista."

        return info
