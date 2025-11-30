import os
import json
import re
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.domain.models import Finding


load_dotenv()

class GeminiSecurityAnalyst:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en .env")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def _clean_json_response(self, text: str) -> str:
        """Limpia la respuesta para extraer solo el JSON válido."""
        text = text.strip()
        
        # Detección y limpieza de bloques de código Markdown
        if text.startswith("```"):
            # Busca el contenido entre las primeras llaves {}
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return match.group(0)
            else:
                # Fallback de limpieza manual
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                return "\n".join(lines)
        return text

    def analyze_vulnerability(self, code_snippet: str, finding: Finding) -> Dict[str, Any]:
        """
        Envía el código y el hallazgo a Gemini para validación.
        """
        
        system_instruction = """
        Actúa como un Ingeniero de Seguridad de Aplicaciones (AppSec) Principal especializado en revisión de código Python.
        Tu objetivo es realizar un triaje de alta precisión de hallazgos SAST, minimizando drásticamente los Falsos Positivos.

        METODOLOGÍA DE ANÁLISIS (TAINT ANALYSIS):
        1.  **Identificar Fuente (Source):** ¿La variable proviene de una entrada no confiable (request, input, db, archivo)?
        2.  **Rastrear Flujo:** Sigue la variable a través de asignaciones y funciones hasta llegar al sumidero (Sink).
        3.  **Verificar Sanitización:** ¿Existe algún paso intermedio que limpie, valide o neutralice el dato? (ej: casting a int, whitelisting, consultas parametrizadas, ORM).
        4.  **Evaluar Contexto:** ¿Es el código alcanzable? ¿Son valores hardcodeados seguros?

        CRITERIOS DE CLASIFICACIÓN:
        -   **True Positive:** Existe un camino claro desde una fuente no confiable hasta un sink peligroso SIN sanitización adecuada.
        -   **False Positive:** El input es seguro (hardcodeado), existe sanitización efectiva (ej: `subprocess.run(["cmd", arg])`), o el código es inalcanzable.
        -   **Uncertain:** Falta contexto del código para determinar el flujo (ej: función externa desconocida).

        GUÍA DE SEVERIDAD:
        -   **CRITICAL:** RCE (Command Injection), SQLi masivo, Auth Bypass.
        -   **HIGH:** SQLi estándar, SSRF a red interna, Path Traversal.
        -   **MEDIUM:** XSS, Exposición de datos sensibles, SSRF limitado.
        -   **LOW:** Malas prácticas, configuraciones débiles.
        -   **INFO:** Sugerencias de estilo o mantenimiento.

        FORMATO DE SALIDA (JSON):
        Responde ÚNICAMENTE con un JSON válido.
        {
            "status": "True Positive" | "False Positive" | "Uncertain",
            "confidence_score": 0-100 (Entero. Sé conservador, 100 requiere certeza absoluta),
            "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO",
            "reasoning": "Explicación técnica detallada en español. Cita variables y líneas de código. Explica POR QUÉ el control es suficiente o insuficiente.",
            "remediation_suggestion": "Solución técnica en español. Si es TP, sugiere código seguro (ej: usar `subprocess.run` con lista). Si es FP, explica por qué es seguro."
        }
        """

        prompt = f"""
        ANALIZA:
        Tipo: {finding.type}
        Msg: {finding.message}
        Source Line: {finding.source_line}
        Sink Line: {finding.sink_line}
        
        CODIGO:
        ```python
        {code_snippet}
        ```
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                )
            )
            
            if not response.text:
                raise ValueError("La IA devolvió una respuesta vacía")

            clean_text = self._clean_json_response(response.text)
            return json.loads(clean_text)

        except Exception as e:
            # Manejo de errores para garantizar continuidad del proceso
            return {
                "status": "Uncertain",
                "confidence_score": 0,
                "severity": "LOW",
                "reasoning": f"Error técnico en análisis: {str(e)}",
                "remediation_suggestion": None
            }

