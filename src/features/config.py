from pathlib import Path

from sqlmesh.core.config import Config, DuckDBConnectionConfig, GatewayConfig

ROOT_DIR = Path(__file__).parent.parent.parent
DB_FILE = ROOT_DIR / "db.db"
GOLD_DELTA_PATH = ROOT_DIR / "gold"

config = Config(
    gateways={"local": GatewayConfig(connection=DuckDBConnectionConfig(database=str(DB_FILE)))},
    default_gateway="local",
    model_defaults={"dialect": "duckdb", "start": "2024-11-02"},
    variables={
        "custom_mult": 5,
        "gold_delta_path": str(GOLD_DELTA_PATH),
    },
)
