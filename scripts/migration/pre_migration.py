"""
Pre-Migration Module
====================
Validações e preparação para a migração.

Responsabilidades:
    - Verificar se DevBase foi executado
    - Listar repositórios Git e seus status
    - Verificar espaço em disco
    - Gerar relatório de pré-migração
"""

import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

from migration_config import MigrationConfig, validate_config


@dataclass
class GitRepoStatus:
    """Status de um repositório Git."""
    path: Path
    name: str
    has_changes: bool
    has_unpushed: bool
    current_branch: str
    remote_url: Optional[str]
    status_summary: str


@dataclass
class PreMigrationReport:
    """Relatório de pré-migração."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    git_repos: List[GitRepoStatus]
    disk_space_ok: bool
    disk_space_available_gb: float
    source_file_count: int
    source_dir_count: int


def check_git_repo_status(repo_path: Path) -> Optional[GitRepoStatus]:
    """
    Verifica o status de um repositório Git.

    Args:
        repo_path: Caminho para o diretório do repositório.

    Returns:
        GitRepoStatus ou None se não for um repositório válido.
    """
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        return None

    try:
        # Obter branch atual
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        current_branch = result.stdout.strip() or "HEAD detached"

        # Verificar se há alterações não commitadas
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        has_changes = bool(result.stdout.strip())

        # Verificar se há commits não enviados
        result = subprocess.run(
            ["git", "log", "@{u}..", "--oneline"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        has_unpushed = bool(result.stdout.strip())

        # Obter URL do remote
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        remote_url = result.stdout.strip() if result.returncode == 0 else None

        # Construir resumo
        status_parts = []
        if has_changes:
            status_parts.append("alterações locais")
        if has_unpushed:
            status_parts.append("commits não enviados")
        if not status_parts:
            status_parts.append("limpo")

        return GitRepoStatus(
            path=repo_path,
            name=repo_path.name,
            has_changes=has_changes,
            has_unpushed=has_unpushed,
            current_branch=current_branch,
            remote_url=remote_url,
            status_summary=", ".join(status_parts),
        )

    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return GitRepoStatus(
            path=repo_path,
            name=repo_path.name,
            has_changes=False,
            has_unpushed=False,
            current_branch="unknown",
            remote_url=None,
            status_summary="erro ao verificar",
        )


def find_git_repositories(root_path: Path, max_depth: int = 2) -> List[Path]:
    """
    Encontra todos os repositórios Git dentro de um diretório.

    Args:
        root_path: Diretório raiz para busca.
        max_depth: Profundidade máxima de busca.

    Returns:
        Lista de caminhos para repositórios Git.
    """
    repos = []

    def search(current_path: Path, depth: int):
        if depth > max_depth:
            return

        if not current_path.is_dir():
            return

        git_dir = current_path / ".git"
        if git_dir.exists():
            repos.append(current_path)
            return  # Não buscar dentro de repos

        try:
            for child in current_path.iterdir():
                if child.is_dir() and not child.name.startswith("."):
                    search(child, depth + 1)
        except PermissionError:
            pass

    search(root_path, 0)
    return repos


def check_disk_space(target_path: Path, required_gb: float = 1.0) -> Tuple[bool, float]:
    """
    Verifica se há espaço em disco suficiente.

    Args:
        target_path: Caminho do destino.
        required_gb: Espaço mínimo requerido em GB.

    Returns:
        Tupla (espaço_suficiente, espaço_disponível_gb).
    """
    try:
        import shutil
        total, used, free = shutil.disk_usage(target_path)
        free_gb = free / (1024 ** 3)
        return free_gb >= required_gb, free_gb
    except Exception:
        return True, 0.0  # Assume OK se não conseguir verificar


def count_source_items(source_path: Path, excluded_dirs: set) -> Tuple[int, int]:
    """
    Conta arquivos e diretórios na origem.

    Args:
        source_path: Caminho de origem.
        excluded_dirs: Diretórios a ignorar.

    Returns:
        Tupla (contagem_arquivos, contagem_diretórios).
    """
    file_count = 0
    dir_count = 0

    def count(path: Path):
        nonlocal file_count, dir_count

        if not path.exists():
            return

        try:
            for item in path.iterdir():
                if item.is_dir():
                    if item.name not in excluded_dirs:
                        dir_count += 1
                        count(item)
                else:
                    file_count += 1
        except PermissionError:
            pass

    count(source_path)
    return file_count, dir_count


def run_pre_migration(config: MigrationConfig) -> PreMigrationReport:
    """
    Executa todas as validações de pré-migração.

    Args:
        config: Configuração de migração.

    Returns:
        PreMigrationReport com os resultados.
    """
    errors = []
    warnings = []

    # 1. Validar configuração
    config_errors = validate_config(config)
    errors.extend(config_errors)

    # 2. Verificar repositórios Git (se origem existir)
    git_repos = []
    if config.source_root.exists():
        code_path = config.source_root / "01_workspace" / "code"
        if code_path.exists():
            repo_paths = find_git_repositories(code_path)
            for repo_path in repo_paths:
                status = check_git_repo_status(repo_path)
                if status:
                    git_repos.append(status)
                    if status.has_changes:
                        warnings.append(
                            f"Repo '{status.name}' tem alterações não commitadas"
                        )
                    if status.has_unpushed:
                        warnings.append(
                            f"Repo '{status.name}' tem commits não enviados"
                        )

    # 3. Verificar espaço em disco
    disk_ok, disk_gb = check_disk_space(
        config.target_root.parent if config.target_root.exists() else Path("D:/"),
        required_gb=1.0,
    )
    if not disk_ok:
        warnings.append(f"Espaço em disco baixo: {disk_gb:.2f} GB disponíveis")

    # 4. Contar itens na origem
    file_count = 0
    dir_count = 0
    if config.source_root.exists():
        file_count, dir_count = count_source_items(
            config.source_root,
            config.excluded_dirs,
        )

    # Determinar se é válido para prosseguir
    is_valid = len(errors) == 0

    return PreMigrationReport(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        git_repos=git_repos,
        disk_space_ok=disk_ok,
        disk_space_available_gb=disk_gb,
        source_file_count=file_count,
        source_dir_count=dir_count,
    )


def print_pre_migration_report(report: PreMigrationReport, verbose: bool = True):
    """
    Imprime o relatório de pré-migração formatado.

    Args:
        report: Relatório gerado por run_pre_migration.
        verbose: Se True, mostra detalhes completos.
    """
    print("\n" + "=" * 60)
    print("📋 RELATÓRIO DE PRÉ-MIGRAÇÃO")
    print("=" * 60)

    # Status geral
    if report.is_valid:
        print("\n✅ Status: PRONTO PARA MIGRAÇÃO")
    else:
        print("\n❌ Status: MIGRAÇÃO BLOQUEADA")

    # Erros
    if report.errors:
        print("\n🚨 ERROS (devem ser corrigidos):")
        for error in report.errors:
            print(f"   • {error}")

    # Warnings
    if report.warnings:
        print("\n⚠️  AVISOS (recomendado corrigir):")
        for warning in report.warnings:
            print(f"   • {warning}")

    # Estatísticas
    print(f"\n📊 Estatísticas da Origem:")
    print(f"   • Arquivos: {report.source_file_count:,}")
    print(f"   • Diretórios: {report.source_dir_count:,}")
    print(f"   • Espaço disponível: {report.disk_space_available_gb:.2f} GB")

    # Repositórios Git
    if verbose and report.git_repos:
        print(f"\n📂 Repositórios Git encontrados ({len(report.git_repos)}):")
        for repo in report.git_repos:
            icon = "⚠️ " if repo.has_changes or repo.has_unpushed else "✓ "
            print(f"   {icon} {repo.name}")
            print(f"      Branch: {repo.current_branch}")
            print(f"      Status: {repo.status_summary}")
            if repo.remote_url and verbose:
                print(f"      Remote: {repo.remote_url}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Teste standalone
    from migration_config import get_default_config

    config = get_default_config()
    report = run_pre_migration(config)
    print_pre_migration_report(report)
