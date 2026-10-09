import sys
from typing import List, Dict, Any
from ssf_tool.client import ApiClient, ApiClientError

# 1x1 valid PNG in raw bytes
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360606060000000050001a7df9d0000000049454e44ae"
    "426082"
)

DEMO_PRODUCTS = [
    {
        "name": "Taladro Percutor DeWalt 20V",
        "price": 185.00,
        "stock": 15,
        "category_name": "Herramientas",
    },
    {
        "name": "Juego de Destornilladores Stanley (6 pcs)",
        "price": 35.50,
        "stock": 25,
        "category_name": "Herramientas",
    },
    {
        "name": "Pintura Vinilo Tipo 1 Blanco Corona (Galón)",
        "price": 48.00,
        "stock": 20,
        "category_name": "Pinturas",
    },
    {
        "name": "Esmalte Sintético Negro Brillante (1/4 Gal)",
        "price": 22.90,
        "stock": 12,
        "category_name": "Pinturas",
    },
    {
        "name": "Cinta Métrica 5m Autolock",
        "price": 14.50,
        "stock": 40,
        "category_name": "Herramientas",
    },
    {
        "name": "Brocha Profesional 3 Pulgadas",
        "price": 9.99,
        "stock": 30,
        "category_name": "Pinturas",
    },
]

def run_seed(api_url: str, admin_user: str, admin_pass: str) -> None:
    client = ApiClient(api_url)
    print(f"🚀 Conectando a Simple Stock Flow API en: {api_url}")

    # 1. Health check
    try:
        health = client.get("/health")
        print(f"   ✓ Health check OK: {health.get('service', 'api')}")
    except Exception as e:
        print(f"   ⚠️ Health check advertencia: {e} (Continuando...)")

    # 2. Login como administrador
    print(f"\n🔑 Iniciando sesión como administrador ({admin_user})...")
    try:
        auth_res = client.post("/api/auth/login", {
            "username": admin_user,
            "password": admin_pass,
        })
        admin_token = auth_res["token"]
        client.set_token(admin_token)
        print("   ✓ Sesión de administrador iniciada correctamente.")
    except ApiClientError as e:
        print(f"   ❌ Error al autenticar admin: {e}")
        sys.exit(1)

    # 3. Obtener categorías existentes
    print("\n📂 Consultando categorías...")
    try:
        categories = client.get("/api/categories")
        cat_map: Dict[str, str] = {c["name"].lower(): c["id"] for c in categories}
        print(f"   ✓ {len(categories)} categorías encontradas: {', '.join(cat_map.keys())}")
    except ApiClientError as e:
        print(f"   ❌ Error al obtener categorías: {e}")
        sys.exit(1)

    # 4. Consultar productos existentes para garantizar idempotencia
    print("\n📦 Verificando inventario actual...")
    existing_prods = client.get("/api/products", query={"perPage": 100})
    existing_names = {p["name"].lower(): p for p in existing_prods.get("items", [])}
    print(f"   ✓ {len(existing_names)} productos ya existentes en base de datos.")

    created_products: List[Dict[str, Any]] = []

    # 5. Sembrar productos
    for p_def in DEMO_PRODUCTS:
        p_name = p_def["name"]
        cat_name = p_def["category_name"].lower()
        cat_id = cat_map.get(cat_name) or list(cat_map.values())[0]

        if p_name.lower() in existing_names:
            print(f"   ℹ️ Producto ya existe: '{p_name}' (Omitiendo creación)")
            prod = existing_names[p_name.lower()]
        else:
            print(f"   ➕ Creando producto: '{p_name}' (${p_def['price']} COP, stock: {p_def['stock']})...")
            prod = client.post("/api/products", {
                "name": p_name,
                "price": p_def["price"],
                "stock": p_def["stock"],
                "categoryId": cat_id,
            })
            print(f"      ✓ Creado con ID: {prod['id']}")

        # Subir imagen si no tiene
        if not prod.get("imageKey"):
            try:
                print(f"      🖼️ Subiendo imagen demo para '{p_name}'...")
                updated_prod = client.post_multipart(
                    f"/api/products/{prod['id']}/image",
                    field_name="image",
                    filename=f"{prod['id'][:8]}.png",
                    file_bytes=TINY_PNG,
                    content_type="image/png"
                )
                prod["imageKey"] = updated_prod.get("imageKey")
                print(f"      ✓ Imagen cargada (key: {prod['imageKey']})")
            except Exception as e:
                print(f"      ⚠️ No se pudo cargar imagen: {e}")

        created_products.append(prod)

    # 6. Alta de vendedor demo
    seller_user = "carlos"
    seller_pass = "secret123"
    print(f"\n👤 Registrando vendedor demo '{seller_user}'...")
    try:
        client.post("/api/auth/register", {
            "username": seller_user,
            "password": seller_pass,
        })
        print(f"   ✓ Vendedor '{seller_user}' registrado exitosamente.")
    except ApiClientError as e:
        if e.status == 409:
            print(f"   ℹ️ Vendedor '{seller_user}' ya existe (Omitiendo creación).")
        else:
            print(f"   ⚠️ Registro de vendedor: {e}")

    # 7. Login como vendedor para registrar ventas
    print(f"\n🛍️ Iniciando sesión como vendedor '{seller_user}'...")
    seller_client = ApiClient(api_url)
    try:
        seller_auth = seller_client.post("/api/auth/login", {
            "username": seller_user,
            "password": seller_pass,
        })
        seller_client.set_token(seller_auth["token"])
        print("   ✓ Sesión de vendedor iniciada.")
    except ApiClientError as e:
        print(f"   ⚠️ No se pudo iniciar sesión como vendedor: {e}. Usando admin.")
        seller_client.set_token(admin_token)

    # 8. Registrar ventas de demostración
    print("\n🛒 Registrando ventas de prueba atómicas...")
    sales_to_place = [
        [{"productId": created_products[0]["id"], "quantity": 1}],
        [
            {"productId": created_products[1]["id"], "quantity": 2},
            {"productId": created_products[4]["id"], "quantity": 1},
        ],
        [
            {"productId": created_products[2]["id"], "quantity": 1},
            {"productId": created_products[3]["id"], "quantity": 2},
        ],
    ]

    for idx, sale_items in enumerate(sales_to_place, 1):
        try:
            sale_res = seller_client.post("/api/sales", {"items": sale_items})
            print(f"   ✓ Venta #{idx} confirmada. ID: {sale_res['id']} · Total: ${sale_res['total']} COP ({len(sale_res['items'])} líneas)")
        except ApiClientError as e:
            print(f"   ⚠️ Venta #{idx} falló: {e}")

    # 9. Consultar reporte de ventas consolidado (con admin)
    print("\n📊 Consultando reporte consolidado de ventas...")
    try:
        report = client.get("/api/reports/sales", query={"from": "2026-01-01", "to": "2026-12-31"})
        print(f"   ✓ Total Ventas Confirmadas: {report['totalSalesCount']}")
        print(f"   ✓ Gran Total Ingresos:     ${report['grandTotal']} COP")
        print("\n   Top Productos Vendidos:")
        for r_item in report.get("items", []):
            print(f"     • {r_item['productName']} ({r_item['categoryName']}): {r_item['unitsSold']} un. -> ${r_item['revenue']} COP")
    except Exception as e:
        print(f"   ⚠️ No se pudo consultar reporte: {e}")

    print("\n✨ ¡Sembrado de datos finalizado con éxito! El sistema está listo para demostración.")
