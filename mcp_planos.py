import os
from urllib.parse import quote

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

# ============================================================
# CONFIGURACIÓN
# ============================================================

API_LOCAL = os.environ.get(
    "PLANOS_API_LOCAL_URL",
    "http://127.0.0.1:8091"
).rstrip("/")

API_KEY = os.environ.get("API_KEY", "")

if len(API_KEY) < 20:
    raise RuntimeError(
        "Define API_KEY antes de iniciar el servidor MCP."
    )


# ============================================================
# SERVIDOR MCP
# ============================================================

security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
        "mcp-planos.origamidemetalicos.com",
        "mcp-planos.origamidemetalicos.com:*",
    ],
    allowed_origins=[
        "https://mcp-planos.origamidemetalicos.com",
    ],
)

mcp = MCPServer("Planos Demetalicos")

# ============================================================
# CLIENTE INTERNO HACIA FASTAPI
# ============================================================

def llamar_api(
    ruta: str,
    parametros: dict | None = None,
    timeout: float = 60.0,
) -> dict:
    headers = {
        "X-API-Key": API_KEY
    }

    try:
        with httpx.Client(timeout=timeout) as cliente:
            respuesta = cliente.get(
                f"{API_LOCAL}{ruta}",
                params=parametros,
                headers=headers,
            )

    except httpx.RequestError as exc:
        raise RuntimeError(
            f"No fue posible conectar con la API de planos: {exc}"
        ) from exc

    if respuesta.is_error:
        try:
            datos_error = respuesta.json()
            detalle = datos_error.get("detail", datos_error)
        except Exception:
            detalle = respuesta.text

        raise RuntimeError(
            f"API Planos respondió HTTP "
            f"{respuesta.status_code}: {detalle}"
        )

    try:
        return respuesta.json()
    except Exception as exc:
        raise RuntimeError(
            "La API de planos devolvió una respuesta no JSON."
        ) from exc


# ============================================================
# HERRAMIENTAS MCP
# ============================================================

@mcp.tool()
def estado_api() -> dict:
    """
    Comprueba si la API de planos está funcionando y si la
    unidad/carpeta de planos está accesible.
    """
    return llamar_api(
        "/api/planos/estado"
    )


@mcp.tool()
def buscar_planos(
    codigo_pc: str,
    recursivo: bool = False,
) -> dict:
    """
    Busca los PDF correspondientes a una cotización PC.

    codigo_pc:
        Código de cotización, por ejemplo PC14774 o 14774.

    recursivo:
        Si es True, incluye PDFs existentes en subcarpetas
        dentro de 01 - Planos.
    """

    resultado = llamar_api(
        "/api/planos/buscar",
        {
            "codigo_pc": codigo_pc,
            "recursivo": str(recursivo).lower(),
        },
    )

    # No necesitamos enviar al modelo rutas internas innecesarias.
    for pdf in resultado.get("pdfs", []):
        pdf.pop("ruta_relativa", None)

    return resultado


@mcp.tool()
def leer_texto_pdf(
    codigo_pc: str,
    archivo: str,
    max_caracteres: int = 50000,
) -> dict:
    """
    Extrae el texto de un PDF previamente encontrado con
    buscar_planos.

    Usa exactamente el valor de 'ruta_en_planos' o 'nombre'
    devuelto por buscar_planos.

    max_caracteres debe estar entre 1000 y 200000.
    """

    if max_caracteres < 1000 or max_caracteres > 200000:
        raise ValueError(
            "max_caracteres debe estar entre 1000 y 200000."
        )

    codigo_seguro = quote(
        codigo_pc.strip(),
        safe=""
    )

    return llamar_api(
        f"/api/planos/{codigo_seguro}/pdf/texto",
        {
            "archivo": archivo,
            "max_caracteres": max_caracteres,
        },
        timeout=120.0,
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8092,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        transport_security=security,
    )