@echo off
REM Run the hypercell CLI from the repo root without activating the venv.
REM Usage from C:\hypercell:  hc talk    |    hc run tournament ...
REM (For 'hc' anywhere, add C:\hypercell\.venv\Scripts to your PATH.)
"%~dp0.venv\Scripts\hc.exe" %*
