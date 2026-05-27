import re


class AnalyzerService:
    PLACEHOLDER = "[Pega el registro de error o stack trace aquí...]"

    @staticmethod
    def is_placeholder(text):
        return AnalyzerService.PLACEHOLDER in (text or "")

    @staticmethod
    def analyze_log(log_text):
        if not log_text or AnalyzerService.is_placeholder(log_text):
            return "⚠️ Por favor, pega un registro primero."

        report = "✅ No se detectó ningún crash en el texto proporcionado."
        if "FATAL" not in log_text and "Exception" not in log_text:
            return report

        lines = log_text.splitlines()
        root_cause = AnalyzerService.extract_root_cause(lines, log_text)
        loc = AnalyzerService.extract_suspect_location(lines)

        report = "🔥 CRASH DETECTADO\n" + "-" * 40 + "\n"
        report += f"❌ CAUSA: {root_cause}\n\n📍 ARCHIVO SOSPECHOSO:\n   {loc}\n"
        report += AnalyzerService.build_hint(root_cause)
        return report

    @staticmethod
    def extract_root_cause(lines, log_text):
        for line in lines:
            if "Caused by:" in line:
                return line.split("Caused by:", 1)[1].strip()

        match = re.search(r"FATAL EXCEPTION:.*?\n.*?(\w+\.\w+Exception)", log_text, re.DOTALL)
        if match:
            return match.group(1)

        return "Error Desconocido"

    @staticmethod
    def extract_suspect_location(lines):
        for line in lines:
            if "at " in line and "(" in line:
                if not any(x in line for x in ["android.", "java.", "com.android", "zygote", "androidx."]):
                    return line.strip().replace("at ", "")
        return "Framework del Sistema (¿No es tu código?)"

    @staticmethod
    def build_hint(root_cause):
        if "NullPointer" in root_cause:
            return "\n💡 EXPLICACIÓN: Intentaste usar una variable que estaba vacía (null). Verifica si inicializaste tus vistas o variables."
        if "IndexOutOfBounds" in root_cause:
            return "\n💡 EXPLICACIÓN: Intentaste obtener un ítem de una lista, pero el índice era demasiado grande (o la lista estaba vacía)."
        if "ActivityNotFound" in root_cause:
            return "\n💡 EXPLICACIÓN: Intentaste abrir una pantalla (Activity) que no está declarada en el AndroidManifest.xml."
        return ""