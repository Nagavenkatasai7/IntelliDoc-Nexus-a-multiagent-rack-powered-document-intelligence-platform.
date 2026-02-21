"""Create seed data for development."""

import uuid

from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password

DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEV_EMAIL = "dev@intellidoc.local"
DEV_PASSWORD = "devpassword123"


async def seed_dev_user(session) -> None:
    """Create the default dev user if it doesn't exist."""
    result = await session.execute(select(User).where(User.id == DEV_USER_ID))
    if result.scalar_one_or_none():
        return

    user = User(
        id=DEV_USER_ID,
        email=DEV_EMAIL,
        hashed_password=hash_password(DEV_PASSWORD),
        full_name="Dev User",
        is_active=True,
    )
    session.add(user)
    await session.commit()
