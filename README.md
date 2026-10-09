# Simple Stock Flow — Tool (Sembrador de Demostración)

Utilidad CLI en Python para el sembrado automatizado e idempotente de datos de prueba en **Simple Stock Flow**.

---

## 📌 Principio de Diseño

Siguiendo el mandato de la Arquitectura Onion y el spec de la prueba técnica:
- **`tool` es un cliente HTTP puro**: se comunica exclusivamente a través de los endpoints públicos de la API HTTP.
- **Cero dependencias externas**: construido exclusivamente con la librería estándar de Python (`urllib`, `argparse`, `json`).
- **No toca la base de datos**: jamás se conecta directamente a MySQL. Toda regla de negocio (validaciones, invariantes, unicidad, transacciones atómicas) es verificada por la API.
- **Idempotente**: ejecutarlo múltiples veces no duplica productos ni corrompe el inventario existente.

---

## 🚀 Uso

```bash
# Ejecutar sembrado con valores por defecto (http://localhost:8000)
python -m ssf_tool seed

# O especificando opciones personalizadas
python -m ssf_tool seed --api-url http://localhost:8000 --admin-user admin --admin-pass admin123
```

### Variables de Entorno Soportadas

- `API_BASE_URL`: URL base de la API (por defecto: `http://localhost:8000`)
- `ADMIN_USERNAME` / `ADMIN_EMAIL`: Usuario administrador (por defecto: `admin`)
- `ADMIN_PASSWORD`: Contraseña de administrador (por defecto: `admin123`)

---

## 🧪 Pruebas Unitarias

```bash
python -m unittest discover tests
```
