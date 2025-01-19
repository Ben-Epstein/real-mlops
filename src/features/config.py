from pathlib import Path

from sqlmesh.core.config import (
    CategorizerConfig,
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
    PlanConfig,
    PostgresConnectionConfig,
)
from sqlmesh.core.config.connection import DuckDBAttachOptions
from sqlmesh.integrations.github.cicd.config import GithubCICDBotConfig, MergeMethod

from features import constants as C

# We purposefully do NOT resolve this path because it's different per user and the db remembers that, and considers it
# a breaking change. The relative path fixes that.
ROOT_DIR = Path(__file__).parent.parent.parent
DB_FILE = ROOT_DIR / "db.db"
GOLD_DELTA_PATH = ROOT_DIR / "gold"

RELATIVE_DB_FILE = DB_FILE.relative_to(ROOT_DIR)
RELATIVE_GOLD_DELTA_PATH = GOLD_DELTA_PATH.relative_to(ROOT_DIR)


config = Config(
    # TODO: This connection will be in S3, with the bucket derived by the client name.
    # gateways={"local": GatewayConfig(connection=DuckDBConnectionConfig(database=str(DB_FILE)))},
    # gateways={"local":GatewayConfig(connection=PostgresConnectionConfig(host="localhost", user="postgres", port=5432, database="postgres", password="postgres"))},
    gateways={
        "duckdb": GatewayConfig(
            connection=DuckDBConnectionConfig(
                # Right now the catalog name must match the dbname 
                # https://github.com/TobikoData/sqlmesh/issues/3663
                catalogs={
                    "postgres": DuckDBAttachOptions(
                        type="postgres",
                        path="dbname=postgres user=postgres host=127.0.0.1"
                    ),
                },
                extensions=["delta", "arrow"],
            )
        ),
        "postgres": GatewayConfig(
            connection=PostgresConnectionConfig(
                host="127.0.0.1",
                port=5432,
                user="postgres",
                password="password",
                database="postgres",      
            )
        ),
    },
    default_gateway="postgres",
    model_defaults=ModelDefaultsConfig(dialect="postgres", start="2024-11-02"),
    variables={
        "custom_mult": 5,
        C.GOLD_DELTA_URI_VAR: str(RELATIVE_GOLD_DELTA_PATH),
        # C.DB_URI_VAR: str(RELATIVE_DB_FILE),
    },
    cicd_bot=GithubCICDBotConfig(
        enable_deploy_command=True,  # If True, you can comment /deploy and override the required approver flow
        merge_method=MergeMethod.SQUASH,
        auto_categorize_changes=CategorizerConfig.all_full(),
        default_pr_start="1 week ago",
    ),
    plan=PlanConfig(auto_categorize_changes=CategorizerConfig.all_full()),
    # users=[
    #     User(
    #         username="ben-epstein",
    #         github_username="ben-epstein",
    #         roles=[UserRole.REQUIRED_APPROVER],
    #     )
    # ],
)


# TODO:
"""
docker run --name mooncake-demo \
  -p 5432:5432 \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  -v $(pwd):/workspace \
  -d mooncakelabs/pg_mooncake


docker run -it --rm --link mooncake-demo:postgres mooncakelabs/pg_mooncake psql -h postgres -U postgres
and run
`create extension pg_mooncake;`
`SET duckdb.force_execution TO true;`

"""
# then
"""


create extension pg_mooncake;
SET duckdb.force_execution TO true;
select * from mooncake.delta_scan('/delta_table') as (a int);
"""