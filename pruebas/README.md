# Pruebas

- `ejemplos/validos/` y `ejemplos/invalidos/`: el corpus de programas `.c` en mini-C (11 válidos y 18 inválidos).
- `ejemplos/ast/`: árboles sintácticos (AST) de ejemplo en JSON para probar el semántico directamente.
- Índice completo del corpus en [`ejemplos/INDICE.md`](ejemplos/INDICE.md).

## Pruebas unitarias

Se corren desde la raíz del repositorio con:

```sh
python -m unittest discover pruebas
```

Incluye las pruebas por módulo:
- `test_lexer.py`: reconocimiento de tokens, comentarios, líneas/columnas y errores léxicos.
- `test_ast.py` y `test_convertidor.py`: contrato del AST, precedencia, asociatividad y errores sintácticos.
- `test_semantico.py` y `test_semantico_s9.py`: tabla de símbolos, ámbitos (S8), declaración previa (S1), redeclaración (S2) y avisos de uso sin inicializar (S9).
- `test_tipos.py`: compatibilidad de tipos y reglas S3 a S7 y S10.
- `test_ejecutor.py`: validación del ejecutor del corpus y corrida completa de los 29 programas `.c`.

## Ejecutor del corpus (`ejecutor.py`)

El ejecutor general del corpus recorre los programas `.c` de `pruebas/ejemplos/` ejecutando el flujo completo (`lexer.lexer` → `parser.convertidor` → `semantico.semantico`) y verifica que:

1. La fase y línea del resultado coincidan con la primera línea `// ESPERADO: ...` (`ok`, `error lexico linea N` o `error semantico linea N`).
2. Todo error o aviso reporte una línea válida y una causa no vacía.

Para correrlo desde la raíz del repositorio:

```sh
python -m pruebas.ejecutor
```

Convención completa del corpus en [`docs/contratos.md`](../docs/contratos.md), sección 6. Nombres de archivo del corpus: `NN_descripcion.c` (por ejemplo `08_variable_no_declarada.c`).
