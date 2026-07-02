"""
config.py
---------
Configuración centralizada del pipeline. El proyecto funciona con valores por
defecto listos para usar, y las variables de entorno son opcionales para
personalizar rutas o parámetros sin tocar el código.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # carga el archivo .env si existe; si no, se usan los defaults

BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas
DATA_PATH = os.getenv("DATA_PATH", str(BASE_DIR / "data" / "Online_Retail.xlsx"))
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "datamart.db"))
SCHEMA_PATH = os.getenv("SCHEMA_PATH", str(BASE_DIR / "db" / "schema.sql"))
LOGS_DIR = os.getenv("LOGS_DIR", str(BASE_DIR / "logs"))
REPORTS_DIR = os.getenv("REPORTS_DIR", str(BASE_DIR / "logs" / "reportes"))

# Parámetros de procesamiento
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20000"))  # tamaño de lote -> optimización (batching)

Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
