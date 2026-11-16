"""Pruebas del ejecutor general del corpus (P5)."""
import io
import unittest
from pathlib import Path
from unittest.mock import patch

from pruebas.ejecutor import (
    CARPETA_CORPUS_DEFECTO,
    ejecutar_corpus,
    ejecutar_programa,
    evaluar_programa,
    leer_esperado,
    main,
)


class PruebasEjecutor(unittest.TestCase):
    def test_leer_esperado_valido_e_invalido(self):
        self.assertEqual(leer_esperado("// ESPERADO: ok\nint x = 1;"), ("ok", None))
        self.assertEqual(leer_esperado("// ESPERADO: error lexico linea 3\n"), ("lexico", 3))
        self.assertEqual(leer_esperado("// ESPERADO: error semantico linea 12\n"), ("semantico", 12))
        self.assertEqual(leer_esperado("// ESPERADO: error sintactico\n"), ("sintactico", None))

        for codigo in ("", "int x = 1;", "// ESPERADO: advertencia"):
            with self.subTest(codigo=codigo):
                with self.assertRaises(ValueError):
                    leer_esperado(codigo)

    def test_ejecutar_programa_separa_fases_y_avisos(self):
        self.assertEqual(ejecutar_programa("int x = 1 @ 2;")[0], "lexico")
        self.assertEqual(ejecutar_programa("int x = ;")[0], "sintactico")
        self.assertEqual(ejecutar_programa('int x = "hola";')[0], "semantico")

        fase, errores, avisos = ejecutar_programa('int x;\nprintf("%d", x);')
        self.assertEqual(fase, "ok")
        self.assertEqual(errores, [])
        self.assertEqual(len(avisos), 1)
        self.assertTrue(avisos[0]["mensaje"].startswith("Aviso:"))

    def test_evaluar_programa_detecta_coincidencias_y_discrepancias(self):
        ok = evaluar_programa("// ESPERADO: ok\nint x = 1;\n")
        self.assertTrue(ok["ok"])

        aviso_ok = evaluar_programa('// ESPERADO: ok\nint x;\nprintf("%d", x);\n')
        self.assertTrue(aviso_ok["ok"])
        self.assertEqual(len(aviso_ok["avisos"]), 1)

        fallo_inesperado = evaluar_programa("// ESPERADO: ok\nint x = @;\n")
        self.assertFalse(fallo_inesperado["ok"])

        fallo_sin_error = evaluar_programa("// ESPERADO: error semantico linea 2\nint x = 1;\n")
        self.assertFalse(fallo_sin_error["ok"])

        fallo_linea = evaluar_programa('// ESPERADO: error semantico linea 9\nint x = "a";\n')
        self.assertFalse(fallo_linea["ok"])

        fallo_fase = evaluar_programa('// ESPERADO: error lexico linea 2\nint x = "a";\n')
        self.assertFalse(fallo_fase["ok"])

    def test_evaluar_programa_exige_linea_y_causa(self):
        error_sin_causa = (
            "semantico",
            [{"fase": "semantico", "linea": 2, "columna": 1, "mensaje": "   "}],
            [],
        )
        with patch("pruebas.ejecutor.ejecutar_programa", return_value=error_sin_causa):
            resultado = evaluar_programa("// ESPERADO: error semantico linea 2\nint x = 1;\n")
        self.assertFalse(resultado["ok"])
        self.assertIn("línea o causa", resultado["detalle"])

    def test_corpus_completo_pasa_sin_fallos(self):
        buffer = io.StringIO()
        correctos, fallidos, resultados = ejecutar_corpus(CARPETA_CORPUS_DEFECTO, salida=buffer)
        self.assertEqual(fallidos, 0, buffer.getvalue())
        self.assertGreaterEqual(correctos, 29)
        self.assertEqual(len(resultados), correctos)

    def test_cli_devuelve_cero_para_el_corpus_y_dos_si_falta_ruta(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main([]), 0)
        with patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(main([str(Path("ruta_que_no_existe"))]), 2)


if __name__ == "__main__":
    unittest.main()
