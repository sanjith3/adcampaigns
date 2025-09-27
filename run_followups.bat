@echo off
cd /d "D:\softads\adsoft"
python manage.py process_followups
echo Follow-up processing completed at %date% %time% >> followup_log.txt
