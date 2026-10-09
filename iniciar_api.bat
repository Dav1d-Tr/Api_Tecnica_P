@echo off
setlocal

title API PLANOS DE COTIZACION

REM =========================================================
REM IR A LA CARPETA DEL PROYECTO
REM =========================================================

cd /d "P:\TECNICA\PLANOS DE COTIZACIÓN"

if errorlevel 1 (
    echo.
    echo ERROR: No se pudo acceder a la carpeta del proyecto.
    echo P:\TECNICA\PLANOS DE COTIZACIÓN
    echo.
    pause
    exit /b 1
)

REM =========================================================
REM VARIABLES DE ENTORNO
REM =========================================================

REM IMPORTANTE:
REM CREA UNA API KEY NUEVA Y PEGALA AQUI.
REM NO USES LA QUE COMPARTISTE EN EL CHAT.

set "API_KEY=hsJfOkq6Zx1lIvb04ncMsQCqJTLLKy0KjT9N8f3OmBY="

set "PUBLIC_URL=https://formation-kennedy-expired-belt.trycloudflare.com"

REM =========================================================
REM COMPROBAR ARCHIVOS DEL PROYECTO
REM =========================================================

if not exist "app.py" (
    echo.
    echo ERROR: No se encontro app.py en:
    echo %CD%
    echo.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo.
    echo ERROR: No existe el entorno virtual.
    echo Se esperaba encontrar:
    echo %CD%\venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

REM =========================================================
REM MOSTRAR CONFIGURACION
REM =========================================================

echo.
echo =========================================================
echo            API PLANOS DE COTIZACION
echo =========================================================
echo.
echo Carpeta del proyecto:
echo %CD%
echo.
echo Ruta de planos configurada:
echo P:\TECNICA\PLANOS DE COTIZACION
echo.
echo Puerto FastAPI:
echo 8091
echo.
echo Swagger local:
echo http://127.0.0.1:8091/docs
echo.
echo OpenAPI local:
echo http://127.0.0.1:8091/openapi.json
echo.
echo URL publica:
echo %PUBLIC_URL%
echo.
echo OpenAPI publico:
echo %PUBLIC_URL%/openapi.json
echo.
echo =========================================================

REM =========================================================
REM COMPROBAR VARIABLES DESDE PYTHON
REM =========================================================

echo.
echo Verificando variables de entorno...
echo.

venv\Scripts\python.exe -c "import os; print('PUBLIC_URL DESDE PYTHON =', os.getenv('PUBLIC_URL')); print('API_KEY CONFIGURADA =', 'SI' if len(os.getenv('API_KEY','')) >= 20 else 'NO')"

if errorlevel 1 (
    echo.
    echo ERROR: Python no pudo verificar las variables.
    echo.
    pause
    exit /b 1
)

echo.
echo =========================================================
echo Iniciando FastAPI...
echo =========================================================
echo.

REM =========================================================
REM INICIAR FASTAPI
REM =========================================================

venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8091

REM =========================================================
REM SI UVICORN SE CIERRA O FALLA
REM =========================================================

echo.
echo =========================================================
echo FastAPI se ha detenido.
echo =========================================================
echo.

pause

endlocal