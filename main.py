import typer
import asyncio
import json
import os
from rich.console import Console
from rich.table import Table
from app.infrastructure.gemini_client import GeminiSecurityAnalyst
from app.application.scanner import VulnerabilityScanner

# Inicialización de componentes CLI y UI
cli = typer.Typer(pretty_exceptions_show_locals=False, no_args_is_help=True)
console = Console()

@cli.command(name="scan") 
def scan_command(
    findings: str = typer.Option("./sample/findings.json", help="Ruta al archivo JSON de hallazgos"),
    output: str = typer.Option("report.json", help="Archivo de salida JSON"),
    model: str = typer.Option("gemini-2.5-flash", help="Modelo de IA a usar")
):
    """
    Ejecuta el análisis de vulnerabilidades asistido por IA.
    
    Procesa un archivo de hallazgos SAST, enriquece la información utilizando un LLM
    para determinar falsos positivos y genera reportes en formatos JSON y HTML.
    """
    # Validación de pre-condiciones
    if not os.path.exists(findings):
        console.print(f"[bold red]Error:[/bold red] No se encontró el archivo de hallazgos: {findings}")
        console.print("[yellow]Verifique que la ruta al archivo de hallazgos sea correcta.[/yellow]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Iniciando AI AppSec Scanner con modelo {model}...[/bold green]")

    try:
        # Configuración del grafo de dependencias
        analyst = GeminiSecurityAnalyst(model_name=model)
        scanner = VulnerabilityScanner(analyst)

        # Ejecución del flujo de análisis
        results = asyncio.run(scanner.scan(findings))

        # Persistencia de resultados
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generación de reportes visuales
        html_output = output.replace(".json", ".html")
        scanner.generate_html_report(results, html_output)
        
        # Resumen de ejecución en consola
        table = Table(title="Resultados del Análisis")
        table.add_column("ID", style="cyan")
        table.add_column("Tipo", style="magenta")
        table.add_column("Estado AI", style="bold")
        table.add_column("Severidad", style="red")
        
        for res in results:
            ai_data = res.get("ai_analysis", {})
            status = ai_data.get("status", "N/A")
            
            # Determinación de estilos visuales según severidad y estado
            color = "green" if status == "False Positive" else "red"
            if status == "Uncertain": color = "yellow"
            
            table.add_row(
                str(res.get("finding_id", "N/A")),
                str(res.get("rule_id", "N/A")),
                f"[{color}]{status}[/{color}]",
                str(ai_data.get("severity", "UNKNOWN"))
            )

        console.print(table)
        console.print(f"\n[bold blue]Reporte guardado en: {output}[/bold blue]")

    except Exception as e:
        console.print(f"[bold red]Fallo crítico en la ejecución:[/bold red] {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    cli()
