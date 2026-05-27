import io
import random
import re
import time

from PIL import Image

try:
    import qrcode
except Exception:
    qrcode = None

import utils


class WirelessService:
    def __init__(self, adb_cmd):
        self.adb_cmd = adb_cmd

    @staticmethod
    def build_qr_payload():
        qr_pass = str(random.randint(100000, 999999))
        qr_name = f"DevThinker-{random.randint(100, 999)}"
        qr_data = f"WIFI:T:ADB;S:{qr_name};P:{qr_pass};;"
        return {
            "qr_pass": qr_pass,
            "qr_name": qr_name,
            "qr_data": qr_data,
        }

    @staticmethod
    def fetch_qr_image(qr_data):
        if qrcode is None:
            raise RuntimeError("qrcode no instalado")

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        return image

    def wait_for_connection_port(self, target_ip, timeout=12):
        start_time = time.time()
        while time.time() - start_time < timeout:
            out = self.adb_cmd(["mdns", "services"])
            if out:
                for line in out.splitlines():
                    if "_adb-tls-connect" in line and target_ip in line:
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+:\d+)", line)
                        if match:
                            return match.group(1)
            time.sleep(1.5)
        return None

    def find_pairing_port(self, qr_name):
        out = self.adb_cmd(["mdns", "services"])
        if not out:
            return None

        for line in out.splitlines():
            if qr_name in line and "_adb-tls-pairing" in line:
                match = re.search(r"(\d+\.\d+\.\d+\.\d+:\d+)", line)
                if match:
                    return match.group(1)
        return None

    def pair_with_qr(self, pair_port, qr_pass):
        return self.adb_cmd(["pair", pair_port, qr_pass])

    def connect(self, connect_port):
        return self.adb_cmd(["connect", connect_port])

    def scan_usb(self):
        out = self.adb_cmd(["devices"])
        if out and out.count("\n") > 1:
            return out

        self.adb_cmd(["kill-server"])
        self.adb_cmd(["start-server"])
        return self.adb_cmd(["devices"])

    @staticmethod
    def parse_usb_state(adb_output):
        if not adb_output:
            return "missing"

        state = "missing"
        for line in adb_output.strip().splitlines():
            if "List" in line or not line.strip():
                continue
            if "unauthorized" in line:
                return "unauthorized"
            if "offline" in line:
                return "offline"
            if "device" in line:
                state = "connected"
                break
        return state
