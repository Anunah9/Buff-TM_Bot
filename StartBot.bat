@echo off

REM Путь к вашему виртуальному окружению (venv)
set VENV_PATH=.\venv

REM Путь к скрипту AutoTradeCreator.py
set SCRIPT_PATH=.\BuffBot.py 

REM Активация виртуального окружения
call %VENV_PATH%\Scripts\activate

REM Запуск Python скрипта
python %SCRIPT_PATH%
