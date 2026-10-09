import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ssf_tool.seeder import run_seed

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ssf_tool",
        description="Utilidad CLI para Simple Stock Flow: sembrador de demostración y pruebas"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcomando 'seed'
    seed_parser = subparsers.add_parser(
        "seed",
        help="Poblar el sistema con productos, imágenes y ventas de prueba vía HTTP"
    )
    seed_parser.add_argument(
        "--api-url",
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="URL base de la API HTTP (defecto: http://localhost:8000)"
    )
    seed_parser.add_argument(
        "--admin-user",
        default=os.getenv("ADMIN_USERNAME", os.getenv("ADMIN_EMAIL", "admin")),
        help="Usuario administrador para autenticación (defecto: admin)"
    )
    seed_parser.add_argument(
        "--admin-pass",
        default=os.getenv("ADMIN_PASSWORD", "admin123"),
        help="Contraseña del usuario administrador (defecto: admin123)"
    )

    args = parser.parse_args()

    if args.subcommand == "seed":
        try:
            run_seed(args.api_url, args.admin_user, args.admin_pass)
            return 0
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
            return 1
        except Exception as e:
            print(f"\n❌ Error fatal: {e}")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
