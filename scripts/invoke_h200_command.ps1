param(
    [string]$RemoteDir     = "/home/zetyun/OpenMythos_test",
    [string]$RemoteCommand = "",
    [switch]$NoCD
)

# H200 connection helper for openMythosBench.
# Secrets are loaded from process environment or local .env.local, not hardcoded.
$RemoteUser = "zetyun"
$RemoteHost = "183.166.183.2"
$RemotePort = "60071"
$SshKeyName = "hd03-tenant13-research-20260405"

$ErrorActionPreference = "Stop"
$AskPassCmd = Join-Path $PSScriptRoot "ssh_askpass.cmd"
$KeyPath = Join-Path $HOME ".ssh\$SshKeyName"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LocalEnvPath = Join-Path $ProjectRoot ".env.local"

function Import-LocalEnv {
    param([string]$Path)
    if (!(Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (!$line -or $line.StartsWith("#") -or !$line.Contains("=")) { return }
        $parts = $line.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($name) {
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

Import-LocalEnv $LocalEnvPath

$SshExe = "C:\Windows\System32\OpenSSH\ssh.exe"
if (!(Test-Path $SshExe)) {
    $found = Get-Command ssh -ErrorAction SilentlyContinue
    if ($found) { $SshExe = $found.Source }
    else { throw "ssh.exe not found. Enable Windows OpenSSH Client." }
}

if (!(Test-Path $KeyPath)) {
    Write-Host "[warn] SSH key not found: $KeyPath" -ForegroundColor Yellow
    Write-Host "       Copy key '$SshKeyName' to that path, or edit `$SshKeyName."
    exit 1
}
try {
    icacls $KeyPath /inheritance:r /grant:r "$($env:USERNAME):R" 2>&1 | Out-Null
} catch {
    Write-Host "[warn] Could not adjust SSH key ACL; continuing with existing permissions." -ForegroundColor Yellow
}

if (-not $env:SSH_KEY_PASSPHRASE) {
    $Secure = Read-Host "SSH key passphrase (blank = none)" -AsSecureString
    $Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        $env:SSH_KEY_PASSPHRASE = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    }
}

$env:SSH_ASKPASS = $AskPassCmd
$env:SSH_ASKPASS_REQUIRE = "force"
$env:DISPLAY = ":0"

# Use -T for non-interactive commands to avoid local PowerShell hanging on detached launches.
$TtyFlag = if ($RemoteCommand) { "-T" } else { "-t" }
$SshArgs = @(
    $TtyFlag,
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "ServerAliveInterval=60",
    "-o", "ServerAliveCountMax=10",
    "-i", $KeyPath,
    "-p", $RemotePort,
    "$RemoteUser@$RemoteHost"
)

if ($RemoteCommand) {
    if ((-not $NoCD) -and $RemoteDir) {
        $SafeRemoteDir = $RemoteDir.Replace("'", "'\''")
        $SshArgs += "cd '$SafeRemoteDir' && $RemoteCommand"
    } else {
        $SshArgs += $RemoteCommand
    }
} elseif ((-not $NoCD) -and $RemoteDir) {
    $SafeRemoteDir = $RemoteDir.Replace("'", "'\''")
    $SshArgs += "cd '$SafeRemoteDir' && exec bash --login"
} else {
    $SshArgs += "exec bash --login"
}

$dest = if ($RemoteDir) { $RemoteDir } else { "~" }
Write-Host "[h200] $RemoteUser@${RemoteHost}:$RemotePort dir=$dest" -ForegroundColor Cyan
& $SshExe @SshArgs
