from __future__ import annotations

from uuid import UUID
from typing import List, Sequence

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import Exam, ExamSubject, Mark
from app.repositories.exam import ExamRepository, ExamSubjectRepository, MarkRepository
from app.schemas.exam import ExamCreate, ExamUpdate, ExamSubjectCreate, MarkEntryRequest, MarkUpdate

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft":     {"published", "cancelled"},
    "published": {"ongoing",   "cancelled"},
    "ongoing":   {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


async def get_exams(
    db: AsyncSession, academic_year_id: UUID | None = None
) -> Sequence[Exam]:
    repo = ExamRepository(db)
    return await repo.list_by_year(academic_year_id)


async def get_exam_by_id(db: AsyncSession, exam_id: UUID) -> Exam:
    repo = ExamRepository(db)
    exam = await repo.get_by_id_with_subjects(exam_id)
    if not exam:
        raise HTTPException(404, "Exam not found")
    return exam


async def create_exam(
    db: AsyncSession, payload: ExamCreate, created_by: UUID | None = None
) -> Exam:
    repo = ExamRepository(db)
    exam = Exam(**payload.model_dump(), created_by=created_by)
    await repo.add(exam)
    await db.commit()
    return exam


async def update_exam(db: AsyncSession, exam_id: UUID, payload: ExamUpdate) -> Exam:
    repo = ExamRepository(db)
    exam = await get_exam_by_id(db, exam_id)
    if exam.status != "draft":
        raise HTTPException(400, "Only draft exams can be edited")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    await db.commit()
    return await repo.get_by_id_with_subjects(exam_id)


async def transition_exam_status(
    db: AsyncSession, exam_id: UUID, new_status: str
) -> Exam:
    """
    Advance the exam through its status state machine.
    Allowed transitions defined in _VALID_TRANSITIONS above.
    """
    repo = ExamRepository(db)
    exam = await get_exam_by_id(db, exam_id)
    allowed = _VALID_TRANSITIONS.get(exam.status, set())
    if new_status not in allowed:
        raise HTTPException(
            400,
            f"Cannot transition exam from '{exam.status}' to '{new_status}'"
        )
    exam.status = new_status
    await db.commit()
    return await repo.get_by_id_with_subjects(exam_id)


async def delete_exam(db: AsyncSession, exam_id: UUID) -> None:
    repo = ExamRepository(db)
    exam = await get_exam_by_id(db, exam_id)
    if exam.status != "draft":
        raise HTTPException(400, "Only draft exams can be deleted")
    await repo.delete(exam)
    await db.commit()


async def add_exam_subject(
    db: AsyncSession, exam_id: UUID, payload: ExamSubjectCreate
) -> ExamSubject:
    es_repo = ExamSubjectRepository(db)

    exam = await get_exam_by_id(db, exam_id)
    if exam.status != "draft":
        raise HTTPException(400, "Cannot modify subjects on a non-draft exam")

    if await es_repo.get_by_exam_and_subject(exam_id, payload.subject_id):
        raise HTTPException(400, "Subject already added to this exam")

    es = ExamSubject(exam_id=exam_id, **payload.model_dump())
    await es_repo.add(es)
    await db.commit()
    return es


async def get_exam_subjects(db: AsyncSession, exam_id: UUID) -> Sequence[ExamSubject]:
    repo = ExamSubjectRepository(db)
    return await repo.list_by_exam(exam_id)


async def enter_marks(
    db: AsyncSession,
    exam_subject_id: UUID,
    payload: MarkEntryRequest,
    entered_by: UUID,
) -> List[Mark]:
    es_repo = ExamSubjectRepository(db)
    mark_repo = MarkRepository(db)

    exam_subject = await es_repo.get_by_id(exam_subject_id)
    if not exam_subject:
        raise HTTPException(404, "Exam subject not found")

    exam = await ExamRepository(db).get_by_id_with_subjects(exam_subject.exam_id)
    if exam and exam.status in ("draft", "completed", "cancelled"):
        raise HTTPException(
            400,
            f"Cannot enter marks for an exam with status '{exam.status}'"
        )

    saved: List[Mark] = []
    for entry in payload.entries:
        mark = await mark_repo.get_by_exam_subject_and_student(
            exam_subject_id, entry.student_id
        )
        if mark:
            mark.obtained_marks = entry.obtained_marks
            mark.is_absent = entry.is_absent
            mark.remarks = entry.remarks
            mark.entered_by = entered_by
        else:
            mark = Mark(
                exam_subject_id=exam_subject_id,
                student_id=entry.student_id,
                obtained_marks=entry.obtained_marks,
                is_absent=entry.is_absent,
                remarks=entry.remarks,
                entered_by=entered_by,
            )
            await mark_repo.add(mark)
        saved.append(mark)

    await db.commit()
    return saved


async def get_marks_for_exam_subject(
    db: AsyncSession, exam_subject_id: UUID
) -> Sequence[Mark]:
    repo = MarkRepository(db)
    return await repo.list_by_exam_subject(exam_subject_id)


async def get_student_marks(db: AsyncSession, student_id: UUID) -> Sequence[Mark]:
    repo = MarkRepository(db)
    return await repo.list_by_student(student_id)


async def update_mark(
    db: AsyncSession, mark_id: UUID, payload: MarkUpdate, updated_by: UUID
) -> Mark:
    from datetime import datetime, timezone
    repo = MarkRepository(db)
    mark = await repo.get_by_id(mark_id)
    if not mark:
        raise HTTPException(404, "Mark record not found")

    mark.is_absent = payload.is_absent
    mark.obtained_marks = payload.obtained_marks
    mark.remarks = payload.remarks
    mark.entered_by = updated_by
    mark.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return mark
