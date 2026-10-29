$ErrorActionPreference='Stop'
Get-ChildItem -File -Recurse | Where-Object { $_.Name -ne 'checksums.csv' -and $_.FullName -notmatch '\\.git\\' } | ForEach-Object {
    [pscustomobject]@{path=$_.FullName.Substring((Get-Location).Path.Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
} | Export-Csv results/checksums.csv -NoTypeInformation
