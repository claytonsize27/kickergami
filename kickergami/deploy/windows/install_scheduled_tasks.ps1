param(
    [string]$ProjectDir = "C:\Users\clayt\OneDrive\Documents\Kickeragami\kickergami",
    [string]$TaskPrefix = "Kickergami"
)

$ErrorActionPreference = "Stop"

$runner = Join-Path $ProjectDir "deploy\windows\run_kickergami_update.ps1"
if (-not (Test-Path -LiteralPath $runner)) {
    throw "Runner script not found: $runner"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`" -ProjectDir `"$ProjectDir`""

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

$windows = @(
    @{ Name = "Thursday"; Day = "Thursday" },
    @{ Name = "Sunday"; Day = "Sunday" },
    @{ Name = "Monday"; Day = "Monday" },
    @{ Name = "Saturday"; Day = "Saturday" }
)

foreach ($window in $windows) {
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $window.Day -At 11:45pm
    $taskName = "$TaskPrefix $($window.Name) 1145PM ET"
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Runs Kickergami completed-game update after the $($window.Name) NFL window." `
        -Force | Out-Null
    Write-Host "Installed scheduled task: $taskName"
}

Write-Host "Kickergami scheduled tasks installed. Confirm this machine's Windows timezone is Eastern Time."

