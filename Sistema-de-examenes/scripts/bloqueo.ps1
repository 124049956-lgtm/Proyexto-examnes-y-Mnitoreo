Write-Host "BLOQUEANDO INTERNET..."

Disable-NetAdapter -Name "Wi-Fi" -Confirm:$false

Write-Host "Internet bloqueado"