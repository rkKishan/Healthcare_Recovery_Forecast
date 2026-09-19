"""split clinician into doctor/analyst roles and add Google identity columns

Revision ID: c4a91f27d8b3
Revises: b7e3555791ec
Create Date: 2026-09-08 22:40:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c4a91f27d8b3'
down_revision = 'b7e3555791ec'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        # A Google account has no password to hash.
        batch_op.alter_column(
            'password_hash',
            existing_type=sa.String(length=255),
            nullable=True,
        )
        # server_default so the rows that already exist get a value; every one
        # of them was created through the password flow.
        batch_op.add_column(
            sa.Column(
                'auth_provider',
                sa.String(length=32),
                nullable=False,
                server_default='password',
            )
        )
        batch_op.add_column(sa.Column('google_sub', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('avatar_url', sa.String(length=512), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_users_google_sub'), ['google_sub'], unique=True
        )

    # Accounts created before the split all held the single "clinician" role.
    # `backend.roles.ALIASES` also maps it at read time, so this backfill is
    # about keeping the stored data honest rather than about anyone's access.
    op.execute(
        sa.text("UPDATE users SET role = 'doctor' WHERE role IN ('clinician', 'physician')")
    )


def downgrade():
    op.execute(sa.text("UPDATE users SET role = 'clinician' WHERE role = 'doctor'"))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_google_sub'))
        batch_op.drop_column('avatar_url')
        batch_op.drop_column('google_sub')
        batch_op.drop_column('auth_provider')
        # Rows with no password cannot exist under the old schema; the caller
        # is responsible for removing Google-only accounts before downgrading.
        batch_op.alter_column(
            'password_hash',
            existing_type=sa.String(length=255),
            nullable=False,
        )
