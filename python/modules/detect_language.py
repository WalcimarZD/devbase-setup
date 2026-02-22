"""
DevBase Detect Language Module
================================================================
PROPÓSITO:
    Detecta a linguagem de programação e stack de um projeto
    analisando arquivos indicadores (package.json, pyproject.toml, etc.).

    Equivalente Python do módulo detect-language.ps1.

STACKS DETECTADOS:
    • Node.js / TypeScript - package.json
    • Python              - requirements.txt, pyproject.toml
    • .NET                - *.csproj
    • Go                  - go.mod
    • Rust                - Cargo.toml
    • Java/Kotlin         - pom.xml, build.gradle

RETORNO:
    Um dicionário com:
    - type: Identificador do stack (node, python, dotnet, go, generic)
    - name: Nome legível do stack
    - package_manager: Gerenciador de pacotes (npm, pip, nuget, etc.)
    - ci_template: Template de CI recomendado

Autor: DevBase Team
Versão: 3.2.0
"""

from pathlib import Path
from typing import TypedDict, Optional


class ProjectStack(TypedDict):
    """Tipo para informações do stack de um projeto."""
    type: str
    name: str
    package_manager: Optional[str]
    ci_template: str


def get_project_stack(path: Path) -> ProjectStack:
    """
    Detecta a linguagem de programação e stack de um projeto.

    Analisa arquivos indicadores no diretório para determinar
    qual stack tecnológico está sendo usado.

    Args:
        path: Caminho do diretório do projeto a analisar.

    Returns:
        ProjectStack: Dicionário com informações do stack detectado.

    Example:
        >>> stack = get_project_stack(Path("./my-project"))
        >>> print(stack["name"])  # "Node.js"
        >>> print(stack["package_manager"])  # "npm"
    """
    # Stack padrão (genérico)
    stack: ProjectStack = {
        "type": "generic",
        "name": "Unknown",
        "package_manager": None,
        "ci_template": "ci-generic.yml.template"
    }

    if not path.exists():
        return stack

    # ================================================
    # 1. Node.js / TypeScript
    # ================================================
    package_json = path / "package.json"
    if package_json.exists():
        stack["type"] = "node"
        stack["name"] = "Node.js"
        stack["ci_template"] = "ci-node.yml.template"

        # Detecta package manager
        if (path / "pnpm-lock.yaml").exists():
            stack["package_manager"] = "pnpm"
        elif (path / "yarn.lock").exists():
            stack["package_manager"] = "yarn"
        elif (path / "bun.lockb").exists():
            stack["package_manager"] = "bun"
        else:
            stack["package_manager"] = "npm"

        # Verifica se é TypeScript
        if (path / "tsconfig.json").exists():
            stack["name"] = "TypeScript"

        return stack

    # ================================================
    # 2. Python
    # ================================================
    has_requirements = (path / "requirements.txt").exists()
    has_pyproject = (path / "pyproject.toml").exists()
    has_setup_py = (path / "setup.py").exists()

    if has_requirements or has_pyproject or has_setup_py:
        stack["type"] = "python"
        stack["name"] = "Python"
        stack["ci_template"] = "ci-python.yml.template"

        # Detecta package manager
        if (path / "poetry.lock").exists():
            stack["package_manager"] = "poetry"
        elif (path / "Pipfile.lock").exists():
            stack["package_manager"] = "pipenv"
        elif (path / "pdm.lock").exists():
            stack["package_manager"] = "pdm"
        elif (path / "uv.lock").exists():
            stack["package_manager"] = "uv"
        else:
            stack["package_manager"] = "pip"

        return stack

    # ================================================
    # 3. .NET (C#, F#, VB.NET)
    # ================================================
    csproj_files = list(path.glob("*.csproj"))
    fsproj_files = list(path.glob("*.fsproj"))
    sln_files = list(path.glob("*.sln"))

    if csproj_files or fsproj_files or sln_files:
        stack["type"] = "dotnet"
        stack["name"] = ".NET"
        stack["package_manager"] = "nuget"
        stack["ci_template"] = "ci-dotnet.yml.template"

        # Detecta se é C# ou F#
        if fsproj_files:
            stack["name"] = "F#"
        elif csproj_files:
            stack["name"] = "C#"

        return stack

    # ================================================
    # 4. Go (Golang)
    # ================================================
    if (path / "go.mod").exists():
        stack["type"] = "go"
        stack["name"] = "Go"
        stack["package_manager"] = "go mod"
        stack["ci_template"] = "ci-go.yml.template"
        return stack

    # ================================================
    # 5. Rust
    # ================================================
    if (path / "Cargo.toml").exists():
        stack["type"] = "rust"
        stack["name"] = "Rust"
        stack["package_manager"] = "cargo"
        stack["ci_template"] = "ci-rust.yml.template"
        return stack

    # ================================================
    # 6. Java / Kotlin
    # ================================================
    if (path / "pom.xml").exists():
        stack["type"] = "java"
        stack["name"] = "Java (Maven)"
        stack["package_manager"] = "maven"
        stack["ci_template"] = "ci-java.yml.template"
        return stack

    if (path / "build.gradle").exists() or (path / "build.gradle.kts").exists():
        stack["type"] = "java"
        stack["name"] = "Java (Gradle)"
        stack["package_manager"] = "gradle"
        stack["ci_template"] = "ci-java.yml.template"

        # Verifica se é Kotlin
        if (path / "build.gradle.kts").exists():
            stack["name"] = "Kotlin (Gradle)"

        return stack

    # ================================================
    # 7. Ruby
    # ================================================
    if (path / "Gemfile").exists():
        stack["type"] = "ruby"
        stack["name"] = "Ruby"
        stack["package_manager"] = "bundler"
        stack["ci_template"] = "ci-ruby.yml.template"
        return stack

    # ================================================
    # 8. PHP
    # ================================================
    if (path / "composer.json").exists():
        stack["type"] = "php"
        stack["name"] = "PHP"
        stack["package_manager"] = "composer"
        stack["ci_template"] = "ci-php.yml.template"
        return stack

    return stack


def detect_frameworks(path: Path, stack: ProjectStack) -> list:
    """
    Detecta frameworks específicos dentro de um stack.

    Args:
        path: Caminho do diretório do projeto.
        stack: Stack já detectado pelo get_project_stack().

    Returns:
        list: Lista de frameworks detectados.
    """
    frameworks = []

    if stack["type"] == "node":
        # Detecta frameworks Node.js
        if (path / "next.config.js").exists() or (path / "next.config.mjs").exists():
            frameworks.append("Next.js")
        if (path / "vite.config.js").exists() or (path / "vite.config.ts").exists():
            frameworks.append("Vite")
        if (path / "angular.json").exists():
            frameworks.append("Angular")
        if (path / "nuxt.config.js").exists() or (path / "nuxt.config.ts").exists():
            frameworks.append("Nuxt")
        if (path / "svelte.config.js").exists():
            frameworks.append("SvelteKit")
        if (path / "astro.config.mjs").exists():
            frameworks.append("Astro")

    elif stack["type"] == "python":
        # Detecta frameworks Python
        if (path / "manage.py").exists():
            frameworks.append("Django")
        if (path / "app.py").exists() or list(path.glob("**/flask_app.py")):
            frameworks.append("Flask")
        if (path / "main.py").exists():
            # Verifica conteúdo para FastAPI
            main_py = path / "main.py"
            if main_py.exists():
                content = main_py.read_text(encoding="utf-8", errors="ignore")
                if "fastapi" in content.lower():
                    frameworks.append("FastAPI")

    elif stack["type"] == "dotnet":
        # Detecta frameworks .NET
        csproj_files = list(path.glob("**/*.csproj"))
        for csproj in csproj_files:
            content = csproj.read_text(encoding="utf-8", errors="ignore")
            if "Microsoft.AspNetCore" in content:
                frameworks.append("ASP.NET Core")
            if "Blazor" in content:
                frameworks.append("Blazor")
            if "Microsoft.Maui" in content:
                frameworks.append("MAUI")

    return frameworks
