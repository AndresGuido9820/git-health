# git-health

[![CI](https://github.com/AndresGuido9820/git-health/actions/workflows/ci.yml/badge.svg)](https://github.com/AndresGuido9820/git-health/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)

CLI para auditar la salud open source de repositorios Git.

`git-health` revisa si un proyecto tiene los archivos y senales basicas que hacen que un repositorio sea confiable, mantenible y facil de contribuir: README, licencia, CI, tests, plantillas de issues, plantilla de PR, guia de contribucion y mas.

## Por que existe

Muchos repositorios tienen buen codigo, pero son dificiles de evaluar, instalar o contribuir porque les faltan piezas basicas de mantenimiento. `git-health` convierte esas senales en un checklist accionable con score y recomendaciones.

## Instalacion

Desde el repositorio local:

```bash
pip install -e .
```

## Uso

Escanear el repositorio actual:

```bash
git-health scan .
```

Escanear otro proyecto:

```bash
git-health scan ../mi-proyecto
```

Salida JSON para CI, bots o dashboards:

```bash
git-health scan . --format json
```

Salida esperada en texto:

```txt
Git Health Score: 7.6/10
Repo: /home/user/project

OK   README                 El proyecto tiene README.
WARN Contribucion           Agrega CONTRIBUTING.md con flujo de fork, ramas, commits y PRs.
OK   CI                     El proyecto tiene GitHub Actions.

Recommended next steps:
1. Agrega CONTRIBUTING.md con flujo de fork, ramas, commits y PRs.
```

Forma de la salida JSON (recortada):

```json
{
  "root": "/home/user/project",
  "score": 7.6,
  "summary": {"total": 14, "passed": 11, "failed": 3},
  "checks": [
    {
      "id": "readme",
      "title": "README",
      "category": "presentation",
      "passed": true,
      "weight": 12,
      "severity": "critical",
      "message": "El proyecto tiene README.",
      "recommendation": "Agrega un README con descripcion, instalacion y ejemplo de uso."
    }
  ]
}
```

## Checks iniciales

- README
- LICENSE
- CONTRIBUTING.md
- Plantilla de pull request
- Plantillas de issues
- GitHub Actions
- Tests
- .gitignore
- SECURITY.md
- CITATION.cff
- Seccion de instalacion en README
- Ejemplo de uso en README
- CHANGELOG.md
- Archivos sensibles obvios

## Arquitectura

```txt
src/git_health/
├── cli.py        # interfaz de comandos
├── fs.py         # helpers seguros de filesystem
├── models.py     # objetos de dominio
├── reporters.py  # salida texto y JSON
├── rules.py      # catalogo de reglas
└── scanner.py    # orquestacion del analisis
```

La CLI no conoce los detalles de cada regla. Las reglas producen resultados de dominio y los reporters deciden como presentarlos. Esto permite agregar salida JSON, nuevos comandos o reglas por lenguaje sin reescribir el nucleo.

## Desarrollo

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## Roadmap

- Comando `git-health fix` para crear plantillas faltantes.
- Checks especificos para Python, Node y notebooks.
- Integracion con GitHub API para leer topics, descripcion y releases.

## Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) para configurar el entorno local y proponer cambios.
