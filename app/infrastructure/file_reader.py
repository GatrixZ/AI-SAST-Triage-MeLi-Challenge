import os
from typing import List

class CodeContextExtractor:
    """
    Lee archivos y extrae fragmentos de código relevantes alrededor de las vulnerabilidades.
    """
    
    def read_file(self, file_path: str) -> List[str]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe.")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def extract_context(self, file_path: str, start_line: int, end_line: int, padding: int = 5) -> str:
        """
        Extrae las líneas entre start y end, más un 'padding' arriba y abajo para dar contexto.
        Maneja índices de línea base-1 (humano) a base-0 (lista).
        """
        lines = self.read_file(file_path)
        total_lines = len(lines)
        
        # Normalización de rango de líneas
        actual_start = min(start_line, end_line)
        actual_end = max(start_line, end_line)
        
        # Cálculo de ventana de contexto con padding
        extract_start = max(0, actual_start - 1 - padding)
        extract_end = min(total_lines, actual_end + padding)
        
        snippet = []
        for i in range(extract_start, extract_end):
            # Inclusión de números de línea para referencia en el análisis
            line_num = i + 1
            marker = " >> " if line_num == start_line or line_num == end_line else "    "
            snippet.append(f"{line_num:4d}{marker}{lines[i]}")
            
        return "".join(snippet)
