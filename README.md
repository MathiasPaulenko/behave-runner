# behave-runner

> CLI completa para Behave con subcomandos.

<!-- markdownlint-disable MD013 -->
[![CI](https://github.com/MathiasPaulenko/behave-runner/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-runner/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/behave-runner)](https://pypi.org/project/behave-runner/)
[![Python](https://img.shields.io/pypi/pyversions/behave-runner)](https://pypi.org/project/behave-runner/)
[![Coverage](https://codecov.io/gh/MathiasPaulenko/behave-runner/branch/main/graph/badge.svg)](https://codecov.io/gh/MathiasPaulenko/behave-runner)
<!-- markdownlint-enable MD013 -->

## Features

- CLI unificada para ejecutar, listar, filtrar y gestionar escenarios Behave.
- Soporte de ejecución en paralelo, sharding, prioridad y reintentos.
- Perfiles de configuración en `pyproject.toml` o `behave.ini`.
- Modo *watch* para re-ejecutar tests automáticamente al cambiar archivos.
- Reportes en consola, HTML, Markdown, JSON, XLSX y PDF.
- Trace viewer y UI web para depuración.
- Gestión de step libraries, generación de features y grabación de navegador.
- Análisis de impacto para detectar escenarios afectados por cambios de código.
- Degradación graceful: si falta una extra opcional, el comando sigue funcionando.

## Installation

```bash
pip install behave-runner
pip install "behave-runner[all]"  # con todas las extras
```

Para desarrollo:

```bash
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

```bash
behave-runner init
behave-runner run
behave-runner list
behave-runner watch
```

## Commands

| Command | Description |
| --- | --- |
| `run` | Ejecutar tests de Behave. |
| `watch` | Re-ejecutar tests al detectar cambios. |
| `list` | Listar escenarios sin ejecutarlos. |
| `select` | Filtrar escenarios por tags, regex o nombre. |
| `lint` | Lint de archivos `.feature`. |
| `format` | Formatear archivos `.feature`. |
| `doctor` | Diagnóstico de salud del proyecto. |
| `init` | Inicializar un proyecto Behave. |
| `generate` | Generar steps o features. |
| `record` | Grabar sesión de navegador y generar steps. |
| `report` | Generar y abrir reportes. |
| `trace` | Ver trace viewer o servir dashboard. |
| `steps` | Gestionar step libraries. |
| `impact` | Detectar escenarios afectados por cambios. |
| `open` | Abrir el último reporte o trace en el navegador. |
| `config` | Gestionar la configuración. |

## Documentation

La documentación completa está en:

<https://mathiaspaulenko.github.io/behave-runner/>

## Links

- **Repositorio**: <https://github.com/MathiasPaulenko/behave-runner>
- **Issues**: <https://github.com/MathiasPaulenko/behave-runner/issues>
- **Discussions**: <https://github.com/MathiasPaulenko/behave-runner/discussions>
- **PyPI**: <https://pypi.org/project/behave-runner/>

## License

MIT
