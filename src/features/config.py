from pathlib import Path

from sqlmesh.core.config import Config, DuckDBConnectionConfig, GatewayConfig, ModelDefaultsConfig

from features import constants as C

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
DB_FILE = ROOT_DIR / "db.db"
GOLD_DELTA_PATH = ROOT_DIR / "gold"

config = Config(
    # TODO: This connection will be in S3, with the bucket derived by the client name.
    gateways={"local": GatewayConfig(connection=DuckDBConnectionConfig(database=str(DB_FILE)))},
    default_gateway="local",
    model_defaults=ModelDefaultsConfig(dialect="duckdb", start="2024-11-02"),
    variables={
        "custom_mult": 5, 
        C.GOLD_DELTA_URI_VAR: str(GOLD_DELTA_PATH), 
        C.DB_URI_VAR: str(DB_FILE),
    },
)
