# Convenience Windows script for running ISO 8583 message comparison CLI
# Usage: compare_amex_cli.bat file1.txt file2.txt [options]

# %~dp0: This expands to the drive letter and path of the batch file's location.
# cd /d: Changes the current directory and drive to the specified path. 
# The /d switch ensures that the drive is also changed if the batch file is located on a different drive.

cd /d "%~dp0"

.venv\Scripts\activate

python3 compare_amex_cli.py "$@"
