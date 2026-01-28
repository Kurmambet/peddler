"""add search trigger

Revision ID: 2806bc89ba00
Revises: 12d027525179
Create Date: 2026-01-28 17:34:16.031180

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2806bc89ba00"
down_revision: Union[str, Sequence[str], None] = "12d027525179"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE FUNCTION messages_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('russian', coalesce(NEW.content, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.content, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON messages FOR EACH ROW EXECUTE FUNCTION messages_search_vector_update();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate ON messages")
    op.execute("DROP FUNCTION IF EXISTS messages_search_vector_update")
