"""installation_state: track initial onboarding completion

Revision ID: 013
Revises: 012
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "installation_state",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("initial_setup_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO installation_state (id, initial_setup_completed, created_at, updated_at)
            VALUES ('default', false, now(), now())
            """
        )
    )

    # Existing deployments: if any user exists, treat onboarding as already done.
    op.execute(
        sa.text(
            """
            UPDATE installation_state
            SET initial_setup_completed = true, updated_at = now()
            WHERE id = 'default'
              AND EXISTS (SELECT 1 FROM users)
            """
        )
    )


def downgrade() -> None:
    op.drop_table("installation_state")
