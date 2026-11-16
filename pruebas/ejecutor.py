"""Ejecutor general del corpus de pruebas de mini-C (P5).

Recorre los programas `.c` del corpus, ejecuta el flujo completo
(lexer -> convertidor a AST -> analizador semántico) y comprueba que cada caso
coincida con la directiva `// ESPERADO: ...` de su primera línea, verificando
además que cada error reporte línea y causa.

Uso desde la raíz del repositorio:
    python -m pruebas.ejecutor
    python -m pruebas.ejecutor pruebas/ejemplos/invalidos
"""
import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, TextIO, Tuple

# Permite ejecutar `python pruebas/ejecutor.py` además de `python -m pruebas.ejecutor`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lexer.lexer import analizar as analizar_lexico
from parser.convertidor import tokens_a_ast
from semantico.semantico import analizar as analizar_semantico

RAIZ_REPO = Path(__file__).resolve().parent.parent
CARPETA_CORPUS_DEFECTO = RAIZ_REPO / "pruebas" / "ejemplos"

PATRON_ESPERADO = re.compile(r"^\s*//\s*ESPERADO:\s*(.+?)\s*$")
PATRON_ERROR_ESPERADO = re.compile(
    r"^error\s+(lexico|sintactico|semantico)(?:\s+linea\s+(\d+))?\s*$"
)


def leer_esperado(codigo: str) -> Tuple[str, Optional[int]]:
    """Extrae `(fase_esperada, linea_esperada)` de la primera línea del programa."""
    lineas = codigo.splitlines()
    if not lineas:
        raise ValueError("El archivo está vacío; falta '// ESPERADO: ...'")
    coincidencia = PATRON_ESPERADO.match(lineas[0])
    if not coincidencia:
        raise ValueError(f"Falta la directiva '// ESPERADO: ...' en la línea 1: {lineas[0]!r}")
    directiva = coincidencia.group(1).lower()
    if directiva == "ok":
        return "ok", None
    error_match = PATRON_ERROR_ESPERADO.match(directiva)
    if not error_match:
        raise ValueError(f"Directiva ESPERADO no válida: {coincidencia.group(1)!r}")
    fase = error_match.group(1)
    linea = int(error_match.group(2)) if error_match.group(2) is not None else None
    return fase, linea


def ejecutar_programa(codigo: str) -> Tuple[str, List[dict], List[dict]]:
    """Ejecuta lexer -> convertidor -> semántico y devuelve `(fase, errores, avisos)`."""
    tokens, errores_lexicos = analizar_lexico(codigo)
    if errores_lexicos:
        return "lexico", errores_lexicos, []

    ast, errores_sintacticos = tokens_a_ast(tokens)
    if errores_sintacticos or ast is None:
        return "sintactico", errores_sintacticos, []

    _, _, diagnosticos = analizar_semantico(ast)
    errores = [d for d in diagnosticos if not str(d.get("mensaje", "")).startswith("Aviso:")]
    avisos = [d for d in diagnosticos if str(d.get("mensaje", "")).startswith("Aviso:")]
    return ("semantico" if errores else "ok"), errores, avisos


def _diagnostico_valido(diagnostico: dict) -> bool:
    """Verifica que un diagnóstico incluya fase válida, línea >= 1 y causa."""
    return (
        diagnostico.get("fase") in ("lexico", "sintactico", "semantico")
        and isinstance(diagnostico.get("linea"), int)
        and diagnostico["linea"] >= 1
        and bool(str(diagnostico.get("mensaje", "")).strip())
    )


def _formatear_esperado(esperado: Tuple[str, Optional[int]]) -> str:
    fase, linea = esperado
    if fase == "ok":
        return "ok"
    return f"error {fase} linea {linea}" if linea is not None else f"error {fase}"


def _formatear_error(error: dict) -> str:
    return f"{error.get('fase')} línea {error.get('linea')}: {error.get('mensaje')}"


def evaluar_programa(codigo: str) -> dict:
    """Evalúa un programa `.c` frente a su `// ESPERADO:` y valida línea y causa."""
    try:
        esperado = leer_esperado(codigo)
    except ValueError as exc:
        return {
            "ok": False,
            "esperado": None,
            "fase": "invalido",
            "errores": [],
            "avisos": [],
            "detalle": str(exc),
        }

    fase_obtenida, errores, avisos = ejecutar_programa(codigo)
    diagnosticos_invalidos = [d for d in (*errores, *avisos) if not _diagnostico_valido(d)]
    if diagnosticos_invalidos:
        return {
            "ok": False,
            "esperado": esperado,
            "fase": fase_obtenida,
            "errores": errores,
            "avisos": avisos,
            "detalle": f"Diagnóstico sin línea o causa válida: {diagnosticos_invalidos[0]}",
        }

    fase_esperada, linea_esperada = esperado
    if fase_esperada == "ok":
        if not errores:
            detalle = "ok"
            if avisos:
                resumen_avisos = "; ".join(
                    f"línea {a['linea']}: {a['mensaje']}" for a in avisos
                )
                detalle = f"ok ({len(avisos)} aviso(s): {resumen_avisos})"
            return {
                "ok": True,
                "esperado": esperado,
                "fase": fase_obtenida,
                "errores": errores,
                "avisos": avisos,
                "detalle": detalle,
            }
        return {
            "ok": False,
            "esperado": esperado,
            "fase": fase_obtenida,
            "errores": errores,
            "avisos": avisos,
            "detalle": f"se esperaba ok, pero ocurrió {_formatear_error(errores[0])}",
        }

    if not errores:
        return {
            "ok": False,
            "esperado": esperado,
            "fase": fase_obtenida,
            "errores": errores,
            "avisos": avisos,
            "detalle": f"se esperaba {_formatear_esperado(esperado)}, pero pasó sin errores",
        }

    primer_error = errores[0]
    coincide_fase = primer_error["fase"] == fase_esperada
    coincide_linea = linea_esperada is None or primer_error["linea"] == linea_esperada
    if coincide_fase and coincide_linea:
        extra = f" (+{len(errores) - 1} más)" if len(errores) > 1 else ""
        return {
            "ok": True,
            "esperado": esperado,
            "fase": fase_obtenida,
            "errores": errores,
            "avisos": avisos,
            "detalle": f"{_formatear_error(primer_error)}{extra}",
        }

    return {
        "ok": False,
        "esperado": esperado,
        "fase": fase_obtenida,
        "errores": errores,
        "avisos": avisos,
        "detalle": (
            f"se esperaba {_formatear_esperado(esperado)}, "
            f"pero ocurrió {_formatear_error(primer_error)}"
        ),
    }


def buscar_programas(ruta: Path) -> List[Path]:
    """Devuelve los archivos `.c` encontrados en un archivo o directorio, ordenados."""
    if ruta.is_file():
        return [ruta]
    if ruta.is_dir():
        return sorted(ruta.rglob("*.c"))
    raise FileNotFoundError(f"No existe la ruta: {ruta}")


def _nombre_mostrar(programa: Path, base: Path) -> str:
    try:
        return str(programa.relative_to(base))
    except ValueError:
        return str(programa)


def ejecutar_corpus(ruta: Path = CARPETA_CORPUS_DEFECTO,
                    salida: Optional[TextIO] = None) -> Tuple[int, int, List[dict]]:
    """Ejecuta el corpus completo, imprime el detalle y devuelve `(correctos, fallidos, resultados)`."""
    flujo = salida if salida is not None else sys.stdout
    programas = buscar_programas(ruta)
    base = ruta if ruta.is_dir() else ruta.parent

    correctos = 0
    fallidos = 0
    total_avisos = 0
    resultados: List[dict] = []

    for programa in programas:
        codigo = programa.read_text(encoding="utf-8-sig")
        resultado = evaluar_programa(codigo)
        resultado["archivo"] = str(programa)
        resultados.append(resultado)

        etiqueta = "[OK]   " if resultado["ok"] else "[FALLO]"
        nombre = _nombre_mostrar(programa, base)
        print(f"{etiqueta} {nombre:<45} -> {resultado['detalle']}", file=flujo)

        if resultado["ok"]:
            correctos += 1
        else:
            fallidos += 1
        total_avisos += len(resultado["avisos"])

    total = correctos + fallidos
    etiqueta_avisos = "aviso S9" if total_avisos == 1 else "avisos S9"
    print(
        f"\nResumen: {correctos} correctos, {fallidos} fallidos "
        f"de {total} programas ({total_avisos} {etiqueta_avisos}).",
        file=flujo,
    )
    return correctos, fallidos, resultados


def main(argv: Optional[List[str]] = None) -> int:
    """Punto de entrada CLI del ejecutor del corpus."""
    parser = argparse.ArgumentParser(
        description="Ejecuta el corpus de pruebas de mini-C y verifica '// ESPERADO:'."
    )
    parser.add_argument(
        "ruta",
        nargs="?",
        default=str(CARPETA_CORPUS_DEFECTO),
        help="archivo .c o carpeta con el corpus (por defecto: pruebas/ejemplos)",
    )
    args = parser.parse_args(argv)
    ruta = Path(args.ruta)

    try:
        correctos, fallidos, resultados = ejecutar_corpus(ruta)
    except (FileNotFoundError, OSError, UnicodeError) as error:
        print(f"ERROR de entrada: {error}", file=sys.stderr)
        return 2

    if not resultados:
        print(f"ERROR: no se encontraron archivos .c en {ruta}", file=sys.stderr)
        return 2

    return 0 if fallidos == 0 and correctos > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
