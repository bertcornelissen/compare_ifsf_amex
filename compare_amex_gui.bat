# Convenience Windows script for running ISO 8583 message comparison GUI
# Usage: compare_amex_cli.bat [options]

# %~dp0: This expands to the drive letter and path of the batch file's location.
# cd /d: Changes the current directory and drive to the specified path. 
# The /d switch ensures that the drive is also changed if the batch file is located on a different drive.

cd /d "%~dp0"

.venv/bin/activate

streamlit run compare_amex_gui.py "$@"