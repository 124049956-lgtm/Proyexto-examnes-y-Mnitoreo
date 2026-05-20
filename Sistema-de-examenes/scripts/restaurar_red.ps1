Write-Host "RESTAURANDO INTERNET..."

Set-NetFirewallProfile `
-Profile Domain,Public,Private `
-DefaultOutboundAction Allow

Remove-NetFirewallRule `
-DisplayName "PermitirServidorLocal"

Write-Host "Internet restaurado"