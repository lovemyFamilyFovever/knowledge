# 知库每日备份：content/ 变更自动 commit + push（含 _inbox/_trash 派生物）
# 由 Windows 计划任务每日 09:00 调用；无变更时静默退出。
$ErrorActionPreference = "Stop"
$root = "E:\chen\code\knowledge"
$log = Join-Path $root "indexes\backup.log"

function Log($m) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    $line | Out-File $log -Append -Encoding utf8
}

try {
    Push-Location $root
    # 内容区（含 _inbox/_trash，它们是派生但承载暂存状态，备份无害）
    git add content/ 2>$null
    $diff = git diff --cached --quiet; $code = $LASTEXITCODE
    if ($code -ne 0) {
        $msg = "auto-backup: content sync {0}" -f (Get-Date -Format "yyyy-MM-dd")
        git commit -m $msg 2>$null | Out-Null
        $pushed = git push 2>&1
        Log "committed+pushed: $msg"
    } else {
        # 无新提交也尝试 push（可能存在昨日未推成功的本地提交）
        $ahead = git rev-list "@{u}..HEAD" --count 2>$null
        if ($ahead -and [int]$ahead -gt 0) {
            git push 2>$null | Out-Null
            Log "pushed $ahead pending commit(s)"
        } else {
            Log "no changes"
        }
    }
} catch {
    Log "ERROR: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}
