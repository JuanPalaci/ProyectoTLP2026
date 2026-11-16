# Analizador léxico y semántico de mini-C

Proyecto de Teoría de Lenguajes de Programación (TLP02-2026), Fase 1: analizador léxico y analizador semántico para un subconjunto de C (**mini-C**).

```text
int total = base @ 2;        ->   ERROR línea 4, col 18: Carácter inválido '@'     (fase léxica)
int n = "hola";              ->   ERROR semantico línea 3, col 1: No se puede asignar un cadena a una variable int
```

## Integrantes

| Nombre | Área |
|---|---|
| Juan Carlos Sibrian | Analizador léxico, especificación de tokens y corpus de pruebas |
| Kattia Sarai Santan Soriano | Representación AST y convertidor de tokens a AST |
| Fabio Mijango | Analizador semántico, tabla de símbolos y manejo de ámbitos |
| Gabriela Sofia Quinteros Ramirez | Reglas de tipos y casos de prueba semánticos |
| Oscar Ernesto Menjivar Ayala | Ejecutor de pruebas e integración |

## El lenguaje

Mini-C cubre un subconjunto de C con tipos `int`, `float` y `char`; declaraciones con o sin valor inicial; asignaciones; operadores aritméticos (`+`, `-`, `*`, `/`, `%`), relacionales (`<`, `>`, `<=`, `>=`, `==`, `!=`) y lógicos (`&&`, `||`, `!`); estructuras `if`/`else` y `while`; bloques con ámbito propio `{ ... }`; `printf`; y comentarios `//` y `/* */`. Un programa es una secuencia de sentencias (sin `main` ni funciones definidas por el usuario).

El detalle del lenguaje, las reglas semánticas (S1 a S10) y la especificación formal de tokens están en [docs/lenguaje_c.md](docs/lenguaje_c.md) y [docs/tokens.md](docs/tokens.md).

## Estructura del repositorio

```text
ProyectoTLP2026/
├── lexer/          analizador léxico (lexer.py) y ejemplo de salida JSON
├── parser/         representación AST (nodo.py) y convertidor de tokens a AST (convertidor.py)
├── semantico/      analizador semántico (semantico.py), tabla de símbolos y reglas de tipos
├── pruebas/        ejecutor del corpus (ejecutor.py), pruebas unitarias y programas .c de ejemplo
├── docs/           especificación formal de tokens, definición de mini-C y contratos
├── CONTRIBUTING.md guía de estilo y flujo de trabajo en Git
└── README.md
```

## Cómo ejecutar

Requisitos: **Python 3.10** o superior (sin dependencias externas). Todos los comandos se ejecutan desde la raíz del repositorio.

```sh
# 1. Analizador léxico: imprime los tokens y errores léxicos, y genera salida/tokens.txt y salida/errores.txt
python -m lexer.lexer pruebas/ejemplos/validos/ejemplo.c

# 2. Convertidor de tokens a AST: imprime el árbol sintáctico en formato JSON
python -m parser.convertidor pruebas/ejemplos/validos/ejemplo.c

# 3. Analizador semántico: recibe un .c o un AST en JSON; verifica ámbitos, declaraciones y tipos
python -m semantico.semantico pruebas/ejemplos/validos/07_ambitos_y_bloques.c
python -m semantico.semantico pruebas/ejemplos/invalidos/09_redeclaracion.c
python -m semantico.semantico pruebas/ejemplos/invalidos/15_variable_fuera_de_su_ambito.c
python -m semantico.semantico pruebas/ejemplos/invalidos/10_cadena_en_entero.c
python -m semantico.semantico pruebas/ejemplos/invalidos/11_float_en_int.c
python -m semantico.semantico pruebas/ejemplos/invalidos/16_modulo_con_float.c
python -m semantico.semantico pruebas/ejemplos/ast/08_variable_no_declarada.json

# 4. Ejecutor del corpus: corre los 29 programas .c de extremo a extremo y valida // ESPERADO
python -m pruebas.ejecutor

# 5. Suite completa de pruebas unitarias
python -m unittest discover pruebas
```

## Casos de prueba

El corpus de pruebas se encuentra en `pruebas/ejemplos/` y consta de 11 programas **válidos** (`validos/`) y 18 **inválidos** (`invalidos/`) con errores léxicos o semánticos que indican línea y causa, además de AST de referencia en `pruebas/ejemplos/ast/`. La primera línea de cada archivo `.c` declara el resultado esperado (`// ESPERADO: ok`, `// ESPERADO: error lexico linea N` o `// ESPERADO: error semantico linea N`). El índice completo se consulta en [pruebas/ejemplos/INDICE.md](pruebas/ejemplos/INDICE.md).

## Reflexión: qué verificaciones no puede expresar una CFG

Una gramática libre de contexto (tipo 2 en la jerarquía de Chomsky) solo describe **en qué orden** pueden aparecer los símbolos de un programa. Sus producciones tienen la forma `A → γ`: el no terminal de la izquierda se reemplaza sin importar qué lo rodea, y la gramática no guarda memoria de lo que ya vio. Por eso sirve para la estructura (sentencias, expresiones, bloques), pero no para reglas que dependen de información que aparece en otra parte del programa.

**1. Declarar antes de usar (S1).** La regla "toda variable usada debe haber sido declarada" exige recordar el conjunto de nombres declarados y compararlo con cada uso. Es la misma situación del lenguaje clásico `{ w c w }`: la segunda `w` debe repetir la primera, y ese lenguaje no es libre de contexto (se demuestra con el lema de bombeo). La gramática acepta `total = a + 1;` con cualquier identificador, exista o no. Ejemplo: [`08_variable_no_declarada.c`](pruebas/ejemplos/invalidos/08_variable_no_declarada.c).

**2. No redeclarar en el mismo ámbito (S2, S8).** Además de recordar nombres, hay que saber en qué bloque estamos y qué se declaró en él. `int a = 1; int a = 2;` tiene una estructura perfectamente válida para la gramática, y lo declarado dentro de un bloque `{ }` no existe fuera de él. Ejemplos: [`09_redeclaracion.c`](pruebas/ejemplos/invalidos/09_redeclaracion.c) y [`15_variable_fuera_de_su_ambito.c`](pruebas/ejemplos/invalidos/15_variable_fuera_de_su_ambito.c).

**3. Compatibilidad de tipos (S3 a S7).** La gramática acepta la forma `tipo ID = expresión;`, pero no sabe que `"hola"` es una cadena y que el destino es un `int`. Para eso hay que calcular el tipo de cada expresión y compararlo con el del destino. Ejemplo: [`10_cadena_en_entero.c`](pruebas/ejemplos/invalidos/10_cadena_en_entero.c).

En los tres casos el programa es **sintácticamente correcto**: la gramática lo acepta y el analizador semántico lo rechaza, con línea y causa.

**Conclusión.** Estas verificaciones se hacen en el analizador semántico con una **tabla de símbolos**, que funciona como la memoria que a la CFG le falta. Esto conecta con los lenguajes sensibles al contexto (tipo 1), cuyas reglas pueden depender del contexto en que aparece cada símbolo. Un compilador reparte así el trabajo entre los niveles de la jerarquía: lenguajes regulares para el lexer, libres de contexto para el parser y verificaciones sensibles al contexto en la fase semántica.

Esa frontera es la que se retoma en la Fase 2: en el español, la concordancia de género y número a distancia es otra dependencia de contexto que una CFG no puede expresar.

## Documentación

- [Especificación formal de tokens](docs/tokens.md): expresiones regulares, autómata numérico y errores léxicos.
- [El lenguaje mini-C](docs/lenguaje_c.md): alcance del lenguaje y reglas semánticas S1 a S10.
- [Contratos entre módulos](docs/contratos.md): formatos de token, error, AST, tabla de símbolos y funciones públicas.
