from pathlib import Path

from sqlmesh.core.config import (
    CategorizerConfig,
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
    PlanConfig,
)
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
    gateways={"local": GatewayConfig(connection=DuckDBConnectionConfig(database=str(DB_FILE)))},
    default_gateway="local",
    model_defaults=ModelDefaultsConfig(dialect="duckdb", start="2024-11-02"),
    variables={
        "custom_mult": 5,
        C.GOLD_DELTA_URI_VAR: str(RELATIVE_GOLD_DELTA_PATH),
        C.DB_URI_VAR: str(RELATIVE_DB_FILE),
    },
    cicd_bot=GithubCICDBotConfig(
        enable_deploy_command=True,  # If True, you can comment /deploy and override the required approver flow
        merge_method=MergeMethod.SQUASH,
        auto_categorize_changes=CategorizerConfig.all_semi(),
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
