from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class AnalysisStatus(str, Enum):
    TRUE_POSITIVE = "True Positive"
    FALSE_POSITIVE = "False Positive"
    UNCERTAIN = "Uncertain"

class Finding(BaseModel):
    """Modelo de datos para el hallazgo original (raw finding)"""
    id: str
    type: str
    sink_line: int
    source_line: int
    message: str
    file_path: str = "sample.py"

class SecurityAnalysis(BaseModel):
    """Modelo de datos para el resultado del análisis de seguridad"""
    finding_id: str
    status: AnalysisStatus
    confidence_score: int = Field(..., ge=0, le=100, description="Nivel de confianza 0-100")
    reasoning: str = Field(..., description="Explicación técnica del por qué")
    severity: Severity
    remediation_suggestion: Optional[str] = None

