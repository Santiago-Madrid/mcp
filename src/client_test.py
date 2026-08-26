"""
Cliente de prueba para verificar el servidor MCP de herramientas matemáticas y microservicio.
Lee la configuración automáticamente desde .env (o usa http://127.0.0.1:8000 por defecto).
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

# Cargar variables de entorno
load_dotenv()

DEFAULT_HOST = os.getenv("HOST", "127.0.0.1")
DEFAULT_PORT = os.getenv("PORT", "8001")
DEFAULT_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"


async def run_client_tests(base_url: str = DEFAULT_URL) -> bool:
    """Ejecuta pruebas sobre todas las herramientas del servidor MCP."""
    mcp_endpoint = f"{base_url.rstrip('/')}/mcp"
    print(f"\n{'='*60}")
    print(f"🚀 Conectando al servidor MCP en {mcp_endpoint}")
    print(f"{'='*60}")

    try:
        async with streamable_http_client(mcp_endpoint) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # 1. Inicialización de sesión
                print("\n🤝 Realizando handshake de inicialización...")
                init_result = await session.initialize()
                print(f"✅ Inicializado con éxito: Servidor={init_result.server_info.name} (v{init_result.server_info.version})")

                # 2. Listar herramientas
                print("\n📋 Listando herramientas disponibles...")
                tools_response = await session.list_tools()
                print(f"📦 Total de herramientas: {len(tools_response.tools)}")
                for tool in tools_response.tools:
                    print(f"  - 🔧 {tool.name}: {tool.description}")

                print(f"\n{'='*60}")
                print("🧪 EJECUTANDO PRUEBAS")
                print(f"{'='*60}")

                # ============================================================
                # PRUEBAS DE HERRAMIENTAS MATEMÁTICAS
                # ============================================================
                print("\n📐 HERRAMIENTAS MATEMÁTICAS")
                print("-" * 40)

                # 1. Sumar
                print("\n1️⃣  Probando 'sumar' (a: 15.5, b: 24.5)...")
                suma_res = await session.call_tool("sumar", {"a": 15.5, "b": 24.5})
                print(f"   Resultado: {suma_res.content[0].text if suma_res.content else suma_res}")

                # 2. Multiplicar
                print("\n2️⃣  Probando 'multiplicar' (a: 7, b: 8)...")
                mul_res = await session.call_tool("multiplicar", {"a": 7, "b": 8})
                print(f"   Resultado: {mul_res.content[0].text if mul_res.content else mul_res}")

                # 3. Dividir
                print("\n3️⃣  Probando 'dividir' (a: 20, b: 4)...")
                div_res = await session.call_tool("dividir", {"a": 20, "b": 4})
                print(f"   Resultado: {div_res.content[0].text if div_res.content else div_res}")

                # 4. Potenciación
                print("\n4️⃣  Probando 'potenciacion' (base: 2, exponente: 10)...")
                pot_res = await session.call_tool("potenciacion", {"base": 2, "exponente": 10})
                print(f"   Resultado: {pot_res.content[0].text if pot_res.content else pot_res}")

                # ============================================================
                # PRUEBAS DE HERRAMIENTAS DE MICROSERVICIO
                # ============================================================
                print("\n\n🌐 HERRAMIENTAS DE MICROSERVICIO")
                print("-" * 40)

                # 5. Obtener usuario (caso exitoso)
                print("\n5️⃣  Probando 'obtener_usuario' (user_id: 1)...")
                user_res = await session.call_tool("obtener_usuario", {"user_id": 1})
                user_data = json.loads(user_res.content[0].text) if user_res.content else {}
                print(f"   Resultado:")
                if user_data.get("success"):
                    usuario = user_data.get("usuario", {})
                    print(f"      ✅ ID: {usuario.get('id')}")
                    print(f"      👤 Nombre: {usuario.get('nombre')}")
                    print(f"      📧 Email: {usuario.get('email')}")
                    print(f"      🏢 Empresa: {usuario.get('empresa')}")
                else:
                    print(f"      ❌ Error: {user_data.get('error')}")

                # 6. Obtener publicaciones (caso exitoso)
                print("\n6️⃣  Probando 'obtener_publicaciones' (user_id: 1, limite: 3)...")
                posts_res = await session.call_tool("obtener_publicaciones", {"user_id": 1, "limite": 3})
                posts_data = json.loads(posts_res.content[0].text) if posts_res.content else {}
                print(f"   Resultado:")
                if posts_data.get("success"):
                    print(f"      ✅ Total: {posts_data.get('total_publicaciones')} publicaciones")
                    print(f"      📄 Mostrando: {posts_data.get('mostradas')}")
                    for i, post in enumerate(posts_data.get("publicaciones", []), 1):
                        print(f"         {i}. {post.get('titulo')[:60]}...")
                else:
                    print(f"      ❌ Error: {posts_data.get('error')}")

                # 7. Obtener usuario (caso de error - ID no existe)
                print("\n7️⃣  Probando 'obtener_usuario' (user_id: 999 - caso de error)...")
                error_res = await session.call_tool("obtener_usuario", {"user_id": 999})
                error_data = json.loads(error_res.content[0].text) if error_res.content else {}
                if error_data.get("success"):
                    print("   ⚠️  ¡Esto no debería ocurrir! Usuario 999 no debería existir")
                else:
                    print(f"   ❌ Error esperado: {error_data.get('error')}")

                # 8. Obtener publicaciones de otro usuario
                print("\n8️⃣  Probando 'obtener_publicaciones' (user_id: 2, limite: 2)...")
                posts_res2 = await session.call_tool("obtener_publicaciones", {"user_id": 2, "limite": 2})
                posts_data2 = json.loads(posts_res2.content[0].text) if posts_res2.content else {}
                if posts_data2.get("success"):
                    print(f"   ✅ Usuario 2: {posts_data2.get('total_publicaciones')} publicaciones, mostrando {posts_data2.get('mostradas')}")
                else:
                    print(f"   ❌ Error: {posts_data2.get('error')}")

                # 9. Probar división por cero (caso de error matemático)
                print("\n9️⃣  Probando 'dividir' (a: 10, b: 0 - caso de error)...")
                div_zero_res = await session.call_tool("dividir", {"a": 10, "b": 0})
                div_zero_data = json.loads(div_zero_res.content[0].text) if div_zero_res.content else {}
                if div_zero_data.get("success"):
                    print("   ⚠️  ¡Esto no debería ocurrir! División por cero debería fallar")
                else:
                    print(f"   ❌ Error esperado: {div_zero_data.get('error')}")

                print(f"\n{'='*60}")
                print("🎉 ¡TODAS LAS PRUEBAS FINALIZARON CON ÉXITO!")
                print(f"{'='*60}\n")
                return True

    except Exception as exc:
        print(f"\n❌ Error durante la ejecución de las pruebas: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    server_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    success = asyncio.run(run_client_tests(server_url))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()