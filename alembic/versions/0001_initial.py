"""Initial PostgreSQL schema for the POC.

Revision ID: 0001_initial
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("cpf", sa.String(11), nullable=False, unique=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
    )
    op.create_table(
        "availability",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("specialty", sa.String(120), nullable=False),
        sa.Column("slot_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("specialty", "slot_datetime", name="uq_availability_slot"),
    )
    op.create_index("ix_availability_specialty", "availability", ["specialty"])
    op.create_index("ix_availability_slot_datetime", "availability", ["slot_datetime"])
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("slot_id", sa.Integer(), sa.ForeignKey("availability.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("confirmation_key", sa.String(100), nullable=False, unique=True),
        sa.Column("specialty", sa.String(120), nullable=False),
        sa.Column("preferred_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
    )
    op.create_table(
        "clinic_info",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("clinic_info")
    op.drop_table("appointments")
    op.drop_index("ix_availability_slot_datetime", table_name="availability")
    op.drop_index("ix_availability_specialty", table_name="availability")
    op.drop_table("availability")
    op.drop_table("patients")
