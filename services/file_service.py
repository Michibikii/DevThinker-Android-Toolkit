from dataclasses import dataclass
import os
import posixpath
import tempfile
import uuid


@dataclass(frozen=True)
class FileEntry:
    name: str
    is_dir: bool


class FileExplorerService:
    def __init__(self, adb_cmd):
        self.adb_cmd = adb_cmd

    @staticmethod
    def normalize_path(path):
        if not path:
            return "/sdcard/"
        normalized = path.replace("//", "/")
        if normalized != "/" and not normalized.endswith("/"):
            normalized += "/"
        return normalized

    @staticmethod
    def parse_listing(adb_output):
        entries = []
        if not adb_output:
            return entries

        for raw_line in adb_output.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("total"):
                continue
            if line.startswith(("Permission denied", "No such file or directory", "cannot access")):
                continue

            if line.startswith(("-", "d", "l")) and len(line.split()) > 1:
                name = line.split()[-1].rstrip("/")
                is_dir = line.endswith("/")
            else:
                is_dir = line.endswith("/")
                name = line.rstrip("/")

            if name:
                entries.append(FileEntry(name=name, is_dir=is_dir))
        return entries

    @staticmethod
    def has_listing_error(adb_output):
        if not adb_output:
            return False
        return any(msg in adb_output for msg in ["Permission denied", "No such file or directory", "cannot access"])

    @staticmethod
    def is_image_file(filename):
        return os.path.splitext(filename)[1].lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

    @staticmethod
    def is_text_file(filename):
        return os.path.splitext(filename)[1].lower() in {".txt", ".xml", ".json", ".log", ".ini", ".prop", ".csv", ".html", ".md", ".py"}

    @staticmethod
    def can_go_up(path):
        normalized = FileExplorerService.normalize_path(path)
        return normalized not in ["/", "/sdcard/"]

    def list_directory(self, path):
        return self.adb_cmd(["shell", "ls", "-1pA", path])

    def delete_entry(self, current_path, entry_name):
        target = posixpath.join(current_path, entry_name)
        return self.adb_cmd(["shell", "rm", "-rf", target])

    def copy_entry(self, current_path, entry_name, destination_path):
        source = posixpath.join(current_path, entry_name)
        return self.adb_cmd(["shell", "cp", "-r", source, destination_path], timeout=None)

    def move_entry(self, current_path, entry_name, destination_path):
        source = posixpath.join(current_path, entry_name)
        return self.adb_cmd(["shell", "mv", source, destination_path], timeout=None)

    def rename_entry(self, current_path, entry_name, new_name):
        source = posixpath.join(current_path, entry_name)
        target = posixpath.join(current_path, new_name)
        return self.adb_cmd(["shell", "mv", source, target], timeout=None)

    def create_directory(self, current_path, folder_name):
        target = posixpath.join(current_path, folder_name)
        return self.adb_cmd(["shell", "mkdir", "-p", target], timeout=None)

    def pull_file(self, remote_path, local_path):
        return self.adb_cmd(["pull", remote_path, local_path], timeout=None)

    def push_file(self, local_path, remote_path):
        return self.adb_cmd(["push", local_path, remote_path], timeout=None)

    def enter_folder_path(self, current_path, folder_name):
        return self.normalize_path(posixpath.join(current_path, folder_name))

    def go_up_path(self, current_path):
        normalized = self.normalize_path(current_path)
        if normalized in ["/", "/sdcard/"]:
            return normalized

        parent = posixpath.dirname(normalized.rstrip("/")) + "/"
        if parent == "//":
            parent = "/"
        return parent

    def read_text_file(self, remote_path):
        return self.adb_cmd(["shell", "cat", remote_path])

    def pull_temp_file(self, remote_path, ext=".tmp"):
        temp_dir = tempfile.gettempdir()
        temp_name = f"devthinker_{uuid.uuid4().hex}{ext}"
        local_path = os.path.join(temp_dir, temp_name)
        res = self.pull_file(remote_path, local_path)
        if res is not None and "error" not in str(res).lower() and os.path.exists(local_path):
            return local_path
        return None
