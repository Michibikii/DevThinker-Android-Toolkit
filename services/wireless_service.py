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
import infrastructure.adb_client as adb_client


class WirelessService:
    def __init__(self, adb_cmd):
        self.adb_cmd = adb_cmd

    def _run_adb(self, args, timeout=15):
        out = adb_client.run_adb(args, timeout=timeout)
        try:
            utils.adb_log(f"wireless adb {' '.join(args)} -> {repr(out)}")
        except Exception:
            pass
        return out

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
            out = self._run_adb(["mdns", "services"])
            if out:
                for line in out.splitlines():
                    if "_adb-tls-connect" in line and target_ip in line:
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+:\d+)", line)
                        if match:
                            return match.group(1)
            time.sleep(1.5)
        return None

    def find_pairing_port(self, qr_name):
        out = self._run_adb(["mdns", "services"])
        if not out:
            return None

        for line in out.splitlines():
            if qr_name in line and "_adb-tls-pairing" in line:
                match = re.search(r"(\d+\.\d+\.\d+\.\d+:\d+)", line)
                if match:
                    return match.group(1)
        return None

    def pair_with_qr(self, pair_port, qr_pass):
        return self._run_adb(["pair", pair_port, qr_pass])

    def connect(self, connect_port):
        return self._run_adb(["connect", connect_port])

    def scan_usb(self):
        out = self._run_adb(["devices"])
        if out and out.count("\n") > 1:
            return out

        self._run_adb(["kill-server"])
        self._run_adb(["start-server"])
        return self._run_adb(["devices"])

    def mdns_check(self):
        return self._run_adb(["mdns", "check"])

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
