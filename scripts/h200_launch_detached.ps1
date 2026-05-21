param(
    [Parameter(Mandatory=$true)]
    [string]$RemoteScript,

    [string]$RemoteDir = "/home/zetyun/OpenMythos_test",
    [string]$LogPath = ""
)

if (-not $LogPath) {
    $name = [IO.Path]::GetFileNameWithoutExtension($RemoteScript)
    $LogPath = "outputs/${name}_main.log"
}

$cmd = "mkdir -p outputs && chmod +x '$RemoteScript' && setsid -f bash '$RemoteScript' > '$LogPath' 2>&1 < /dev/null && echo LAUNCHED_SCRIPT='$RemoteScript' && echo LOG='$LogPath'"

powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\invoke_h200_command.ps1" `
    -RemoteDir $RemoteDir `
    -RemoteCommand $cmd
