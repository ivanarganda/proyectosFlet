from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
import typer

try:
    # Python 3.9+
    from importlib.resources import files as ir_files
except ImportError:
    ir_files = None  # type: ignore

app = typer.Typer(help="ivbox CLI - Framework sobre Flet")


def _template_project_dir() -> Path:
    """
    Devuelve la ruta a ivbox/templates/base_app.

    - En desarrollo (editable), puede crear la carpeta si no existe.
    - En instalación desde PyPI, la plantilla DEBE venir empaquetada (no se puede "crear" dentro del site-packages).
    """
    # 1) Intento: buscar dentro del paquete (PyPI / editable)
    if ir_files is not None:
        template = ir_files("ivbox").joinpath("templates", "base_app")

        try:
            p = Path(template)
        except TypeError:
            p = Path(str(template))

        if p.exists():
            return p

    # 2) Fallback desarrollo: ruta relativa al repo (ivbox/cli/main.py -> ivbox/)
    base = Path(__file__).resolve().parent.parent  # .../ivbox/
    p = base / "templates" / "base_app"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _copytree(src: Path, dst: Path) -> None:
    """
    Copia recursivamente src -> dst.
    Si src está vacío, crea solo dst (sin fallar).
    """
    if not src.exists():
        raise FileNotFoundError(f"No encuentro la plantilla: {src}")

    if dst.exists():
        raise FileExistsError(f"La carpeta '{dst.name}' ya existe en: {dst.parent}")

    # Si la plantilla está vacía, crea solo la carpeta destino
    try:
        is_empty = not any(src.iterdir())
    except Exception:
        is_empty = False

    if is_empty:
        dst.mkdir(parents=True, exist_ok=True)
        return

    shutil.copytree(src, dst)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """
    Ejecuta un comando del sistema (pip, etc.) con salida visible.
    """
    typer.echo(f"▶ Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def _install_deps(target: Path) -> None:
    """
    Instala dependencias del proyecto creado.
    Prioridad:
      1) requirements.txt
      2) pyproject.toml (instala el proyecto como paquete local)
      3) fallback mínimo (flet + ivbox-utils)
    """
    req = target / "requirements.txt"
    pyproj = target / "pyproject.toml"

    if req.exists():
        _run([sys.executable, "-m", "pip", "install", "-r", str(req)], cwd=target)
        return

    if pyproj.exists():
        # Instala el proyecto local (si tu pyproject está bien configurado)
        _run([sys.executable, "-m", "pip", "install", "."], cwd=target)
        return

    # Fallback mínimo
    _run([sys.executable, "-m", "pip", "install", "flet"], cwd=target)
    _run([sys.executable, "-m", "pip", "install", "ivbox-utils"], cwd=target)


@app.command()
def new(
    name: str = typer.Argument(..., help="Nombre del proyecto (carpeta a crear)."),
    install: bool = typer.Option(False, "--install", help="Instala dependencias tras crear el proyecto."),
):
    """
    Crea un nuevo proyecto ivbox copiando la plantilla incluida en el paquete.
    """
    target = Path.cwd() / name
    template_dir = _template_project_dir()

    typer.echo(f"Creando proyecto: {name}")
    _copytree(template_dir, target)
    typer.echo(f"✅ Proyecto creado en: {target}")

    typer.echo("Instalando dependencias...")
    _install_deps(target)


@app.command()
def create(
    kind: str = typer.Argument(..., help="Tipo: view|middleware|component"),
    name: str = typer.Argument(..., help="Nombre del recurso"),
):
    """Crea recursos: view, middleware, component, etc."""
    typer.echo(f"Creando {kind}: {name}")
    # TODO: aquí irán tus generadores reales


def main():
    app()


if __name__ == "__main__":
    main()