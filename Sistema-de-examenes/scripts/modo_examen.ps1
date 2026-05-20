$Servidor = "192.168.1.113"

Write-Host "CONFIGURANDO MODO EXAMEN..."

# BLOQUEAR TODO EL TRAFICO
Set-NetFirewallProfile `
-Profile Domain,Public,Private `
-DefaultOutboundAction Block

# PERMITIR SERVIDOR LOCAL
New-NetFirewallRule `
-DisplayName "PermitirServidorLocal" `
-Direction Outbound `
-RemoteAddress $Servidor `
-Action Allow

Write-Host "Modo examen activado"