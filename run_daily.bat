@echo off
chcp 65001 > nul
cd /d "c:\Users\LTSZ\Desktop\test\cc test"
echo. >> output\run_log.txt
echo ============================================== >> output\run_log.txt
echo Run start: %date% %time% >> output\run_log.txt
echo ============================================== >> output\run_log.txt
python main.py >> output\run_log.txt 2>&1
echo. >> output\run_log.txt
echo Run end: %date% %time% >> output\run_log.txt
