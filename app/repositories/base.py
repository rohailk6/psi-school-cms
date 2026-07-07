from __future__ import annotations

from typing import Generic, Optional, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD layer. Every model-specific repo inherits from this.

    TRANSACTION RESPONSIBILITY — important to understand:
    • Repos call flush() inside add() to materialize auto-generated IDs
      so the service can use obj.id immediately after insertion.
    • Services call db.commit() to finalize the whole transaction.
    This split lets one service method do multiple repo operations
    and commit them all atomically at the end.

    Example:
        user = await user_repo.add(User(...))   # flush — gets user.id
        student = await student_repo.add(Student(user_id=user.id, ...))
        await db.commit()                        # both rows committed together
    """

    model: Type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[ModelT]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 100) -> Sequence[ModelT]:
        result = await self.db.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def count_all(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def add(self, obj: ModelT) -> ModelT:
        """
        Persist a new object and flush so auto-generated fields
        (id, created_at) are populated before the caller continues.
        Does NOT commit — the service owns the transaction boundary.
        """
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        """
        Mark an object for deletion. The service must commit
        afterwards. For soft-deletes, set deleted_at instead.
        """
        await self.db.delete(obj)
