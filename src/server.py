"""
Servidor MCP en Python con transporte HTTP (SSE) y herramientas matemáticas básicas.
Además incluye herramientas para consultar microservicios externos.
"""

import json
import os
import sys
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración leída desde variables de entorno (.env)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
TRANSPORT = os.getenv("TRANSPORT", "sse").lower().strip()
MICROSERVICE_URL = os.getenv("MICROSERVICE_URL", "https://jsonplaceholder.typicode.com")


def create_server() -> MCPServer:
    """Crea y configura el servidor MCP con herramientas matemáticas y de microservicio."""
    server = MCPServer(
        name="MathAndMicroserviceTools",
        version="1.0.0",
        description="Servidor MCP con herramientas matemáticas y consultas a microservicios",
        instructions="Este servidor provee herramientas para sumar, multiplicar, calcular potencias y consultar microservicios externos.",
    )

    # =============================================================
    # HERRAMIENTAS MATEMÁTICAS (existentes)
    # =============================================================

    @server.tool(
        name="sumar",
        description="Suma dos números (a + b) y devuelve el resultado.",
    )
    def sumar(a: float, b: float) -> dict[str, Any]:
        """Suma dos números (a + b)."""
        print(f"👉 [MCP Tool] Ejecutando sumar: a={a}, b={b}")
        resultado = a + b  # Corregido: sin +5 extra
        return {
            "success": True,
            "operacion": "suma",
            "a": a,
            "b": b,
            "resultado": resultado,
        }

    @server.tool(
        name="multiplicar",
        description="Multiplica dos números (a * b) y devuelve el resultado.",
    )
    def multiplicar(a: float, b: float) -> dict[str, Any]:
        """Multiplica dos números (a * b)."""
        print(f"👉 [MCP Tool] Ejecutando multiplicar: a={a}, b={b}")
        resultado = a * b
        return {
            "success": True,
            "operacion": "multiplicacion",
            "a": a,
            "b": b,
            "resultado": resultado,
        }

    @server.tool(
        name="dividir",
        description="Divide dos números (a / b) y devuelve el resultado.",
    )
    def dividir(a: float, b: float) -> dict[str, Any]:
        """Divide dos números (a / b)."""
        print(f"👉 [MCP Tool] Ejecutando dividir: a={a}, b={b}")
        if b == 0:
            return {"success": False, "error": "No se puede dividir por cero"}
        resultado = a / b
        return {
            "success": True,
            "operacion": "division",
            "a": a,
            "b": b,
            "resultado": resultado,
        }

    @server.tool(
        name="potenciacion",
        description="Calcula la potencia de un número base elevado a un exponente (base ** exponente).",
    )
    def potenciacion(base: float, exponente: float) -> dict[str, Any]:
        """Calcula la potenciación (base ** exponente)."""
        print(f"👉 [MCP Tool] Ejecutando potenciacion: base={base}, exponente={exponente}")
        try:
            if exponente > 10000:
                return {
                    "success": False,
                    "error": "Exponente demasiado grande (máximo permitido: 10000).",
                }
            resultado = base ** exponente
            return {
                "success": True,
                "operacion": "potenciacion",
                "base": base,
                "exponente": exponente,
                "resultado": resultado,
            }
        except OverflowError:
            return {"success": False, "error": "Resultado demasiado grande (desbordamiento numérico)."}
        except Exception as exc:
            return {"success": False, "error": f"Error en la potenciación: {str(exc)}"}

    # =============================================================
    # NUEVAS HERRAMIENTAS: CONSULTA A MICROSERVICIO
    # =============================================================

    # -------------------------------------------------------------
    # HERRAMIENTA 1: OBTENER USUARIO
    # -------------------------------------------------------------
    @server.tool(
        name="obtener_usuario",
        description="Obtiene información de un usuario desde el microservicio externo.",
    )
    async def obtener_usuario(user_id: int) -> dict[str, Any]:
        """
        Obtiene información de un usuario desde el microservicio.
        
        Args:
            user_id: ID del usuario a consultar (ej: 1, 2, 3...)
            
        Returns:
            dict: Información del usuario o mensaje de error
        """
        print(f"👉 [MCP Tool] Ejecutando obtener_usuario: user_id={user_id}")
        print(f"   🌐 Consultando: {MICROSERVICE_URL}/users/{user_id}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{MICROSERVICE_URL}/users/{user_id}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "success": True,
                        "usuario": {
                            "id": user_data.get("id"),
                            "nombre": user_data.get("name"),
                            "username": user_data.get("username"),
                            "email": user_data.get("email"),
                            "telefono": user_data.get("phone"),
                            "sitio_web": user_data.get("website"),
                            "empresa": user_data.get("company", {}).get("name"),
                        },
                        "codigo_estado": response.status_code,
                        "mensaje": f"Usuario {user_id} obtenido exitosamente"
                    }
                elif response.status_code == 404:
                    return {
                        "success": False,
                        "error": f"Usuario con ID {user_id} no encontrado",
                        "codigo_estado": 404
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error en la consulta: HTTP {response.status_code}",
                        "codigo_estado": response.status_code
                    }
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Timeout: El microservicio no respondió en el tiempo esperado"
            }
        except httpx.ConnectError:
            return {
                "success": False,
                "error": f"No se pudo conectar al microservicio en {MICROSERVICE_URL}"
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Error inesperado: {str(exc)}"
            }

    # -------------------------------------------------------------
    # HERRAMIENTA 2: OBTENER PUBLICACIONES DEL USUARIO
    # -------------------------------------------------------------
    @server.tool(
        name="obtener_publicaciones",
        description="Obtiene las publicaciones (posts) de un usuario desde el microservicio externo.",
    )
    async def obtener_publicaciones(user_id: int, limite: int = 5) -> dict[str, Any]:
        """
        Obtiene las publicaciones de un usuario desde el microservicio.
        
        Args:
            user_id: ID del usuario
            limite: Número máximo de publicaciones a retornar (por defecto 5)
            
        Returns:
            dict: Lista de publicaciones o mensaje de error
        """
        print(f"👉 [MCP Tool] Ejecutando obtener_publicaciones: user_id={user_id}, limite={limite}")
        print(f"   🌐 Consultando: {MICROSERVICE_URL}/posts?userId={user_id}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{MICROSERVICE_URL}/posts",
                    params={"userId": user_id}
                )
                
                if response.status_code == 200:
                    posts = response.json()
                    total = len(posts)
                    
                    # Limitar el número de publicaciones
                    posts_limitados = posts[:limite]
                    
                    # Formatear las publicaciones
                    publicaciones = []
                    for post in posts_limitados:
                        publicaciones.append({
                            "id": post.get("id"),
                            "titulo": post.get("title"),
                            "contenido": post.get("body")[:150] + "..." if len(post.get("body", "")) > 150 else post.get("body", ""),
                            "completo": len(post.get("body", "")) <= 150
                        })
                    
                    return {
                        "success": True,
                        "user_id": user_id,
                        "total_publicaciones": total,
                        "mostradas": len(publicaciones),
                        "publicaciones": publicaciones,
                        "codigo_estado": response.status_code,
                        "mensaje": f"Se encontraron {total} publicaciones para el usuario {user_id}"
                    }
                elif response.status_code == 404:
                    return {
                        "success": False,
                        "error": f"Usuario con ID {user_id} no encontrado",
                        "codigo_estado": 404
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error en la consulta: HTTP {response.status_code}",
                        "codigo_estado": response.status_code
                    }
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Timeout: El microservicio no respondió en el tiempo esperado"
            }
        except httpx.ConnectError:
            return {
                "success": False,
                "error": f"No se pudo conectar al microservicio en {MICROSERVICE_URL}"
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Error inesperado: {str(exc)}"
            }

    # =============================================================
    # RECURSOS Y RUTAS
    # =============================================================

    @server.resource(
        "system://status",
        name="server_status",
        description="Estado y herramientas disponibles en el servidor MCP",
        mime_type="application/json",
    )
    def server_status() -> str:
        """Retorna un recurso JSON informativo."""
        return json.dumps(
            {
                "status": "healthy",
                "server": "MathAndMicroserviceTools",
                "version": "1.0.0",
                "transport": TRANSPORT,
                "microservice_url": MICROSERVICE_URL,
                "tools": [
                    "sumar", 
                    "multiplicar", 
                    "dividir",
                    "potenciacion", 
                    "obtener_usuario", 
                    "obtener_publicaciones"
                ],
            },
            indent=2,
        )

    @server.custom_route("/", methods=["GET"])
    async def root_handler(request: Request) -> JSONResponse:
        """Endpoint HTTP informativo en la raíz."""
        return JSONResponse(
            {
                "name": "MathAndMicroserviceTools",
                "version": "1.0.0",
                "protocol": "Model Context Protocol (MCP)",
                "status": "online",
                "transport": TRANSPORT,
                "microservice_url": MICROSERVICE_URL,
                "endpoints": {
                    "sse": "/sse",
                    "messages": "/messages/",
                    "streamable_http": "/mcp",
                },
                "available_tools": [
                    "sumar",
                    "multiplicar",
                    "dividir",
                    "potenciacion",
                    "obtener_usuario",
                    "obtener_publicaciones",
                ],
            }
        )

    return server


def main() -> None:
    """Punto de entrada principal para ejecutar el servidor MCP."""
    server = create_server()
    print(f"🚀 Iniciando servidor MCP '{server.name}' v{server.version}")
    print(f"📍 http://{HOST}:{PORT} (transporte: {TRANSPORT})")
    print(f"📡 Microservicio configurado: {MICROSERVICE_URL}")

    if TRANSPORT == "sse":
        server.run(transport="sse", host=HOST, port=PORT)
    elif TRANSPORT == "streamable-http":
        server.run(transport="streamable-http", host=HOST, port=PORT)
    elif TRANSPORT == "stdio":
        server.run(transport="stdio")
    else:
        print(f"❌ Transporte '{TRANSPORT}' no válido. Opciones: sse, streamable-http, stdio")
        sys.exit(1)


if __name__ == "__main__":
    main()


# Agregar al server.py
@server.tool(
    name="obtener_comentarios",
    description="Obtiene los comentarios de una publicación",
)
async def obtener_comentarios(post_id: int, limite: int = 5) -> dict[str, Any]:
    """Obtiene comentarios de una publicación."""
    # Implementación similar a obtener_publicaciones
    pass

@server.tool(
    name="crear_usuario",
    description="Crea un nuevo usuario en el microservicio",
)
async def crear_usuario(nombre: str, email: str) -> dict[str, Any]:
    """Crea un nuevo usuario."""
    # Implementación POST al microservicio
    pass