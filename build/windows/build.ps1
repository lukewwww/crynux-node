param(
    [string]$BLOCKCHAIN = ""
)

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Get-Location
.\build\windows\prepare.ps1 build\crynux_node
Set-Location "build\crynux_node"
.\package.ps1 -BLOCKCHAIN $BLOCKCHAIN
Set-Location $PROJECT_ROOT
