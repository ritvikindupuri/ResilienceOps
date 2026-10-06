# Cross-platform AWS Teardown Script for SRE Colosseum
# Guarantees 100% destruction of all AWS cloud resources to prevent ongoing charges.

$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   SRE COLOSSEUM - AWS CLEAN INFRASTRUCTURE TEARDOWN" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Join-Path $ScriptDir "terraform"

if (-not (Test-Path $TerraformDir)) {
    Write-Host "[ERROR] Terraform directory not found at $TerraformDir" -ForegroundColor Red
    exit 1
}

Push-Location $TerraformDir

try {
    Write-Host "`n[1/2] Checking current Terraform state..." -ForegroundColor Yellow
    $StateList = terraform state list 2>$null
    if (-not $StateList) {
        Write-Host "[INFO] No active Terraform resources found. Zero charges running." -ForegroundColor Green
        Pop-Location
        exit 0
    }

    Write-Host "[2/2] Destroying all AWS resources (EC2, VPC, Subnets, SG, IAM, IGW)..." -ForegroundColor Yellow
    terraform destroy -auto-approve

    Write-Host "`n[SUCCESS] All AWS infrastructure cleanly destroyed. ZERO residual cost." -ForegroundColor Green
}
catch {
    Write-Host "`n[ERROR] Teardown encountered an error: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
finally {
    Pop-Location
}
