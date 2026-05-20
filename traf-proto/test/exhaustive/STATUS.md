# test/exhaustive — estado de trabajo

Test exhaustivo que enumera todas las queries sintácticamente válidas hasta
cierta profundidad y las corre contra Postgres, comparando con el interpreter.
Espejo no-aleatorio de la gramática de `interpreter/queryGenerator.py`, sin
agregaciones.

## Archivos

- `__init__.py` — vacío.
- `enumerate.py` — enumerador lazy con cap duro global. Incluye subcomando
  `dump <preset> <path>` que vuelca el corpus a JSONL. **Listo.**
- `corpus/<preset>.jsonl` — corpus generado, commiteado al repo. Regenerar con
  `python -m test.exhaustive.enumerate dump <preset> test/exhaustive/corpus/<preset>.jsonl`.
- `conftest.py` — fixture de conexión a la bd `interpreter`. `infer_schema`
  uppercasea keys y trae todas las tablas de `public`; el conftest filtra a
  `ta/tb/tc` y lowercasea para alinear con el enumerador. **Listo.**
- `test_exhaustive_postgres.py` — test parametrizado en collection-time desde
  el archivo JSONL. Path configurable por `EXHAUSTIVE_QUERIES_FILE`, default
  `corpus/floor.jsonl`. Pipeline espejo de Calcite: parse (skip si Lark falla)
  → typecheck → run interpreter + run Postgres → `Engine().Compare`. **Listo.**

## Gramática del enumerador (sin agregaciones)

```
Query ::= SELECT Cols FROM From [WHERE Comp]
        | Query UNION Query | Query EXCEPT Query | Query INTERSECT Query
From  ::= tabla alias | From "," From | "(" Query ")" alias
Cols  ::= Expr AS colN (, Expr AS colN)*
Expr  ::= tabla.col | literal | "(" Expr "+" Expr ")" | CAST(Expr AS tipo)
Comp  ::= Expr "<" Expr | Expr "=" Expr | "(" Expr "IS NULL" ")"
        | Expr IN (Query) | EXISTS (Query)
        | "(" Comp AND Comp ")" | "(" Comp OR Comp ")"
```

## Diseño anti-OOM

El enumerador explota cuadráticamente en `Expr < Expr`, `AND/OR`, cross-product
de FROMs. Decisiones para no romper la máquina:

- **Todos los niveles son generators** (`yield`), nunca se materializa la lista
  completa del producto cartesiano.
- **Cap duro global** `Budgets.max_queries` aplicado con `itertools.islice`.
  Aunque los budgets internos pidan 64M, el cap corta.
- **Defaults conservadores**: `max_expr_depth=0, max_comp_depth=0,
  max_sub_depth=0, max_set_depth=0, max_from_tables=1, max_cols=1,
  max_queries=2000`. Eso da queries del tipo `SELECT c FROM t` /
  `SELECT c FROM t WHERE c op lit`.
- **Literales acotados**: `('1', "'a'", 'NULL')` — uno por tipo.
- **Cast types acotados**: `('DECIMAL(10,1)',)` — uno por default.

## Correr

```bash
# Regenerar corpus (opcional — ya commiteado):
python -m test.exhaustive.enumerate dump floor  test/exhaustive/corpus/floor.jsonl
python -m test.exhaustive.enumerate dump small  test/exhaustive/corpus/small.jsonl
python -m test.exhaustive.enumerate dump medium test/exhaustive/corpus/medium.jsonl

# Correr el test (usa floor por default):
python -m pytest test/exhaustive/

# Con otro corpus:
EXHAUSTIVE_QUERIES_FILE=test/exhaustive/corpus/medium.jsonl python -m pytest test/exhaustive/
```

## Estado

`floor` (200 queries): 200 passed en ~15s.

## Próximos pasos

- Generar `small.jsonl` / `medium.jsonl` y correrlos; esperar primeros
  mismatches — dependen de optimizaciones del planner PSQL (ver `PROBLEMS.md`
  §6.3).
- Si el count se vuelve caro, bajar literales / columnas / tablas base o subir
  `max_queries` con cuidado.

## Base de datos

Postgres local, bd `interpreter` (no `traf_spider` ni `traf_calcite`). Tablas
ya existentes en `public`:

| Tabla | Columnas                                   | Tipos                    | Filas |
|-------|--------------------------------------------|--------------------------|-------|
| ta    | name, height, age                          | varchar, numeric, int    | 5     |
| tb    | realage, fullname, fullheight              | int, varchar, numeric    | 5     |
| tc    | newage, newheight, newname                 | int, numeric, varchar    | 5     |
