from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from git_health.fs import exists_any, file_contains, glob_any
from git_health.models import CheckResult, Severity

Predicate = Callable[[Path], bool]


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    category: str
    weight: int
    severity: Severity
    success_message: str
    recommendation: str
    predicate: Predicate

    def evaluate(self, root: Path) -> CheckResult:
        return CheckResult(
            id=self.id,
            title=self.title,
            category=self.category,
            passed=self.predicate(root),
            weight=self.weight,
            severity=self.severity,
            success_message=self.success_message,
            recommendation=self.recommendation,
        )


def default_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            id="readme",
            title="README",
            category="presentation",
            weight=12,
            severity=Severity.CRITICAL,
            success_message="El proyecto tiene README.",
            recommendation="Agrega un README con descripcion, instalacion y ejemplo de uso.",
            predicate=lambda root: exists_any(root, ("README.md", "README.rst", "README.txt")),
        ),
        Rule(
            id="license",
            title="Licencia",
            category="trust",
            weight=10,
            severity=Severity.CRITICAL,
            success_message="El proyecto declara licencia.",
            recommendation="Agrega LICENSE para aclarar como puede usarse el codigo.",
            predicate=lambda root: exists_any(root, ("LICENSE", "LICENSE.md", "COPYING")),
        ),
        Rule(
            id="contributing",
            title="Guia de contribucion",
            category="community",
            weight=8,
            severity=Severity.WARNING,
            success_message="El proyecto explica como contribuir.",
            recommendation="Agrega CONTRIBUTING.md con flujo de fork, ramas, commits y PRs.",
            predicate=lambda root: exists_any(root, ("CONTRIBUTING.md", ".github/CONTRIBUTING.md")),
        ),
        Rule(
            id="pr-template",
            title="Plantilla de PR",
            category="community",
            weight=6,
            severity=Severity.WARNING,
            success_message="El proyecto tiene plantilla de pull request.",
            recommendation="Agrega .github/PULL_REQUEST_TEMPLATE.md con resumen y verificacion.",
            predicate=lambda root: exists_any(root, (".github/PULL_REQUEST_TEMPLATE.md", "PULL_REQUEST_TEMPLATE.md")),
        ),
        Rule(
            id="issue-templates",
            title="Plantillas de issues",
            category="community",
            weight=6,
            severity=Severity.WARNING,
            success_message="El proyecto tiene plantillas de issues.",
            recommendation="Agrega plantillas para bugs, features o propuestas.",
            predicate=lambda root: glob_any(root, ".github/ISSUE_TEMPLATE/*"),
        ),
        Rule(
            id="ci",
            title="Integracion continua",
            category="engineering",
            weight=12,
            severity=Severity.CRITICAL,
            success_message="El proyecto tiene GitHub Actions.",
            recommendation="Agrega un workflow que ejecute tests o validaciones basicas.",
            predicate=lambda root: glob_any(root, ".github/workflows/*.yml")
            or glob_any(root, ".github/workflows/*.yaml"),
        ),
        Rule(
            id="tests",
            title="Tests",
            category="engineering",
            weight=10,
            severity=Severity.CRITICAL,
            success_message="El proyecto tiene tests.",
            recommendation="Agrega tests pequenos para el comportamiento principal.",
            predicate=lambda root: exists_any(root, ("tests", "test")) or glob_any(root, "**/test_*.py"),
        ),
        Rule(
            id="gitignore",
            title="Gitignore",
            category="engineering",
            weight=5,
            severity=Severity.WARNING,
            success_message="El proyecto ignora artefactos locales.",
            recommendation="Agrega .gitignore para caches, entornos virtuales y archivos generados.",
            predicate=lambda root: (root / ".gitignore").exists(),
        ),
        Rule(
            id="security",
            title="Politica de seguridad",
            category="trust",
            weight=5,
            severity=Severity.WARNING,
            success_message="El proyecto tiene politica de seguridad.",
            recommendation="Agrega SECURITY.md con instrucciones para reportar vulnerabilidades.",
            predicate=lambda root: exists_any(root, ("SECURITY.md", ".github/SECURITY.md")),
        ),
        Rule(
            id="citation",
            title="Citacion",
            category="trust",
            weight=4,
            severity=Severity.INFO,
            success_message="El proyecto tiene metadatos de citacion.",
            recommendation="Agrega CITATION.cff si el repo es academico o investigativo.",
            predicate=lambda root: (root / "CITATION.cff").exists(),
        ),
        Rule(
            id="install-docs",
            title="Instalacion documentada",
            category="documentation",
            weight=8,
            severity=Severity.CRITICAL,
            success_message="El README incluye instalacion.",
            recommendation="Agrega una seccion de instalacion con comandos copiables.",
            predicate=lambda root: file_contains(
                root / "README.md",
                ("install", "instalar", "pip install", "npm install", "docker run"),
            ),
        ),
        Rule(
            id="usage-docs",
            title="Uso documentado",
            category="documentation",
            weight=8,
            severity=Severity.CRITICAL,
            success_message="El README incluye ejemplo de uso.",
            recommendation="Agrega un ejemplo minimo de ejecucion y salida esperada.",
            predicate=lambda root: file_contains(
                root / "README.md",
                ("usage", "uso", "quickstart", "ejemplo", "example"),
            ),
        ),
        Rule(
            id="changelog",
            title="Changelog",
            category="maintenance",
            weight=3,
            severity=Severity.INFO,
            success_message="El proyecto documenta cambios.",
            recommendation="Agrega CHANGELOG.md para registrar versiones y mejoras.",
            predicate=lambda root: exists_any(root, ("CHANGELOG.md", "HISTORY.md", "RELEASES.md")),
        ),
        Rule(
            id="sensitive-files",
            title="Archivos sensibles",
            category="security",
            weight=3,
            severity=Severity.CRITICAL,
            success_message="No se detectaron archivos sensibles obvios.",
            recommendation="No subas .env ni llaves privadas; usa .env.example.",
            predicate=lambda root: not exists_any(root, (".env", "id_rsa", "id_ed25519")),
        ),
    )
