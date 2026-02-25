# scripts/setup-productivity.ps1
# Atalhos de produtividade para o DevBase

function ib {
    devbase pkm icebox $args
}

function jr {
    devbase pkm journal $args
}

function cb {
    devbase pkm cookbook $args
}

function ov {
    if (Test-Path '.\OVEN.md') {
        code (Get-Item '.\OVEN.md')
    } else {
        Write-Host "OVEN.md não encontrado no diretório atual." -ForegroundColor Yellow
    }
}

Write-Host "🚀 Atalhos de produtividade carregados: ib (icebox), jr (journal), cb (cookbook), ov (oven)" -ForegroundColor Green
