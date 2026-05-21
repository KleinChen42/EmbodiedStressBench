param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("push", "pull")]
    [string]$Direction,

    [Parameter(Mandatory=$true)]
    [string[]]$Paths,

    [string]$RemoteDir = "/home/zetyun/OpenMythos_test/projects/openMythosBench"
)

$RemoteUser = "zetyun"
$RemoteHost = "183.166.183.2"
$RemotePort = "60071"
$SshKeyName = "hd03-tenant13-research-20260405"
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LocalEnvPath = Join-Path $ProjectRoot ".env.local"
$AskPassCmd = Join-Path $PSScriptRoot "ssh_askpass.cmd"
$KeyPath = Join-Path $HOME ".ssh\$SshKeyName"

function Import-LocalEnv {
    param([string]$Path)
    if (!(Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (!$line -or $line.StartsWith("#") -or !$line.Contains("=")) { return }
        $parts = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim().Trim('"').Trim("'"), "Process")
    }
}

Import-LocalEnv $LocalEnvPath
$env:SSH_ASKPASS = $AskPassCmd
$env:SSH_ASKPASS_REQUIRE = "force"
$env:DISPLAY = ":0"

$ScpExe = "C:\Windows\System32\OpenSSH\scp.exe"
if (!(Test-Path $ScpExe)) {
    $found = Get-Command scp -ErrorAction SilentlyContinue
    if ($found) { $ScpExe = $found.Source }
    else { throw "scp.exe not found. Enable Windows OpenSSH Client." }
}

if (!(Test-Path $KeyPath)) {
    throw "SSH key not found: $KeyPath"
}

$CommonArgs = @(
    "-o", "StrictHostKeyChecking=accept-new",
    "-i", $KeyPath,
    "-P", $RemotePort
)

foreach ($path in $Paths) {
    $remotePath = $path -replace "\\", "/"
    if ($Direction -eq "push") {
        $local = Resolve-Path $path
        $remote = "$RemoteUser@${RemoteHost}:`"$RemoteDir/$remotePath`""
        Write-Host "[h200-sync] push $local -> $remote" -ForegroundColor Cyan
        & $ScpExe @CommonArgs -r $local $remote
    } else {
        $remote = "$RemoteUser@${RemoteHost}:`"$RemoteDir/$remotePath`""
        Write-Host "[h200-sync] pull $remote -> $path" -ForegroundColor Cyan
        & $ScpExe @CommonArgs -r $remote $path
    }
}
