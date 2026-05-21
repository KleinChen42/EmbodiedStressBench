param(
    [string]$RemoteDir = "/home/zetyun/OpenMythos_test"
)

$cmd = @'
echo ===DATE===
date
echo ===PWD===
pwd
echo ===GPU===
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
echo ===Q2G_OR_BENCH_PIDS===
pgrep -af 'openMythosBench|EmbodiedStressBench|embodied_stressbench|run_matrix|run_single|ras_revision|run_single_view_pick' || true
'@

powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\invoke_h200_command.ps1" `
    -RemoteDir $RemoteDir `
    -RemoteCommand $cmd
