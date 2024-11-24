from pathlib import Path

from sqlmesh.core.config import (
    AutoCategorizationMode,
    CategorizerConfig,
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
    PlanConfig,
)
from sqlmesh.integrations.github.cicd.config import GithubCICDBotConfig, MergeMethod

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
    cicd_bot=GithubCICDBotConfig(
        enable_deploy_command=True,  # If True, you can comment /deploy and override the required approver flow
        merge_method=MergeMethod.SQUASH,
    ),
    plan=PlanConfig(
        auto_categorize_changes=CategorizerConfig(
            external=AutoCategorizationMode.SEMI,
            python=AutoCategorizationMode.SEMI,
            sql=AutoCategorizationMode.SEMI,
            seed=AutoCategorizationMode.SEMI,
        )
    ),
    default_pr_start="1 week ago",
    # users=[
    #     User(
    #         username="ben-epstein",
    #         github_username="ben-epstein",
    #         roles=[UserRole.REQUIRED_APPROVER],
    #     )
    # ],
)
