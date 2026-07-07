from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exam import Exam, ExamSubject, Mark
from app.models.student import Student
from app.models.subject import Subject
from app.models.class_ import StudentEnrollment


def _compute_grade(percentage: float) -> str:
    """
    Converts a percentage (0–100) to a letter grade.
    Grades are NEVER stored — always computed fresh from obtained_marks.
    This means changing the grading scale retroactively works correctly.
    """
    if percentage >= 90:
        return "A+"
    if percentage >= 80:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 60:
        return "C"
    if percentage >= 50:
        return "D"
    return "F"


async def get_student_results(db: AsyncSession, student_id: UUID) -> dict:
    """
    All marks for a student grouped by exam.
    Returns a list of exams, each with per-subject breakdown and totals.
    """
    student_result = await db.execute(
        select(Student)
        .options(selectinload(Student.user))
        .where(Student.id == student_id, Student.deleted_at.is_(None))
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    marks_result = await db.execute(
        select(Mark)
        .options(
            selectinload(Mark.exam_subject).selectinload(ExamSubject.exam),
            selectinload(Mark.exam_subject).selectinload(ExamSubject.subject),
        )
        .where(Mark.student_id == student_id)
    )
    marks: Sequence[Mark] = marks_result.scalars().all()

    # Group marks by exam
    exams_map: dict[UUID, dict] = {}
    for mark in marks:
        es = mark.exam_subject
        exam = es.exam
        eid = exam.id

        if eid not in exams_map:
            exams_map[eid] = {
                "exam_id": eid,
                "exam_name": exam.name,
                "exam_status": exam.status,
                "subjects": [],
                "total_obtained": 0.0,
                "total_max": 0.0,
            }

        pct = round((mark.obtained_marks / es.max_marks) * 100, 2) if not mark.is_absent and mark.obtained_marks is not None else None

        exams_map[eid]["subjects"].append({
            "subject_id": es.subject_id,
            "subject_name": es.subject.name,
            "subject_code": es.subject.code,
            "max_marks": float(es.max_marks),
            "passing_marks": float(es.passing_marks),
            "obtained_marks": float(mark.obtained_marks) if mark.obtained_marks is not None else None,
            "is_absent": mark.is_absent,
            "percentage": pct,
            "grade": _compute_grade(pct) if pct is not None else None,
            "remarks": mark.remarks,
        })

        if not mark.is_absent and mark.obtained_marks is not None:
            exams_map[eid]["total_obtained"] += float(mark.obtained_marks)
        exams_map[eid]["total_max"] += float(es.max_marks)

    for eid, entry in exams_map.items():
        if entry["total_max"] > 0:
            pct = round((entry["total_obtained"] / entry["total_max"]) * 100, 2)
            entry["overall_percentage"] = pct
            entry["overall_grade"] = _compute_grade(pct)
        else:
            entry["overall_percentage"] = None
            entry["overall_grade"] = None

    return {
        "student_id": student_id,
        "admission_number": student.admission_number,
        "first_name": student.user.first_name,
        "last_name": student.user.last_name,
        "exams": list(exams_map.values()),
    }


async def get_exam_results(db: AsyncSession, exam_id: UUID) -> dict:
    """
    All marks for an exam — one row per student, one column per subject.
    Used by admin to see the full class result sheet.
    """
    exam_result = await db.execute(
        select(Exam)
        .options(selectinload(Exam.exam_subjects).selectinload(ExamSubject.subject))
        .where(Exam.id == exam_id)
    )
    exam = exam_result.scalar_one_or_none()
    if not exam:
        raise HTTPException(404, "Exam not found")

    marks_result = await db.execute(
        select(Mark)
        .options(
            selectinload(Mark.exam_subject),
            selectinload(Mark.student).selectinload(Student.user),
        )
        .where(Mark.exam_subject_id.in_([es.id for es in exam.exam_subjects]))
    )
    all_marks: Sequence[Mark] = marks_result.scalars().all()

    # Group marks by student
    students_map: dict[UUID, dict] = {}
    for mark in all_marks:
        sid = mark.student_id
        if sid not in students_map:
            students_map[sid] = {
                "student_id": sid,
                "admission_number": mark.student.admission_number,
                "first_name": mark.student.user.first_name,
                "last_name": mark.student.user.last_name,
                "subjects": {},
                "total_obtained": 0.0,
                "total_max": 0.0,
            }
        es = mark.exam_subject
        pct = round((mark.obtained_marks / es.max_marks) * 100, 2) if not mark.is_absent and mark.obtained_marks is not None else None
        students_map[sid]["subjects"][str(es.subject_id)] = {
            "obtained_marks": float(mark.obtained_marks) if mark.obtained_marks is not None else None,
            "is_absent": mark.is_absent,
            "percentage": pct,
            "grade": _compute_grade(pct) if pct is not None else None,
        }
        if not mark.is_absent and mark.obtained_marks is not None:
            students_map[sid]["total_obtained"] += float(mark.obtained_marks)
        students_map[sid]["total_max"] += float(es.max_marks)

    for entry in students_map.values():
        if entry["total_max"] > 0:
            pct = round((entry["total_obtained"] / entry["total_max"]) * 100, 2)
            entry["overall_percentage"] = pct
            entry["overall_grade"] = _compute_grade(pct)
        else:
            entry["overall_percentage"] = None
            entry["overall_grade"] = None

    return {
        "exam_id": exam_id,
        "exam_name": exam.name,
        "exam_status": exam.status,
        "subjects": [
            {"subject_id": es.subject_id, "subject_name": es.subject.name, "max_marks": float(es.max_marks)}
            for es in exam.exam_subjects
        ],
        "students": list(students_map.values()),
    }


async def get_report_card(db: AsyncSession, student_id: UUID, exam_id: UUID) -> dict:
    """
    Detailed report card for one student in one exam.
    Includes enrollment info (class/section), per-subject breakdown, and totals.
    """
    student_result = await db.execute(
        select(Student)
        .options(selectinload(Student.user))
        .where(Student.id == student_id, Student.deleted_at.is_(None))
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    exam_result = await db.execute(
        select(Exam)
        .options(
            selectinload(Exam.exam_subjects).selectinload(ExamSubject.subject),
            selectinload(Exam.academic_year),
            selectinload(Exam.class_),
        )
        .where(Exam.id == exam_id)
    )
    exam = exam_result.scalar_one_or_none()
    if not exam:
        raise HTTPException(404, "Exam not found")

    marks_result = await db.execute(
        select(Mark)
        .where(
            Mark.student_id == student_id,
            Mark.exam_subject_id.in_([es.id for es in exam.exam_subjects]),
        )
    )
    marks_by_es: dict[UUID, Mark] = {m.exam_subject_id: m for m in marks_result.scalars().all()}

    subject_results = []
    total_obtained = 0.0
    total_max = 0.0

    for es in exam.exam_subjects:
        mark = marks_by_es.get(es.id)
        max_m = float(es.max_marks)
        total_max += max_m

        if mark and not mark.is_absent and mark.obtained_marks is not None:
            obtained = float(mark.obtained_marks)
            total_obtained += obtained
            pct = round((obtained / max_m) * 100, 2)
            subject_results.append({
                "subject_name": es.subject.name,
                "subject_code": es.subject.code,
                "max_marks": max_m,
                "passing_marks": float(es.passing_marks),
                "obtained_marks": obtained,
                "is_absent": False,
                "percentage": pct,
                "grade": _compute_grade(pct),
                "passed": obtained >= float(es.passing_marks),
                "remarks": mark.remarks,
            })
        else:
            subject_results.append({
                "subject_name": es.subject.name,
                "subject_code": es.subject.code,
                "max_marks": max_m,
                "passing_marks": float(es.passing_marks),
                "obtained_marks": None,
                "is_absent": mark.is_absent if mark else True,
                "percentage": None,
                "grade": None,
                "passed": False,
                "remarks": mark.remarks if mark else None,
            })

    overall_pct = round((total_obtained / total_max) * 100, 2) if total_max > 0 else 0.0

    return {
        "student_id": student_id,
        "admission_number": student.admission_number,
        "first_name": student.user.first_name,
        "last_name": student.user.last_name,
        "exam_id": exam_id,
        "exam_name": exam.name,
        "academic_year": exam.academic_year.name,
        "class_name": exam.class_.name,
        "subject_results": subject_results,
        "total_obtained": total_obtained,
        "total_max": total_max,
        "overall_percentage": overall_pct,
        "overall_grade": _compute_grade(overall_pct),
    }
