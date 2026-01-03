$prs = 29..40
foreach ($pr in $prs) {
    Write-Host "----------------------------------------"
    Write-Host "Processing PR $pr"
    Write-Host "Marking as ready..."
    gh pr ready $pr
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Merging..."
        gh pr merge $pr --merge --delete-branch
    } else {
        Write-Host "Failed to mark PR $pr as ready. Skipping merge."
    }
}
