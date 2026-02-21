"""Cross-database type compatibility (PostgreSQL ↔ SQLite for testing)."""

import json
import uuid

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.types import CHAR


class GUID(TypeDecorator):
    """Platform-independent UUID type. Uses CHAR(36) on SQLite, native UUID on PostgreSQL."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class JSONType(TypeDecorator):
    """Platform-independent JSON type. Uses JSONB on PostgreSQL, TEXT on SQLite."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)


class ArrayType(TypeDecorator):
    """Platform-independent ARRAY type. Uses ARRAY on PostgreSQL, JSON TEXT on SQLite."""

    impl = Text
    cache_ok = True

    def __init__(self, item_type=None, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
            return dialect.type_descriptor(ARRAY(PG_UUID(as_uuid=True)))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return json.dumps([str(v) for v in value])

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, list):
            return value
        items = json.loads(value)
        return [uuid.UUID(i) if isinstance(i, str) and len(i) == 36 else i for i in items]
