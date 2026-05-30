import customtkinter as ctk
import posixpath
from tkinter import filedialog
import utils
from utils import AskString, ToolTip, requires_device, run_async
from services import FileExplorerService, FileEntry


class RemoteFolderPicker(ctk.CTkToplevel):
    def __init__(self, parent, service, start_path, title="Elegir destino"):
        super().__init__(parent)
        self.app = parent
        self.service = service
        self.result = None
        self.current_path = self.service.normalize_path(start_path)
        self.title(title)
        self.attributes("-topmost", True)
        self.transient(parent)
        self.geometry("620x520")
        self.minsize(560, 460)

        ctk.CTkLabel(self, text=title, font=("Segoe UI", 18, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(self, text="Navega y elige la carpeta de destino.", font=("Segoe UI", 12), text_color="#94A3B8").pack(anchor="w", padx=20, pady=(0, 12))

        top = ctk.CTkFrame(self, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        top.pack(fill="x", padx=20, pady=(0, 12))

        self.btn_up = ctk.CTkButton(top, text="⬆ Volver", width=90, height=36, font=("Segoe UI", 12, "bold"), fg_color="#475569", hover_color="#334155", command=self.go_up)
        self.btn_up.pack(side="left", padx=12, pady=12)

        self.entry_path = ctk.CTkEntry(top, font=("Consolas", 12), height=36, fg_color="#0B0F19", border_color="#252D40", text_color="#E2E8F0")
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=12)
        self.entry_path.insert(0, self.current_path)
        self.entry_path.bind("<Return>", lambda _e: self.load_path())

        self.btn_use = ctk.CTkButton(top, text="Usar carpeta", width=120, height=36, font=("Segoe UI", 12, "bold"), fg_color="#10B981", hover_color="#059669", command=self.accept)
        self.btn_use.pack(side="right", padx=(0, 12), pady=12)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkButton(bottom, text="Cancelar", width=120, height=38, font=("Segoe UI", 12, "bold"), fg_color="#475569", hover_color="#334155", command=self.cancel).pack(side="right")

        self.grab_set()
        self.after(50, self.load_path)
        self.wait_window()

    def _set_busy(self, message="Cargando carpetas..."):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.scroll, text=message, font=("Segoe UI", 14), text_color="#38BDF8").pack(pady=30)

    def load_path(self):
        self.current_path = self.service.normalize_path(self.entry_path.get())
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, self.current_path)
        self._set_busy()
        run_async(lambda: self.service.list_directory(self.current_path), self._render_path, self.app)

    def _render_path(self, adb_output):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not adb_output or self.service.has_listing_error(adb_output):
            ctk.CTkLabel(self.scroll, text="No se pudo leer esta carpeta.", font=("Segoe UI", 13), text_color="#EF4444").pack(pady=24)
            return

        entries = [entry for entry in self.service.parse_listing(adb_output) if entry.is_dir]
        if not entries:
            ctk.CTkLabel(self.scroll, text="No hay subcarpetas aquí.", font=("Segoe UI", 13), text_color="#94A3B8").pack(pady=24)
            return

        for entry in entries:
            row = ctk.CTkButton(
                self.scroll,
                text=f"📁 {entry.name}",
                anchor="w",
                height=38,
                fg_color="#181D2B",
                hover_color="#252D40",
                font=("Segoe UI", 12),
                command=lambda name=entry.name: self.enter_folder(name),
            )
            row.pack(fill="x", pady=4)

    def enter_folder(self, folder_name):
        self.current_path = self.service.enter_folder_path(self.current_path, folder_name)
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, self.current_path)
        self.load_path()

    def go_up(self):
        self.current_path = self.service.go_up_path(self.current_path)
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, self.current_path)
        self.load_path()

    def accept(self):
        self.result = self.service.normalize_path(self.entry_path.get())
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

    def get(self):
        return self.result

class FrameFileExplorer(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.service = FileExplorerService(self.app.adb_cmd)
        self.current_path = self.service.normalize_path("/sdcard/")

        ctk.CTkLabel(self, text="Explorador de Archivos", font=("Segoe UI", 24, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Navega, descarga y envía archivos al dispositivo.", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(0, 15))

        nav_frame = ctk.CTkFrame(self, fg_color="#181D2B", corner_radius=12, border_width=1, border_color="#252D40")
        nav_frame.pack(fill="x", pady=5)

        self.btn_up = ctk.CTkButton(nav_frame, text="⬆ Volver", width=90, height=40, font=("Segoe UI", 13, "bold"), fg_color="#475569", hover_color="#334155", command=self.go_up)
        self.btn_up.pack(side="left", padx=15, pady=15)
        ToolTip(self.btn_up, "Subir un directorio hacia atrás.")

        self.entry_path = ctk.CTkEntry(nav_frame, font=("Consolas", 13), height=40, fg_color="#0B0F19", border_color="#252D40", text_color="#E2E8F0")
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.entry_path.insert(0, self.current_path)
        self.entry_path.bind("<Return>", lambda e: self.load_files())

        self.btn_push = ctk.CTkButton(nav_frame, text="⬆️ Subir Archivo", width=130, height=40, font=("Segoe UI", 13, "bold"), fg_color="#10B981", hover_color="#059669", command=self.upload_file)
        self.btn_push.pack(side="right", padx=15, pady=15)
        ToolTip(self.btn_push, "Envía un archivo desde tu PC a esta carpeta en el teléfono.")

        self.btn_new_folder = ctk.CTkButton(nav_frame, text="📁 Nueva Carpeta", width=130, height=40, font=("Segoe UI", 13, "bold"), fg_color="#8B5CF6", hover_color="#7C3AED", command=self.create_folder)
        self.btn_new_folder.pack(side="right", padx=(0, 15), pady=15)
        ToolTip(self.btn_new_folder, "Crea una carpeta nueva en la ruta actual.")

        self.btn_refresh = ctk.CTkButton(nav_frame, text="🔄 Actualizar", width=110, height=40, font=("Segoe UI", 13, "bold"), fg_color="#38BDF8", hover_color="#0284C7", command=self.load_files)
        self.btn_refresh.pack(side="right", padx=(0, 15), pady=15)
        ToolTip(self.btn_refresh, "Recarga la lista de archivos de la carpeta actual.")

        self.scroll_files = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_files.pack(fill="both", expand=True, pady=10)
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, self.current_path)
        self._sync_back_button_state()
        self._scroll_to_top()

    @requires_device
    def load_files(self):
        for widget in self.scroll_files.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.scroll_files, text="🔄 Cargando directorio...", font=("Segoe UI", 14), text_color="#38BDF8").pack(pady=30)
        self._scroll_to_top()
        
        path = self.service.normalize_path(self.entry_path.get())
        self.current_path = path
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, path)
        run_async(lambda: self.service.list_directory(path), self._update_ui_with_files, self.app)

    def _sync_back_button_state(self):
        current = self.service.normalize_path(self.entry_path.get())
        if not self.service.can_go_up(current):
            self.btn_up.configure(state="disabled", text_color_disabled="#64748B")
        else:
            self.btn_up.configure(state="normal")

    def _scroll_to_top(self):
        canvas = getattr(self.scroll_files, "_parent_canvas", None)
        if canvas:
            try:
                canvas.update_idletasks()
                canvas.yview_moveto(0)
            except:
                pass

    def _update_ui_with_files(self, adb_output):
        for widget in self.scroll_files.winfo_children():
            widget.destroy()

        if not adb_output:
            ctk.CTkLabel(self.scroll_files, text="📁 Carpeta vacía", font=("Segoe UI", 14), text_color="#94A3B8").pack(pady=30)
            return

        if self.service.has_listing_error(adb_output):
            ctk.CTkLabel(self.scroll_files, text="Carpeta sin permisos (requiere root) o inaccesible.", font=("Segoe UI", 13), text_color="#EF4444").pack(pady=20)
            return

        entries = self.service.parse_listing(adb_output)

        if not entries:
            ctk.CTkLabel(self.scroll_files, text="📁 Carpeta vacía", font=("Segoe UI", 14), text_color="#94A3B8").pack(pady=30)
            return

        for entry in entries:
            self.create_file_row(entry)
        self._sync_back_button_state()
        self._scroll_to_top()

    def is_image(self, filename):
        return self.service.is_image_file(filename)

    def create_file_row(self, entry: FileEntry):
        f_name = entry.name
        f_type = 'd' if entry.is_dir else '-'
        f_date = ""
        row = ctk.CTkFrame(self.scroll_files, fg_color="#181D2B", corner_radius=8, border_width=1, border_color="#252D40")
        row.pack(fill="x", pady=3, padx=5)
        row.grid_columnconfigure(1, weight=1)
        
        if f_type in ['d', 'l']:
            icon, color, action = "📁", "#FBBF24", lambda: self.enter_folder(f_name)
        else:
            if self.is_image(f_name):
                icon = "🖼️"
                color = "#A78BFA"
            else:
                icon = "📄"
                color = "#E2E8F0"
            action = lambda: self.download_file(f_name) 
            
        btn_icon = ctk.CTkButton(row, text=icon, width=35, height=35, fg_color="transparent", text_color=color, hover_color="#1E293B", font=("Segoe UI Emoji", 18), command=action)
        btn_icon.grid(row=0, column=0, padx=8, pady=7, sticky="w")
        
        lbl_name = ctk.CTkLabel(row, text=f_name, font=("Segoe UI", 14), text_color=color, anchor="w")
        lbl_name.grid(row=0, column=1, padx=5, pady=7, sticky="ew")
        lbl_name.bind("<Double-Button-1>", lambda e, act=action: act())

        if f_date:
            ctk.CTkLabel(row, text=f_date, font=("Consolas", 12), text_color="#64748B").grid(row=0, column=2, padx=10, pady=7, sticky="e")
        
        btn_del = ctk.CTkButton(row, text="🗑", width=36, height=32, fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI Emoji", 16), command=lambda entry=entry: self.delete_file(entry))
        btn_del.grid(row=0, column=3, padx=8, pady=7, sticky="e")
        ToolTip(btn_del, "Eliminar archivo")

        if f_type == '-':
            btn_copy = ctk.CTkButton(row, text="📄", width=36, height=32, fg_color="#38BDF8", hover_color="#0284C7", font=("Segoe UI Emoji", 16), command=lambda entry=entry: self.copy_entry(entry))
            btn_copy.grid(row=0, column=4, padx=5, pady=7, sticky="e")
            ToolTip(btn_copy, "Copiar archivo")

            btn_move = ctk.CTkButton(row, text="➡", width=36, height=32, fg_color="#F59E0B", hover_color="#D97706", font=("Segoe UI Emoji", 16), command=lambda entry=entry: self.move_entry(entry))
            btn_move.grid(row=0, column=5, padx=5, pady=7, sticky="e")
            ToolTip(btn_move, "Mover archivo")

            btn_rename = ctk.CTkButton(row, text="✏", width=36, height=32, fg_color="#8B5CF6", hover_color="#7C3AED", font=("Segoe UI Emoji", 16), command=lambda entry=entry: self.rename_entry(entry))
            btn_rename.grid(row=0, column=6, padx=5, pady=7, sticky="e")
            ToolTip(btn_rename, "Renombrar archivo")

            btn_ext = ctk.CTkButton(row, text="📥", width=36, height=32, fg_color="#38BDF8", hover_color="#0284C7", font=("Segoe UI Emoji", 16), command=action)
            btn_ext.grid(row=0, column=7, padx=5, pady=7, sticky="e")
            ToolTip(btn_ext, "Descargar archivo")
        else:
            btn_copy = ctk.CTkButton(row, text="📄", width=36, height=32, fg_color="#38BDF8", hover_color="#0284C7", font=("Segoe UI Emoji", 16), command=lambda entry=entry: self.copy_entry(entry))
            btn_copy.grid(row=0, column=4, padx=5, pady=7, sticky="e")
            ToolTip(btn_copy, "Copiar carpeta")

            btn_move = ctk.CTkButton(row, text="➡", width=36, height=32, fg_color="#F59E0B", hover_color="#D97706", font=("Segoe UI Emoji", 16), command=lambda entry=entry: self.move_entry(entry))
            btn_move.grid(row=0, column=5, padx=5, pady=7, sticky="e")
            ToolTip(btn_move, "Mover carpeta")

            btn_rename = ctk.CTkButton(row, text="✏", width=36, height=32, fg_color="#8B5CF6", hover_color="#7C3AED", font=("Segoe UI Emoji", 16), command=lambda entry=entry: self.rename_entry(entry))
            btn_rename.grid(row=0, column=6, padx=5, pady=7, sticky="e")
            ToolTip(btn_rename, "Renombrar carpeta")

    def delete_file(self, entry: FileEntry):
        f_name = entry.name
        if utils.AskYesNo(self.app, "Confirmar", f"¿Eliminar '{f_name}' permanentemente?").get():
            def on_delete_done(res):
                if res is not None and not str(res).strip():
                    utils.show_alert(self.app, "Advertencia", "El elemento fue eliminado.", is_error=False)
                else:
                    utils.show_alert(self.app, "Advertencia", "La operación requiere permisos o falló.", is_error=False)
                self.load_files()
                
            run_async(lambda: self.service.delete_entry(self.entry_path.get(), f_name), on_delete_done, self.app)

    def _ask_destination_path(self, title, text, default_value=""):
        return AskString(self.app, title, text, initial_value=default_value).get()

    def _pick_remote_folder(self, title):
        picker = RemoteFolderPicker(self.app, self.service, self.entry_path.get(), title=title)
        return picker.get()

    @requires_device
    def copy_entry(self, entry: FileEntry):
        destination = self._pick_remote_folder("Copiar en carpeta")
        if not destination:
            return

        def callback(res):
            if res is not None and "error" not in str(res).lower() and "failed" not in str(res).lower():
                self.app.show_toast("Copiado con éxito")
                self.load_files()
            else:
                utils.show_alert(self.app, "Error", "No se pudo copiar el archivo.", is_error=True)

        run_async(lambda: self.service.copy_entry(self.entry_path.get(), entry.name, destination), callback, self.app)

    @requires_device
    def move_entry(self, entry: FileEntry):
        destination = self._pick_remote_folder("Mover a carpeta")
        if not destination:
            return

        def callback(res):
            if res is not None and "error" not in str(res).lower() and "failed" not in str(res).lower():
                self.app.show_toast("Movido con éxito")
                self.load_files()
            else:
                utils.show_alert(self.app, "Error", "No se pudo mover el elemento.", is_error=True)

        run_async(lambda: self.service.move_entry(self.entry_path.get(), entry.name, destination), callback, self.app)

    @requires_device
    def rename_entry(self, entry: FileEntry):
        new_name = self._ask_destination_path("Renombrar", f"Nuevo nombre para '{entry.name}'", default_value=entry.name)
        if not new_name or new_name == entry.name:
            return

        def callback(res):
            if res is not None and "error" not in str(res).lower() and "failed" not in str(res).lower():
                self.app.show_toast("Renombrado con éxito")
                self.load_files()
            else:
                utils.show_alert(self.app, "Error", "No se pudo renombrar.", is_error=True)

        run_async(lambda: self.service.rename_entry(self.entry_path.get(), entry.name, new_name), callback, self.app)

    @requires_device
    def create_folder(self):
        folder_name = self._ask_destination_path("Nueva carpeta", "Nombre de la carpeta")
        if not folder_name:
            return

        def callback(res):
            if res is not None and "error" not in str(res).lower() and "failed" not in str(res).lower():
                self.app.show_toast("Carpeta creada")
                self.load_files()
            else:
                utils.show_alert(self.app, "Error", "No se pudo crear la carpeta.", is_error=True)

        run_async(lambda: self.service.create_directory(self.entry_path.get(), folder_name), callback, self.app)

    @requires_device
    def download_file(self, file_name):
        remote_path = posixpath.join(self.entry_path.get(), file_name)
        local_path = filedialog.asksaveasfilename(initialfile=file_name, title="Guardar como...")
        
        if local_path:
            self.app.show_toast(f"Descargando {file_name}...", color="#38BDF8")
            def callback(res):
                if res is not None and "error" not in str(res).lower() and "failed" not in str(res).lower():
                    self.app.show_toast("¡Guardado con éxito!")
                else:
                    utils.show_alert(self.app, "Error", "No se pudo descargar el archivo.", is_error=True)
            run_async(lambda: self.service.pull_file(remote_path, local_path), callback, self.app)

    @requires_device
    def upload_file(self):
        local_path = filedialog.askopenfilename(title="Seleccionar archivo")
        if local_path:
            file_name = os.path.basename(local_path)
            remote_path = posixpath.join(self.entry_path.get(), file_name)
            
            self.app.show_toast(f"Subiendo {file_name}...", color="#38BDF8")
            def callback(res):
                if res is not None and "error" not in str(res).lower() and "failed" not in str(res).lower():
                    self.app.show_toast("¡Subido con éxito!")
                    self.load_files()
                else:
                    utils.show_alert(self.app, "Error", "No se pudo subir el archivo.", is_error=True)
            run_async(lambda: self.service.push_file(local_path, remote_path), callback, self.app)

    def enter_folder(self, folder_name):
        new_path = self.service.enter_folder_path(self.entry_path.get(), folder_name)
        self.current_path = new_path
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, new_path)
        self._sync_back_button_state()
        self.load_files()

    def go_up(self):
        current = self.service.normalize_path(self.entry_path.get())
        if current in ["/", "/sdcard/"]:
            self._sync_back_button_state()
            return

        new_path = self.service.go_up_path(current)
        self.current_path = new_path
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, new_path)
        self._sync_back_button_state()
        self.load_files()