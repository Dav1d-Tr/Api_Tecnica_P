import hmac
import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.security import APIKeyHeader
from pypdf import PdfReader

# ============================================================
# CONFIGURACIÓN
# ============================================================

RUTA_BASE = Path(r"P:\TECNICA\PLANOS DE COTIZACIÓN")

API_KEY = os.environ.get("API_KEY", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

if len(API_KEY) < 20:
    raise RuntimeError(
        "Define la variable de entorno API_KEY con al menos 20 caracteres."
    )

app = FastAPI(
    title="API Planos de Cotización",
    description=(
        "Busca cotizaciones por código PC, lista los PDF de "
        "'01 - Planos', lee su texto y los descarga."
    ),
    version="1.1.0",
    servers=[{"url": PUBLIC_URL}] if PUBLIC_URL else None,
)
# ============================================================
# AUTENTICACIÓN
# ============================================================

esquema_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verificar_clave(
    por_header: str | None = Security(esquema_header),
):
    enviada = por_header or ""

    if not hmac.compare_digest(
        enviada.encode(),
        API_KEY.encode()
    ):
        raise HTTPException(
            status_code=401,
            detail="API key inválida o ausente."
        )


# ============================================================
# UTILIDADES
# ============================================================

def validar_ruta_base():
    if not RUTA_BASE.exists():
        raise HTTPException(
            status_code=503,
            detail=f"No se puede acceder a {RUTA_BASE}. Verifica que P: esté conectada.",
        )
    if not RUTA_BASE.is_dir():
        raise HTTPException(status_code=500, detail="La ruta configurada no es una carpeta.")


def normalizar_pc(codigo_pc: str) -> str:
    codigo = codigo_pc.strip().upper()

    if codigo.isdigit():
        codigo = f"PC{codigo}"

    if not re.fullmatch(r"PC\d+", codigo):
        raise HTTPException(
            status_code=400,
            detail="El código debe tener formato PC14774."
        )

    return codigo

def buscar_carpeta_pc(codigo_pc: str) -> Path:
    codigo = normalizar_pc(codigo_pc)
    validar_ruta_base()
    encontrados = []
    try:
        for carpeta in RUTA_BASE.iterdir():
            if not carpeta.is_dir():
                continue
            nombre = carpeta.name.strip().upper()
            if nombre == codigo or nombre.startswith((codigo + " ", codigo + "-")):
                encontrados.append(carpeta)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Sin permisos para leer la carpeta de cotizaciones.")

    if not encontrados:
        raise HTTPException(status_code=404, detail=f"No se encontró una carpeta para {codigo}.")

    encontrados.sort(key=lambda p: p.name.lower())
    return encontrados[0]


def buscar_carpeta_planos(carpeta_pc: Path) -> Path:
    try:
        for carpeta in carpeta_pc.iterdir():
            if carpeta.is_dir() and carpeta.name.strip().lower() == "01 - planos":
                return carpeta
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Sin permisos para leer {carpeta_pc.name}.")
    raise HTTPException(
        status_code=404,
        detail=f"No se encontró '01 - Planos' dentro de '{carpeta_pc.name}'.",
    )


def listar_pdfs(carpeta_planos: Path, recursivo: bool = False):
    patron = "**/*" if recursivo else "*"
    resultado = []
    try:
        for archivo in carpeta_planos.glob(patron):
            if archivo.is_file() and archivo.suffix.lower() == ".pdf":
                resultado.append({
                    "nombre": archivo.name,
                    "ruta_relativa": str(archivo.relative_to(RUTA_BASE)),
                    "ruta_en_planos": str(archivo.relative_to(carpeta_planos)),
                    "tamano_bytes": archivo.stat().st_size,
                })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Sin permisos para leer los planos.")
    resultado.sort(key=lambda x: x["ruta_relativa"].lower())
    return resultado


def buscar_pdf(carpeta_planos: Path, nombre_pdf: str) -> Path:
    nombre = nombre_pdf.replace("\\", "/").strip()
    if not nombre.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")

    base = carpeta_planos.resolve()

    # 1) Ruta relativa exacta dentro de 01 - Planos (bloquea "..")
    destino = (base / nombre).resolve()
    if base in destino.parents and destino.is_file():
        return destino

    # 2) Búsqueda por nombre en subcarpetas
    solo_nombre = Path(nombre).name.lower()
    try:
        for archivo in base.rglob("*"):
            if (
                archivo.is_file()
                and archivo.suffix.lower() == ".pdf"
                and archivo.name.lower() == solo_nombre
            ):
                return archivo
    except PermissionError:
        raise HTTPException(status_code=403, detail="Sin permisos para leer 01 - Planos.")

    raise HTTPException(status_code=404, detail=f"No se encontró el PDF '{nombre_pdf}'.")


# ============================================================
# ENDPOINTS PÚBLICOS (sin datos sensibles)
# ============================================================

@app.get("/", include_in_schema=False)
def inicio():
    return {"mensaje": "API Planos de Cotización funcionando", "documentacion": "/docs"}


@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
def robots():
    return "User-agent: *\nAllow: /\n"


# ============================================================
# ENDPOINTS PROTEGIDOS
# ============================================================

@app.get("/api/planos/estado", dependencies=[Depends(verificar_clave)],
         operation_id="estadoApi", summary="Estado de la API y de la unidad P:")
def estado():
    return {"accesible": RUTA_BASE.exists() and RUTA_BASE.is_dir()}


@app.get("/api/planos/buscar", dependencies=[Depends(verificar_clave)],
         operation_id="buscarPlanos", summary="Lista los PDF de un código PC")
def buscar_planos(
    codigo_pc: str = Query(..., description="Código de PC. Ejemplo: PC14774"),
    recursivo: bool = Query(False, description="Incluir subcarpetas de 01 - Planos"),
):
    codigo = normalizar_pc(codigo_pc)
    carpeta_pc = buscar_carpeta_pc(codigo)
    carpeta_planos = buscar_carpeta_planos(carpeta_pc)
    pdfs = listar_pdfs(carpeta_planos, recursivo)
    return {
        "codigo_pc": codigo,
        "carpeta_pc": carpeta_pc.name,
        "carpeta_planos": carpeta_planos.name,
        "total_pdfs": len(pdfs),
        "pdfs": pdfs,
    }


@app.get("/api/planos/{codigo_pc}/pdf/texto", dependencies=[Depends(verificar_clave)],
         operation_id="leerTextoPdf", summary="Extrae el texto de un PDF")
def leer_texto_pdf(
    codigo_pc: str,
    archivo: str = Query(..., description="Nombre del PDF o 'ruta_en_planos' devuelta por buscarPlanos"),
    max_caracteres: int = Query(50000, ge=1000, le=200000, description="Límite de texto devuelto"),
):
    codigo = normalizar_pc(codigo_pc)
    carpeta_planos = buscar_carpeta_planos(buscar_carpeta_pc(codigo))
    pdf = buscar_pdf(carpeta_planos, archivo)

    try:
        reader = PdfReader(str(pdf))
        partes = []
        for numero, pagina in enumerate(reader.pages, start=1):
            try:
                texto = pagina.extract_text() or ""
            except Exception:
                texto = ""
            if texto.strip():
                partes.append(f"[Página {numero}]\n{texto.strip()}")
        texto_final = "\n\n".join(partes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo PDF: {e}")

    truncado = len(texto_final) > max_caracteres
    return {
        "codigo_pc": codigo,
        "pdf": pdf.name,
        "paginas": len(reader.pages),
        "texto_extraido": bool(texto_final.strip()),
        "truncado": truncado,
        "texto": texto_final[:max_caracteres],
        "observacion": None if texto_final.strip() else
            "El PDF no contiene texto extraíble (probablemente escaneado o en imágenes).",
    }


@app.get(
    "/api/planos/{codigo_pc}/pdf/descargar",
    dependencies=[Depends(verificar_clave)],
    operation_id="descargarPdf",
    summary="Descarga un PDF",
    response_class=FileResponse,
    responses={
        200: {
            "description": "Archivo PDF",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        }
    },
)
def descargar_pdf(
    codigo_pc: str,
    archivo: str = Query(
        ...,
        description="Nombre del PDF o 'ruta_en_planos'"
    ),
):
    codigo = normalizar_pc(codigo_pc)

    carpeta_planos = buscar_carpeta_planos(
        buscar_carpeta_pc(codigo)
    )

    pdf = buscar_pdf(
        carpeta_planos,
        archivo
    )

    return FileResponse(
        path=str(pdf),
        filename=pdf.name,
        media_type="application/pdf"
    )

@app.get(
    "/api/ping",
    operation_id="pingApi",
    summary="Prueba pública de conectividad"
)
def ping():
    return {
        "ok": True,
        "mensaje": "GPT Action llegó correctamente a FastAPI"
    }
    
# ============================================================
# EJECUCIÓN DIRECTA (opcional; el .bat usa uvicorn)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8091, reload=False)