import json
import asyncio
import os
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict
from app.domain.models import Finding, SecurityAnalysis, Severity
from app.infrastructure.gemini_client import GeminiSecurityAnalyst
from app.infrastructure.file_reader import CodeContextExtractor

class VulnerabilityScanner:
    def __init__(self, analyst: GeminiSecurityAnalyst):
        self.analyst = analyst
        self.extractor = CodeContextExtractor()

    def load_findings(self, findings_path: str) -> List[Finding]:
        with open(findings_path, 'r') as f:
            data = json.load(f)
            # Normalización de la estructura de datos de entrada
            # Se espera una lista bajo la clave "vulnerabilities"
            raw_list = data.get("vulnerabilities", [])
            
            findings = []
            for item in raw_list:
                # Mapeo de atributos al modelo de dominio
                findings.append(Finding(
                    id=item.get("id"),
                    type=item.get("type"),
                    sink_line=item.get("sink_line"),
                    source_line=item.get("source_line"),
                    message=item.get("message"),
                    file_path="sample/sample.py" # TODO: Parametrizar ruta de archivo fuente
                ))
            return findings

    async def scan(self, findings_path: str) -> List[Dict]:
        findings = self.load_findings(findings_path)
        results = []
        
        print(f"Iniciando análisis de {len(findings)} hallazgos...")

        for finding in findings:
            print(f"  >> Analizando {finding.id} ({finding.type})...")
            
            # Recuperación del contexto de código fuente
            try:
                code_snippet = self.extractor.extract_context(
                    finding.file_path, 
                    finding.source_line, 
                    finding.sink_line
                )
            except Exception as e:
                print(f"Error leyendo archivo: {e}")
                continue

            # Análisis de vulnerabilidad mediante LLM
            # Nota: Ejecución síncrona intencional para control de rate-limits.
            analysis_dict = self.analyst.analyze_vulnerability(code_snippet, finding)
            
            # Consolidación de resultados
            result = {
                "finding_id": finding.id,
                "rule_id": finding.type,
                "original_message": finding.message,
                "ai_analysis": analysis_dict
            }
            results.append(result)
            
        return results

    def generate_html_report(self, results: List[Dict], output_path: str):
        """Genera un reporte HTML visual usando Jinja2"""
        # Ruta absoluta al directorio de templates
        template_dir = os.path.join(os.path.dirname(__file__), '../infrastructure/templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('report_template.html')
        
        html_content = template.render(results=results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Reporte HTML generado en: {output_path}")
