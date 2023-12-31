"""01_initial-db1

Revision ID: 989ed9954068
Revises: 
Create Date: 2023-09-11 14:58:25.685497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '989ed9954068'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('access',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tocken', sa.String(length=36), nullable=True),
    sa.Column('user', sa.String(length=12), nullable=True),
    sa.Column('password', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tocken'),
    sa.UniqueConstraint('user')
    )
    op.create_table('unique_uuid',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('paths',
    sa.Column('id_path', sa.UUID(), nullable=False),
    sa.Column('unique_id', sa.UUID(), nullable=True),
    sa.Column('path', sa.String(length=100), nullable=True),
    sa.Column('is_downloadable', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('account_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['access.id'], ),
    sa.PrimaryKeyConstraint('id_path')
    )
    op.create_table('files',
    sa.Column('id_file', sa.UUID(), nullable=False),
    sa.Column('unique_id', sa.UUID(), nullable=True),
    sa.Column('file_name', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('id_path', sa.UUID(), nullable=True),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.Column('is_downloadable', sa.Boolean(), nullable=True),
    sa.Column('hash', sa.String(length=64), nullable=True),
    sa.Column('modified_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('account_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['access.id'], ),
    sa.ForeignKeyConstraint(['id_path'], ['paths.id_path'], ),
    sa.PrimaryKeyConstraint('id_file')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('files')
    op.drop_table('paths')
    op.drop_table('unique_uuid')
    op.drop_table('access')
    # ### end Alembic commands ###
