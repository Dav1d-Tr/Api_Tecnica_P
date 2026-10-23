@echo off
chcp 65001 >nul
setlocal

title API PLANOS DE COTIZACION

REM =========================================================
REM IR A LA CARPETA DEL PROYECTO
REM =========================================================
cd /d "P:\TECNICA\PLANOS DE COTIZACIÓN"
if errorlevel 1 (
    echo ERROR: No se pudo acceder a la carpeta del proyecto.
    pause
    exit /b 1
)

REM =========================================================
REM VARIABLES DE ENTORNO - COMPLETAR ANTES DE INICIAR
REM =========================================================
REM Pega tu clave actual entre = y la comilla final. No se muestra en pantalla.
set "API_KEY=hsJfOkq6Zx1lIvb04ncMsQCqJTLLKy0KjT9N8f3OmBY="
set "PUBLIC_URL=https://formation-kennedy-expired-belt.trycloudflare.com"
set "PLANOS_API_LOCAL_URL=http://127.0.0.1:8091"
set "PLANOS_RAIZ_TECNICA=P:\TECNICA"
set "PLANOS_RAIZ_TECNICA_2=P:\aplic\TECNICA 2"
set "PLANOS_RAIZ_FS_DPTO=S:\FS-DPTO"
set "PLANOS_RUTA_PC=P:\TECNICA\PLANOS DE COTIZACIÓN"

REM Elegir graph para SharePoint directo, o local para OneDrive sincronizado.
set "SP_MODE=graph"

REM MODO GRAPH: completar estos cuatro valores.
REM App de Entra con permiso de aplicación Sites.Selected,
REM consentimiento de administrador y acceso read al sitio correspondiente.
REM SP_DRIVE_ID es el ID de la biblioteca documental, no la URL del sitio.
set "SP_TENANT_ID=f9e88750-7a39-4637-a9f0-5a3cb1bc9295"
set "SP_CLIENT_ID=ef65490a-5b52-4d9c-a8c2-7cbe0577a7d4"
set "SP_CLIENT_SECRET=%AZURE_CLIENT_SECRET%"
set "SP_DRIVE_ID=b!5gW2mOUh5kiH1Zd6NksuFlXfRoEvLgJMpbNe6HaCQGUOobu2qca3QY7NlciVwpz9"
REM Ruta dentro de la biblioteca, sin repetir su nombre:
set "SP_PROJECTS_PATH=Demetalicos proyectos"

REM MODO LOCAL: poner SP_MODE=local y completar la ruta absoluta real.
REM Debe terminar en: Demetalicos SAS - Documentos\Demetalicos proyectos
REM Ejemplo: C:\Users\USUARIO\Demetalicos SAS - Documentos\Demetalicos proyectos
set "SP_LOCAL_ROOT="

REM =========================================================
REM COMPROBAR ARCHIVOS DEL PROYECTO
REM =========================================================
if not exist "app.py" (
    echo ERROR: No se encontro app.py en %CD%
    pause
    exit /b 1
)
if not exist "mcp_planos.py" (
    echo ERROR: No se encontro mcp_planos.py en %CD%
    pause
    exit /b 1
)
if not exist "venv\Scripts\python.exe" (
    echo ERROR: No existe venv\Scripts\python.exe
    pause
    exit /b 1
)

REM =========================================================
REM MOSTRAR CONFIGURACION Y VALIDAR CLAVE SIN REVELARLA
REM =========================================================
echo.
echo =========================================================
echo            API PLANOS DE COTIZACION
echo =========================================================
echo Carpeta: %CD%
echo FastAPI: http://127.0.0.1:8091/docs
echo OpenAPI: http://127.0.0.1:8091/openapi.json
echo URL publica: %PUBLIC_URL%
echo SharePoint - modo: %SP_MODE%
echo.
venv\Scripts\python.exe -c "import os,sys; ok=len(os.getenv('API_KEY',''))>=20; print('API_KEY CONFIGURADA =', 'SI' if ok else 'NO'); sys.exit(0 if ok else 1)"
if errorlevel 1 (
    echo ERROR: Completa API_KEY con al menos 20 caracteres en este BAT.
    pause
    exit /b 1
)

REM =========================================================
REM MISMO BAT PARA AMBOS PROCESOS Y MISMAS VARIABLES
REM =========================================================
REM Consola 1: iniciar.bat
REM Consola 2: iniciar.bat mcp
REM Instalar dependencias una vez con:
REM venv\Scripts\python.exe -m pip install -r requirements.txt
REM No utiliza .env ni necesita revision_ov.py: todo esta en app.py.

if /I "%~1"=="mcp" goto INICIAR_MCP
if not "%~1"=="" (
    echo Uso: iniciar.bat [mcp]
    pause
    exit /b 1
)

echo Iniciando FastAPI en el puerto 8091...
venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8091
goto FIN

:INICIAR_MCP
title MCP PLANOS DEMETALICOS
venv\Scripts\python.exe -c "from mcp.server.mcpserver import MCPServer; print('MCPServer disponible')"
if errorlevel 1 (
    echo ERROR: Instala las dependencias de requirements.txt en este venv.
    pause
    exit /b 1
)
echo Iniciando MCP en http://127.0.0.1:8092/mcp ...
venv\Scripts\python.exe mcp_planos.py

:FIN
echo.
echo El servidor se ha detenido.
pause
endlocal
