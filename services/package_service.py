class PackageService:
    def __init__(self, adb_cmd):
        self.adb_cmd = adb_cmd

    def list_third_party_packages(self):
        out = self.adb_cmd(["shell", "pm", "list", "packages", "-3"])
        return [line.replace("package:", "").strip() for line in out.splitlines() if line] if out else []

    @staticmethod
    def extract_app_name(pkg):
        parts = pkg.split(".")
        ignore = {"com", "org", "net", "android", "google", "apps", "mobile", "app"}
        filtered = [part for part in parts if part.lower() not in ignore]
        return (filtered[-1] if filtered else parts[-1]).capitalize()

    def install_apk(self, apk_path):
        return self.adb_cmd(["install", "-r", apk_path], timeout=None)

    def launch_app(self, pkg):
        return self.adb_cmd(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])

    def force_stop(self, pkg):
        return self.adb_cmd(["shell", "am", "force-stop", pkg])

    def clear_data(self, pkg):
        return self.adb_cmd(["shell", "pm", "clear", pkg])

    def uninstall(self, pkg):
        return self.adb_cmd(["uninstall", pkg])