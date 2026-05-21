param(
    [string]$MainTex = "paper/ieee_access/main_revised.tex",
    [string]$OutputDir = "ieee_access_revision_20260520"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$MainPath = Resolve-Path (Join-Path $ProjectRoot $MainTex)
$PaperDir = Split-Path $MainPath -Parent
$MainFile = Split-Path $MainPath -Leaf
$JobName = [IO.Path]::GetFileNameWithoutExtension($MainFile)
$BuildDir = Join-Path $PaperDir "build"
$StatusDir = Join-Path $ProjectRoot $OutputDir
$StatusPath = Join-Path $StatusDir "pdf_build_status.md"

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null

$Status = New-Object System.Collections.Generic.List[string]
$Status.Add("# IEEE Access PDF Build Status")
$Status.Add("")
$Status.Add("Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$Status.Add("")
$Status.Add("Canonical source: $MainTex")
$Status.Add("")

function Add-Status {
    param([string]$Line)
    $Status.Add($Line)
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Run-Checked {
    param(
        [string]$Exe,
        [string[]]$Args
    )
    Add-Status -Line "- Running: $Exe $($Args -join ' ')"
    & $Exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "$Exe exited with code $LASTEXITCODE"
    }
}

$Built = $false
Push-Location $PaperDir
try {
    if (Test-Command "latexmk") {
        Add-Status "## Build Attempt"
        Add-Status ""
        Add-Status -Line "- latexmk detected; compiling canonical IEEE Access source."
        Run-Checked "latexmk" @("-pdf", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-outdir=build", $MainFile)
        $Built = $true
    } elseif (Test-Command "pdflatex") {
        Add-Status "## Build Attempt"
        Add-Status ""
        Add-Status -Line "- pdflatex detected; compiling with BibTeX pass."
        Run-Checked "pdflatex" @("-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-output-directory", "build", $MainFile)
        Run-Checked "bibtex" @("build/$JobName")
        Run-Checked "pdflatex" @("-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-output-directory", "build", $MainFile)
        Run-Checked "pdflatex" @("-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-output-directory", "build", $MainFile)
        $Built = $true
    } else {
        Add-Status "## Build Attempt"
        Add-Status ""
        Add-Status -Line "- latexmk: missing"
        Add-Status -Line "- pdflatex: missing"
        if (Test-Command "docker") {
            Add-Status -Line "- docker: command found"
            $DockerExitCode = 1
            try {
                & docker info *> $null
                $DockerExitCode = $LASTEXITCODE
            } catch {
                $DockerExitCode = 1
            }
            if ($DockerExitCode -eq 0) {
                $Images = & docker images --format "{{.Repository}}:{{.Tag}}"
                $TexImage = $Images | Where-Object { $_ -match "tex|latex|texlive" } | Select-Object -First 1
                if ($TexImage) {
                    Add-Status -Line "- Docker daemon is running and TeX-like image detected: $TexImage."
                    Add-Status -Line "- Docker compilation is not run automatically by this script; use the image above to compile $MainTex from the repository root."
                } else {
                    Add-Status -Line "- Docker daemon is running, but no local TeX/LaTeX image was found."
                }
            } else {
                Add-Status -Line "- Docker command exists, but the Docker daemon is not reachable."
            }
        } else {
            Add-Status -Line "- docker: missing"
        }
    }
} catch {
    Add-Status ""
    Add-Status "## Error"
    Add-Status ""
    Add-Status -Line "- $($_.Exception.Message)"
} finally {
    Pop-Location
}

$PdfPath = Join-Path $BuildDir "$JobName.pdf"
if ($Built -and (Test-Path $PdfPath)) {
    Add-Status ""
    Add-Status "## Result"
    Add-Status ""
    Add-Status -Line "- PDF built: $PdfPath"
    $LogPath = Join-Path $BuildDir "$JobName.log"
    if (Test-Path $LogPath) {
        $LogText = Get-Content $LogPath -Raw
        $Overfull = ([regex]::Matches($LogText, "Overfull \\hbox")).Count
        $Undefined = ([regex]::Matches($LogText, "undefined references|Citation .* undefined|There were undefined")).Count
        Add-Status -Line "- Overfull hbox count: $Overfull"
        Add-Status -Line "- Undefined reference/citation warnings: $Undefined"
    }
} else {
    Add-Status ""
    Add-Status "## Result"
    Add-Status ""
    Add-Status -Line "- PDF not built in this environment."
    Add-Status -Line "- Install latexmk/pdflatex, or start Docker Desktop and provide a local TeX Live image, then rerun:"
    Add-Status "  powershell -ExecutionPolicy Bypass -File scripts/build_ieee_access_pdf.ps1"
}

$Status | Set-Content -Path $StatusPath -Encoding UTF8
Write-Host "[ieee-access-build] wrote $StatusPath"
if ($Built) {
    Write-Host "[ieee-access-build] PDF: $PdfPath"
}
