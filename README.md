# Compilador de mini-C: lexer y analizador semántico

Proyecto TLP02-2026 (Teoría de Lenguajes de Programación). La **Fase 1** consiste en un **analizador léxico**
y un **analizador semántico** para un subconjunto de **C** (mini-C). El parser para el español es de la Fase 2.

```
int total = base @ 2;        ->   ERROR línea 4, col 18: Carácter inválido '@'     (lo detecta el lexer)
int n = "hola";              ->   error semántico: no se puede guardar una cadena en un int
```

## Equipo

| Rol | Nombre | Módulo |
|---|---|---|
| P1 | Juan Carlos Sibrian | Analizador léxico, especificación de tokens y corpus de pruebas |
| P2 | Kattia Sarai Santan Soriano | Representación mínima (AST) para el semántico y reflexión sobre CFG |
| P3 | Fabio Mijango | Analizador semántico: tabla de símbolos, ámbitos, declaración y redeclaración |
| P4 | Gabriela Sofia Quinteros Ramirez | Reglas de tipos y casos de prueba semánticos |
| P5 | Oscar Ernesto Menjivar Ayala | Ejecutor de pruebas, README, video y entrega |

## El lenguaje

Un subconjunto de C: tipos `int`, `float` y `char`; declaraciones y asignaciones; aritmética; comparaciones;
operadores lógicos `&&` `||` `!`; `if/else`, `while`, bloques con ámbito; `printf`; y comentarios `//` y `/* */`.
Un programa es una secuencia de sentencias (sin `main` ni funciones propias). El detalle y las reglas semánticas
(S1 a S10) están en [docs/lenguaje_c.md](docs/lenguaje_c.md).

## Estructura del repositorio

```
ProyectoTLP2026/
├── lexer/          lexer.py: analizador léxico (P1)
├── semantico/      semantico.py, tabla_simbolos.py y tipos.py: analizador semántico, tabla de símbolos y reglas de tipos (P3 y P4)
├── parser/         nodo.py (AST mínimo) y convertidor.py (tokens a AST) que consume el semántico (P2)
├── pruebas/        ejecutor.py, pruebas unitarias (test_*.py) y el corpus de programas .c (ejemplos/validos, ejemplos/invalidos, ejemplos/ast)
├── docs/           especificación de tokens, lenguaje mini-C y contratos entre módulos
├── CONTRIBUTING.md     cómo trabajamos con Git (leer antes de empezar)
└── README.md
```

## Cómo ejecutar

Requisitos: Python 3.10 o superior. No hay dependencias externas en la Fase 1.
Todos los comandos se corren desde la raíz del repositorio.

```sh
# Analizador léxico: imprime los tokens y los errores léxicos, y crea salida/tokens.txt y salida/errores.txt
python -m lexer.lexer pruebas/ejemplos/validos/ejemplo.c

# AST de un programa (lo que recibe el semántico): imprime el árbol en JSON
python -m parser.convertidor pruebas/ejemplos/validos/ejemplo.c

# Analizador semántico (P3 y P4): nombres, redeclaraciones, ámbitos y reglas de tipos
python -m semantico.semantico pruebas/ejemplos/validos/07_ambitos_y_bloques.c
python -m semantico.semantico pruebas/ejemplos/invalidos/09_redeclaracion.c
python -m semantico.semantico pruebas/ejemplos/invalidos/15_variable_fuera_de_su_ambito.c
python -m semantico.semantico pruebas/ejemplos/invalidos/10_cadena_en_entero.c
python -m semantico.semantico pruebas/ejemplos/invalidos/11_float_en_int.c
python -m semantico.semantico pruebas/ejemplos/invalidos/16_modulo_con_float.c
python -m semantico.semantico pruebas/ejemplos/ast/08_variable_no_declarada.json

# Ejecutor general del corpus: corre los 29 programas .c de extremo a extremo y verifica // ESPERADO
python -m pruebas.ejecutor

# Suite completa de pruebas unitarias (lexer, AST, convertidor, semántico, tipos y ejecutor)
python -m unittest discover pruebas
```

## Casos de prueba

El corpus está en `pruebas/ejemplos/`: programas **válidos** que deben analizarse sin errores e **inválidos** que
deben producir errores léxicos o semánticos claros, con línea y causa. La primera línea de cada programa declara lo
esperado (`// ESPERADO: ok`, `// ESPERADO: error lexico linea 4`, `// ESPERADO: error semantico linea 3`). El ejecutor
(`python -m pruebas.ejecutor`) verifica todos los casos automáticamente y el índice completo está en
[pruebas/ejemplos/INDICE.md](pruebas/ejemplos/INDICE.md).

## Estado de los módulos

| Módulo | Responsable | Estado |
|---|---|---|
| Léxico y especificación de tokens | P1 | Listo |
| Corpus de pruebas | P1 | Listo |
| AST mínimo y convertidor de tokens a AST | P2 | Listo |
| Semántico: tabla de símbolos y ámbitos | P3 | Listo |
| Semántico: reglas de tipos | P4 | Listo |
| Ejecutor de pruebas y README | P5 | Listo |
| Video de la Fase 1 y entrega | P5 | Pendiente |

(Actualizar esta tabla al unir cada módulo a `main`: Pendiente, En curso, Listo.)

## Reflexión: qué verificaciones no puede expresar una CFG

Una gramática libre de contexto (tipo 2 en la jerarquía de Chomsky) solo describe **en qué orden** pueden aparecer los símbolos de un programa. Sus producciones tienen la forma `A → γ`: el no terminal de la izquierda se reemplaza sin importar qué lo rodea, y la gramática no guarda memoria de lo que ya vio. Por eso sirve para la estructura (sentencias, expresiones, bloques), pero no para reglas que dependen de información que aparece en otra parte del programa.

**1. Declarar antes de usar (S1).** La regla "toda variable usada debe haber sido declarada" exige recordar el conjunto de nombres declarados y compararlo con cada uso. Es la misma situación del lenguaje clásico `{ w c w }`: la segunda `w` debe repetir la primera, y ese lenguaje no es libre de contexto (se demuestra con el lema de bombeo). La gramática acepta `total = a + 1;` con cualquier identificador, exista o no. Ejemplo: [`08_variable_no_declarada.c`](pruebas/ejemplos/invalidos/08_variable_no_declarada.c).

**2. No redeclarar en el mismo ámbito (S2, S8).** Además de recordar nombres, hay que saber en qué bloque estamos y qué se declaró en él. `int a = 1; int a = 2;` tiene una estructura perfectamente válida para la gramática, y lo declarado dentro de un bloque `{ }` no existe fuera de él. Ejemplos: [`09_redeclaracion.c`](pruebas/ejemplos/invalidos/09_redeclaracion.c) y [`15_variable_fuera_de_su_ambito.c`](pruebas/ejemplos/invalidos/15_variable_fuera_de_su_ambito.c).

**3. Compatibilidad de tipos (S3 a S7).** La gramática acepta la forma `tipo ID = expresión;`, pero no sabe que `"hola"` es una cadena y que el destino es un `int`. Para eso hay que calcular el tipo de cada expresión y compararlo con el del destino. Ejemplo: [`10_cadena_en_entero.c`](pruebas/ejemplos/invalidos/10_cadena_en_entero.c).

En los tres casos el programa es **sintácticamente correcto**: la gramática lo acepta y el analizador semántico lo rechaza, con línea y causa.

**Conclusión.** Estas verificaciones se hacen en el analizador semántico con una **tabla de símbolos**, que funciona como la memoria que a la CFG le falta. Esto conecta con los lenguajes sensibles al contexto (tipo 1), cuyas reglas pueden depender del contexto en que aparece cada símbolo. Un compilador reparte así el trabajo entre los niveles de la jerarquía: lenguajes regulares para el lexer, libres de contexto para el parser y verificaciones sensibles al contexto en la fase semántica.

Esa frontera es la que se retoma en la Fase 2: en el español, la concordancia de género y número a distancia es otra dependencia de contexto que una CFG no puede expresar.

## Video de la Fase 1

_Enlace pendiente (máximo 10 minutos; lo sube P5)._

## Documentación

- [Especificación formal de tokens](docs/tokens.md): expresiones regulares de cada token y errores léxicos.
- [El lenguaje mini-C](docs/lenguaje_c.md): alcance y reglas semánticas S1 a S10.
- [Contratos entre módulos](docs/contratos.md): formatos de token, error, AST, tabla de símbolos y funciones.