# API Planos de Cotización

La API lee la carpeta:

P:\PLANOS DE COTIZACIÓN

## Estructura recomendada

P:\API_Tecnica\
  app.py
  iniciar_api.bat
  abrir_puerto_8090.bat
  venv\

## Primera instalación

Desde PowerShell:

cd P:\API_Tecnica
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install fastapi uvicorn

## Arranque normal

Doble clic en:

iniciar_api.bat

## URLs

Local:
http://localhost:8090/docs

Desde otro PC:
http://IP_DEL_SERVIDOR:8090/docs

## Endpoints

GET /
GET /api/planos/estado
GET /api/planos/archivos
GET /api/planos/buscar?q=texto
GET /api/planos/descargar?ruta_relativa=...

## Nota importante

La unidad P: debe estar conectada en la misma sesión de Windows que ejecuta el .bat.
Si más adelante el API se instala como servicio de Windows, conviene usar la ruta UNC
real de la carpeta compartida en lugar de la letra P:.
