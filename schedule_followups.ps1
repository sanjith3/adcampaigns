# PowerShell script to schedule follow-up processing
# Run this script as Administrator to set up the scheduled task

$action = New-ScheduledTaskAction -Execute "D:\softads\adsoft\run_followups.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "00:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "AdSoft Follow-up Processing" -Action $action -Trigger $trigger -Settings $settings -Description "Automatically process follow-ups at midnight"

Write-Host "Scheduled task created successfully!"
Write-Host "The follow-up processing will run daily at 12:00 AM"
Write-Host "To view the task: Get-ScheduledTask -TaskName 'AdSoft Follow-up Processing'"
Write-Host "To remove the task: Unregister-ScheduledTask -TaskName 'AdSoft Follow-up Processing'"
