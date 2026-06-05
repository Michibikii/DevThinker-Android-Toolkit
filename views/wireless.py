import customtkinter as ctk
import threading
import utils
from utils import ToolTip
from services import WirelessService

class FrameWireless(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.service = WirelessService(self.app.adb_cmd)
        
        ctk.CTkLabel(self, text="Conectar Dispositivo", font=("Segoe UI", 24, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(0,5))
        ctk.CTkLabel(self, text="Conecta tu dispositivo mediante Wi-Fi de forma remota o cable USB.", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(0,15))
        
        ctk.CTkLabel(self, text="⚠️ Nota: Asegúrate de pausar cualquier VPN o Adblocker (ej. Blokada/AdGuard) antes de conectar de forma inalámbrica.", text_color="#F59E0B", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 15))

        self.tabs = ctk.CTkTabview(self, fg_color="#181D2B", segmented_button_fg_color="#0B0F19", segmented_button_selected_color="#1E293B", segmented_button_selected_hover_color="#252D40", segmented_button_unselected_hover_color="#181D2B", text_color="#E2E8F0", border_width=1, border_color="#252D40", corner_radius=12)
        self.tabs.pack(fill="both", expand=True, pady=5)
        
        self.tab_qr = self.tabs.add("📱 Escanear QR")
        self.tab_manual = self.tabs.add("⌨️ Conectar por IP/Puerto")
        self.tab_legacy = self.tabs.add("🔌 Conectar con Cable USB")
        
        self.setup_qr_tab()
        self.setup_manual_tab()
        self.setup_legacy_tab()

    def _add_tab_header(self, tab, title, instructions):
        f_header = ctk.CTkFrame(tab, fg_color="transparent")
        f_header.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(f_header, text=title, font=("Segoe UI", 16, "bold"), text_color="#F8FAFC").pack(anchor="w")
        ctk.CTkLabel(f_header, text=instructions, font=("Segoe UI", 13), text_color="#94A3B8", justify="left").pack(anchor="w", pady=(2, 0))

    def _safe_after(self, delay, callback):
        try:
            self.app.after(delay, callback)
        except:
            pass

    def _wait_for_connection_port(self, target_ip, timeout=12):
        return self.service.wait_for_connection_port(target_ip, timeout=timeout)

    def _end_process(self, btn, text, msg, success=False):
        self._safe_after(0, lambda: btn.configure(text=text, state="normal"))
        self._safe_after(100, lambda: utils.ShowInfo(self.app, "¡Éxito!" if success else "Error de Conexión", msg, not success))

    def setup_qr_tab(self):
        payload = self.service.build_qr_payload()
        self.qr_pass = payload["qr_pass"]
        self.qr_name = payload["qr_name"]
        self.qr_data = payload["qr_data"]
        
        instructions = (
            "1. Ve a Opciones de Desarrollador > Depuración Inalámbrica.\n"
            "2. Toca 'Vincular dispositivo con código QR' y escanea esto:"
        )
        self._add_tab_header(self.tab_qr, "📱 Conexión por Código QR", instructions)
        
        f_content = ctk.CTkFrame(self.tab_qr, fg_color="transparent")
        f_content.pack(fill="both", expand=True)
        
        self.lbl_qr = ctk.CTkLabel(f_content, text="Cargando código QR...", font=("Segoe UI", 12), text_color="#94A3B8")
        self.lbl_qr.pack(expand=True)
        
        self.btn_scan = ctk.CTkButton(f_content, text="🔍 Buscar y Conectar", font=("Segoe UI", 14, "bold"), fg_color="#10B981", hover_color="#059669", height=45, width=220, command=self.scan_mdns, text_color_disabled="#94A3B8")
        self.btn_scan.pack(pady=20)

        
        self.after(50, self.load_qr)

    def load_qr(self):
        try:
            image = self.service.fetch_qr_image(self.qr_data)
            ctk_img = ctk.CTkImage(light_image=image, dark_image=image, size=(220, 220))
            self._qr_image = ctk_img
            self._safe_after(0, lambda: self.lbl_qr.configure(image=self._qr_image, text=""))

        except Exception:
            self._safe_after(0, lambda: utils.show_alert(self.app, "Error", "No se pudo generar el código QR.", is_error=True))

    def scan_mdns(self):
        self.btn_scan.configure(text="⏳ Rastreando la red local...", state="disabled")
        threading.Thread(target=self._mdns_thread, daemon=True).start()

    def _mdns_thread(self):
        self.service.mdns_check()
        out = self.service.find_pairing_port(self.qr_name)
        if not out:
            self._end_process(self.btn_scan, "🔍 Buscar y Conectar", "La red local no responde. Verifica que la PC tenga Wi-Fi activado o desactiva VPNs.", False)
            return

        pairing_ip_port = out

        if not pairing_ip_port:
            self._end_process(self.btn_scan, "🔍 Buscar y Conectar", "No se detectó el celular.\n1. Asegúrate de tener la pantalla del escáner QR abierta en el teléfono.\n2. Revisa que estén en la misma red Wi-Fi.", False)
            return
            
        self._safe_after(0, lambda: self.btn_scan.configure(text="⏳ Vinculando dispositivo..."))
        
        pair_res = self.service.pair_with_qr(pairing_ip_port, self.qr_pass)
        if not pair_res or ("Failed" in pair_res or "error" in pair_res.lower()):
            try:
                utils.connection_log(f"wireless failed stage=pair pair_port={pairing_ip_port!r} result={pair_res!r}")
            except Exception:
                pass
            self._end_process(self.btn_scan, "🔍 Buscar y Conectar", f"El teléfono rechazó la vinculación. Intenta de nuevo.\nDetalle: {pair_res}", False)
            return
            
        self._safe_after(0, lambda: self.btn_scan.configure(text="⏳ Cazando puerto de conexión..."))
        
        ip_only = pairing_ip_port.split(':')[0]
        connect_ip_port = self._wait_for_connection_port(ip_only)
        
        if connect_ip_port:
            conn_res = self.service.connect(connect_ip_port)
            if conn_res and "connected" in conn_res.lower():
                try:
                    utils.connection_log(f"wireless success pair_port={pairing_ip_port!r} connect_port={connect_ip_port!r}")
                except Exception:
                    pass
                self._end_process(self.btn_scan, "🔍 Buscar y Conectar", f"El dispositivo se conectó exitosamente de forma inalámbrica en:\n{connect_ip_port}", True)
            else:
                try:
                    utils.connection_log(f"wireless failed stage=connect pair_port={pairing_ip_port!r} connect_port={connect_ip_port!r} result={conn_res!r}")
                except Exception:
                    pass
                self._end_process(self.btn_scan, "🔍 Buscar y Conectar", f"Se encontró el puerto, pero ADB denegó la conexión final:\n{conn_res}", False)
        else:
            try:
                utils.connection_log(f"wireless failed stage=discover pair_port={pairing_ip_port!r} result='no connect port exposed'")
            except Exception:
                pass
            self._end_process(self.btn_scan, "🔍 Buscar y Conectar", "El dispositivo se vinculó con éxito, pero Android nunca expuso el puerto de conexión final.\nIntenta desactivar y reactivar la 'Depuración Inalámbrica' en el celular.", False)

    def setup_manual_tab(self):
        instructions = (
            "Ingresa la IP y el Puerto de 'Depuración Inalámbrica'. El código es opcional y solo necesario si es la primera vez en Android 11+.\n"
            "Presiona 'Vincular / Conectar' para iniciar el proceso."
        )
        self._add_tab_header(self.tab_manual, "⌨️ Conexión Manual por IP", instructions)
        
        f_main = ctk.CTkFrame(self.tab_manual, fg_color="#0B0F19", corner_radius=12, border_width=1, border_color="#252D40")
        f_main.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        f_center = ctk.CTkFrame(f_main, fg_color="transparent")
        f_center.pack(expand=True)
        
        row1 = ctk.CTkFrame(f_center, fg_color="transparent")
        row1.pack(fill="x", pady=15)
        
        self.entry_ip = ctk.CTkEntry(row1, placeholder_text="IP (ej. 192.168.1.5)", font=("Consolas", 13), width=200, height=45, fg_color="#181D2B", border_color="#252D40", text_color="#F8FAFC")
        self.entry_ip.pack(side="left", padx=(0, 15))
        
        self.entry_port = ctk.CTkEntry(row1, placeholder_text="Puerto", font=("Consolas", 13), width=100, height=45, fg_color="#181D2B", border_color="#252D40", text_color="#F8FAFC")
        self.entry_port.pack(side="left", padx=(0, 15))
        
        self.entry_code = ctk.CTkEntry(row1, placeholder_text="Código (Opcional)", font=("Consolas", 13), width=150, height=45, fg_color="#181D2B", border_color="#252D40", text_color="#F8FAFC")
        self.entry_code.pack(side="left")

        self.btn_manual_connect = ctk.CTkButton(f_center, text="Vincular / Conectar", font=("Segoe UI", 14, "bold"), height=45, width=220, fg_color="#38BDF8", hover_color="#0284C7", command=self.start_manual_connection)
        self.btn_manual_connect.pack(pady=20)

    def start_manual_connection(self):
        ip = self.entry_ip.get().strip()
        port = self.entry_port.get().strip()
        pair_code = self.entry_code.get().strip()

        if not ip or not port:
            utils.show_alert(self.app, "Advertencia", "Debes rellenar al menos la IP y el Puerto.", is_error=False)
            return

        pair_addr = f"{ip}:{port}"
        self.btn_manual_connect.configure(text="⏳ Procesando...", state="disabled")
        
        if pair_code:
            threading.Thread(target=self._manual_connect_thread, args=(pair_addr, pair_code), daemon=True).start()
        else:
            self.app.show_toast("Conectando...", color="#38BDF8")
            utils.run_async(lambda: self.service.connect(pair_addr), lambda res: self._post_connect_legacy(res), self.app)

    def _post_connect_legacy(self, res):
        if res and "connected" in res.lower() and "fail" not in res.lower():
            self.app.show_toast("¡Conectado exitosamente!", color="#10B981")
        elif res and ("fail" in res.lower() or "cannot connect" in res.lower() or "error" in res.lower()):
            utils.show_alert(self.app, "Error", "No se pudo completar la conexión manual.", is_error=True)
        else:
            self.app.show_toast("Intento finalizado", color="#F59E0B")
            
        self._safe_after(0, lambda: self.btn_manual_connect.configure(text="Vincular / Conectar", state="normal"))

    def _manual_connect_thread(self, pair_addr, pair_code):
        self.service.mdns_check()
        pair_res = self.service.pair_with_qr(pair_addr, pair_code)
        
        if pair_res and ("Successfully paired" in pair_res or "Already paired" in pair_res or "successfully" in pair_res.lower()):
            self._safe_after(0, lambda: self.btn_manual_connect.configure(text="⏳ Conectando..."))
            
            ip_only = pair_addr.split(':')[0]
            connect_ip_port = self._wait_for_connection_port(ip_only)
            
            if connect_ip_port:
                conn_res = self.service.connect(connect_ip_port)
                if conn_res and "connected" in conn_res.lower():
                    try:
                        utils.connection_log(f"wireless success pair_port={pair_addr!r} connect_port={connect_ip_port!r}")
                    except Exception:
                        pass
                    self._end_process(self.btn_manual_connect, "Vincular / Conectar", f"¡Conexión inyectada automáticamente en {connect_ip_port}!", True)
                    return

                try:
                    utils.connection_log(f"wireless failed stage=connect pair_port={pair_addr!r} connect_port={connect_ip_port!r} result={conn_res!r}")
                except Exception:
                    pass
            
            try:
                utils.connection_log(f"wireless failed stage=discover pair_port={pair_addr!r} result='no connect port exposed'")
            except Exception:
                pass
            self._end_process(self.btn_manual_connect, "Vincular / Conectar", "Se vinculó correctamente, pero el router bloqueó el auto-descubrimiento.\nVe a Utilidades y conéctate usando el puerto principal manualmente.", False)
        else:
            try:
                utils.connection_log(f"wireless failed stage=pair pair_port={pair_addr!r} result={pair_res!r}")
            except Exception:
                pass
            self._end_process(self.btn_manual_connect, "Vincular / Conectar", f"Credenciales rechazadas por el teléfono:\n{pair_res}", False)

    def setup_legacy_tab(self):
        instructions = (
            "1. Activa la 'Depuración USB' en las Opciones de Desarrollador.\n"
            "2. Conecta tu teléfono a la PC usando el cable USB."
        )
        self._add_tab_header(self.tab_legacy, "🔌 Conexión por Cable USB", instructions)
        
        f_content = ctk.CTkFrame(self.tab_legacy, fg_color="#0B0F19", corner_radius=12, border_width=1, border_color="#252D40")
        f_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        f_center = ctk.CTkFrame(f_content, fg_color="transparent")
        f_center.pack(expand=True)
        
        ctk.CTkLabel(f_center, text="🔌", font=("Segoe UI Emoji", 45), text_color="#F8FAFC").pack(pady=(0, 20))

        self.btn_usb_connect = ctk.CTkButton(f_center, text="Buscar Dispositivo USB", font=("Segoe UI", 14, "bold"), height=45, width=220, fg_color="#8B5CF6", hover_color="#7C3AED", command=self.conectar_usb_directo)
        self.btn_usb_connect.pack()


    def conectar_usb_directo(self):
        self.btn_usb_connect.configure(text="⏳ Buscando...", state="disabled")
        
        def task():
            return self.service.scan_usb()
            
        def on_done(out):
            self._safe_after(0, lambda: self.btn_usb_connect.configure(text="Buscar Dispositivo USB", state="normal"))
            
            if not out:
                utils.show_alert(self.app, "Error", "Error crítico al ejecutar ADB.", is_error=True)
                return

            state = self.service.parse_usb_state(out)

            if state == "connected":
                try:
                    utils.connection_log("usb success state=connected")
                except Exception:
                    pass
                self.app.show_toast("¡Dispositivo USB detectado y listo!", color="#10B981")
            elif state == "unauthorized":
                try:
                    utils.connection_log("usb failed state=unauthorized")
                except Exception:
                    pass
                utils.ShowInfo(self.app, "Autorización Pendiente", "El dispositivo está conectado pero bloqueado.\n\nPor favor, enciende la pantalla de tu celular y presiona 'Permitir depuración USB'.", True)
            elif state == "offline":
                try:
                    utils.connection_log("usb failed state=offline")
                except Exception:
                    pass
                utils.show_alert(self.app, "Advertencia", "El dispositivo está offline. Desconecta y reconecta el cable.", is_error=False)
            else:
                try:
                    utils.connection_log(f"usb failed state={state!r}")
                except Exception:
                    pass
                utils.ShowInfo(self.app, "No Detectado", "No se encontró ningún teléfono.\n\n1. Revisa el cable USB.\n2. Asegúrate de tener activada la 'Depuración USB' en tu celular.", True)

        utils.run_async(task, on_done, self.app)