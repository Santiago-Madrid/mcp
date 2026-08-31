"""
Cliente de prueba para el servidor MCP de World Dance.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()
DEFAULT_URL = f"http://127.0.0.1:8001"


async def run_client_tests(base_url: str = DEFAULT_URL) -> bool:
    """Ejecuta pruebas sobre las herramientas de World Dance."""
    mcp_endpoint = f"{base_url.rstrip('/')}/mcp"
    print(f"\n{'='*60}")
    print(f"🚀 Conectando al servidor MCP en {mcp_endpoint}")
    print(f"{'='*60}")

    try:
        async with streamable_http_client(mcp_endpoint) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                print("\n🤝 Realizando handshake...")
                init_result = await session.initialize()
                print(f"✅ Inicializado: {init_result.server_info.name}")

                print("\n📋 Herramientas disponibles:")
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    print(f"  - 🔧 {tool.name}: {tool.description}")

                print(f"\n{'='*60}")
                print("🧪 PRUEBA: CREAR EVENTO")
                print(f"{'='*60}")

                # 🔥 USAR FECHAS FUTURAS (octubre 2026)
                ahora = datetime.now()
                # Sumar 45 días para asegurar que es futuro
                fecha_futura = ahora + timedelta(days=45)
                
                fecha_inicio = f"{fecha_futura.year}-{fecha_futura.month:02d}-{fecha_futura.day:02d}T09:00:00"
                fecha_fin = f"{fecha_futura.year}-{fecha_futura.month:02d}-{fecha_futura.day:02d}T18:00:00"
                nombre_evento = f"Evento MCP {fecha_futura.strftime('%d%m%Y')}"
                
                print(f"\n📝 Datos del evento:")
                print(f"   📌 Nombre: {nombre_evento}")
                print(f"   🏢 Owner ID: 7")
                print(f"   📍 Ubicación: Armenia, Quindío")
                print(f"   📅 Inicio: {fecha_inicio}")
                print(f"   📅 Fin: {fecha_fin}")
                print(f"   📊 Estado: ACTIVE")
                print(f"   📆 Fecha actual del sistema: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")

                evento_res = await session.call_tool("crear_evento", {
                    "ownerId": 7,
                    "name": nombre_evento,
                    "description": f"Evento creado desde servidor MCP el {ahora.strftime('%d/%m/%Y')}",
                    "startDate": fecha_inicio,
                    "endDate": fecha_fin,
                    "location": "Armenia, Quindío",
                    "status": "ACTIVE"
                })
                
                evento_data = json.loads(evento_res.content[0].text) if evento_res.content else {}
                
                print(f"\n📥 Respuesta del servidor:")
                print(json.dumps(evento_data, indent=2))
                
                if evento_data.get("success"):
                    evento = evento_data.get("evento", {})
                    print(f"\n✅ ¡Evento creado exitosamente!")
                    print(f"   🆔 ID: {evento.get('id') or evento.get('eventoId') or 'N/A'}")
                    print(f"   📌 Nombre: {evento.get('name') or 'N/A'}")
                    print(f"   📍 Ubicación: {evento.get('location') or 'N/A'}")
                else:
                    print(f"\n❌ Error: {evento_data.get('error')}")
                    if "detalle" in evento_data:
                        detalle = evento_data.get('detalle')
                        print(f"   📝 Detalle: {detalle}")
                        # Intentar parsear el detalle si es JSON
                        try:
                            detalle_json = json.loads(detalle)
                            if "message" in detalle_json:
                                print(f"   💡 Mensaje: {detalle_json.get('message')}")
                        except:
                            pass

                # Prueba de sumar
                print(f"\n{'='*60}")
                print("🧪 PRUEBA: SUMAR")
                print(f"{'='*60}")
                
                sum_res = await session.call_tool("sumar", {"a": 10, "b": 20})
                sum_data = json.loads(sum_res.content[0].text) if sum_res.content else {}
                if sum_data.get("success"):
                    print(f"   ✅ {sum_data.get('a')} + {sum_data.get('b')} = {sum_data.get('resultado')}")

                print(f"\n{'='*60}")
                print("🎉 ¡PRUEBAS COMPLETADAS!")
                print(f"{'='*60}\n")
                return True

    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        import traceback
        traceback.print_exc()
        return False


def main():
    success = asyncio.run(run_client_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()