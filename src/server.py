"""
Servidor MCP en Python con herramientas para World Dance API.
Incluye autenticación automática con Bearer Token.
"""

import json
import os
import sys
from typing import Any
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv
from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse

# Cargar variables de entorno
load_dotenv()

# Configuración
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))
TRANSPORT = os.getenv("TRANSPORT", "streamable-http").lower().strip()
WORLD_DANCE_API = os.getenv("WORLD_DANCE_API", "https://api.worlddance.win/api/v1")

# Credenciales
EMAIL = os.getenv("WORLD_DANCE_EMAIL", "").strip('"')
PASSWORD = os.getenv("WORLD_DANCE_PASSWORD", "").strip('"')

# Token cache
_token_cache = {
    "token": None,
    "expires_at": None
}


async def get_token() -> str:
    """Obtiene un token de autenticación."""
    global _token_cache
    
    # Verificar si el token guardado sigue siendo válido
    if _token_cache["token"] and _token_cache["expires_at"]:
        if datetime.now() < _token_cache["expires_at"]:
            print(f"   🔑 Usando token guardado")
            return _token_cache["token"]
    
    if not EMAIL or not PASSWORD:
        print(f"   ❌ ERROR: Credenciales no configuradas")
        return None
    
    print(f"   🔐 Intentando login con: {EMAIL}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{WORLD_DANCE_API}/auth/login",
                json={"email": EMAIL, "password": PASSWORD}
            )
            
            if response.status_code in [200, 202]:
                data = response.json()
                token = data.get("data", {}).get("jwt")
                
                if token:
                    _token_cache["token"] = token
                    _token_cache["expires_at"] = datetime.now() + timedelta(hours=24)
                    print(f"   ✅ Token obtenido exitosamente")
                    return token
                else:
                    print(f"   ❌ No se encontró token en la respuesta")
                    return None
            else:
                print(f"   ❌ Error en login: HTTP {response.status_code}")
                return None
                
    except Exception as exc:
        print(f"   ❌ Error en login: {str(exc)}")
        return None


async def get_headers() -> dict[str, str]:
    """Retorna los headers con autenticación."""
    token = await get_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def create_server() -> MCPServer:
    """Crea y configura el servidor MCP con herramientas para World Dance."""
    server = MCPServer(
        name="WorldDanceMCPServer",
        version="1.0.0",
        description="Servidor MCP para el microservicio World Dance",
        instructions="Este servidor permite crear eventos en World Dance.",
    )

    # =============================================================
    # HERRAMIENTA 1: CREAR EVENTO
    # =============================================================
    @server.tool(
        name="crear_evento",
        description="Crea un nuevo evento en World Dance. Requiere ownerId, nombre, descripción, fechas, ubicación y estado.",
    )
    async def crear_evento(
        ownerId: int,
        name: str,
        description: str,
        startDate: str,
        endDate: str,
        location: str,
        status: str = "ACTIVE"
    ) -> dict[str, Any]:
        """
        Crea un nuevo evento en World Dance.
        
        Args:
            ownerId: ID del organizador del evento
            name: Nombre del evento
            description: Descripción del evento
            startDate: Fecha de inicio (formato: YYYY-MM-DDTHH:MM:SS)
            endDate: Fecha de finalización (formato: YYYY-MM-DDTHH:MM:SS)
            location: Ubicación del evento
            status: Estado del evento (ACTIVE, CANCELLED, FINISHED)
            
        Returns:
            dict: Información del evento creado
        """
        print(f"\n👉 [MCP Tool] Ejecutando crear_evento")
        print(f"   📌 Nombre: {name}")
        print(f"   🏢 Owner ID: {ownerId}")
        print(f"   📍 Ubicación: {location}")
        
        # Validar formato de fechas
        try:
            datetime.fromisoformat(startDate.replace('Z', '+00:00'))
            datetime.fromisoformat(endDate.replace('Z', '+00:00'))
        except ValueError:
            return {
                "success": False,
                "error": "Formato de fecha inválido. Usa: YYYY-MM-DDTHH:MM:SS"
            }
        
        payload = {
            "ownerId": ownerId,
            "name": name,
            "description": description,
            "startDate": startDate,
            "endDate": endDate,
            "location": location,
            "status": status
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = await get_headers()
                if not headers.get("Authorization"):
                    return {
                        "success": False,
                        "error": "No se pudo obtener el token de autenticación"
                    }
                
                response = await client.post(
                    f"{WORLD_DANCE_API}/events/create",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "mensaje": "Evento creado exitosamente",
                        "evento": data,
                        "codigo_estado": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error al crear el evento: HTTP {response.status_code}",
                        "detalle": response.text,
                        "codigo_estado": response.status_code
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Timeout: El microservicio no respondió en el tiempo esperado"
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Error inesperado: {str(exc)}"
            }

    # =============================================================
    # HERRAMIENTA 2: SUMAR (para pruebas)
    # =============================================================
    @server.tool(
        name="sumar",
        description="Suma dos números (a + b) y devuelve el resultado.",
    )
    def sumar(a: float, b: float) -> dict[str, Any]:
        """Suma dos números."""
        print(f"👉 [MCP Tool] Ejecutando sumar: {a} + {b}")
        return {
            "success": True,
            "operacion": "suma",
            "a": a,
            "b": b,
            "resultado": a + b
        }

    # =============================================================
    # RECURSO DE ESTADO
    # =============================================================
    @server.resource(
        "system://status",
        name="server_status",
        description="Estado del servidor MCP",
        mime_type="application/json",
    )
    def server_status() -> str:
        return json.dumps({
            "status": "healthy",
            "server": "WorldDanceMCPServer",
            "version": "1.0.0",
            "transport": TRANSPORT,
            "world_dance_api": WORLD_DANCE_API,
            "auth_configured": bool(EMAIL and PASSWORD),
            "tools": ["crear_evento", "sumar"],
        }, indent=2)

    @server.custom_route("/", methods=["GET"])
    async def root_handler(request: Request) -> JSONResponse:
        return JSONResponse({
            "name": "WorldDanceMCPServer",
            "version": "1.0.0",
            "status": "online",
            "transport": TRANSPORT,
            "world_dance_api": WORLD_DANCE_API,
            "tools": ["crear_evento", "sumar"],
        })

    return server


def main() -> None:
    server = create_server()
    print(f"\n{'='*60}")
    print(f"🚀 Servidor MCP 'WorldDanceMCPServer' v1.0.0")
    print(f"📍 http://{HOST}:{PORT} (transporte: {TRANSPORT})")
    print(f"📡 World Dance API: {WORLD_DANCE_API}")
    print(f"🔐 Autenticación: {'✅ Configurada' if (EMAIL and PASSWORD) else '❌ No configurada'}")
    print(f"{'='*60}\n")

    if TRANSPORT == "sse":
        server.run(transport="sse", host=HOST, port=PORT)
    elif TRANSPORT == "streamable-http":
        server.run(transport="streamable-http", host=HOST, port=PORT)
    elif TRANSPORT == "stdio":
        server.run(transport="stdio")
    else:
        print(f"❌ Transporte '{TRANSPORT}' no válido")
        sys.exit(1)


if __name__ == "__main__":
    main()