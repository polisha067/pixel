"""
API эндпоинты для статистики.

Этот модуль содержит эндпоинты для получения статистики:
- Общая статистика по письмам
- Статистика по категориям
- Статистика по статусам
- Статистика по сотрудникам
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List

from backend.database.database import get_db
from backend.database.models import Letter, LetterStatus, Employee
from backend.config import settings

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/overview")
def get_overview_statistics(db: Session = Depends(get_db)):
    """
    Получить общую статистику по письмам.
    
    Возвращает:
    - Общее количество писем
    - Количество по статусам
    - Количество по категориям
    
    Args:
        db: Сессия базы данных
    
    Returns:
        dict: Общая статистика
    """
    # Общее количество писем
    total_letters = db.query(func.count(Letter.id)).scalar()
    
    # Количество по статусам
    status_counts = {}
    for status in LetterStatus:
        count = db.query(func.count(Letter.id)).filter(Letter.status == status).scalar()
        status_counts[status.value] = count
    
    # Количество по категориям
    category_counts = {}
    for category in settings.BANK_CATEGORIES:
        count = db.query(func.count(Letter.id)).filter(Letter.category == category).scalar()
        category_counts[category] = count
    
    return {
        "total_letters": total_letters,
        "by_status": status_counts,
        "by_category": category_counts
    }


@router.get("/by_category")
def get_statistics_by_category(db: Session = Depends(get_db)):
    """
    Получить детальную статистику по категориям.
    
    Для каждой категории показывает:
    - Общее количество писем
    - Количество по статусам
    
    Args:
        db: Сессия базы данных
    
    Returns:
        dict: Статистика по категориям
    """
    result = {}
    
    for category in settings.BANK_CATEGORIES:
        total = db.query(func.count(Letter.id)).filter(Letter.category == category).scalar()
        
        by_status = {}
        for status in LetterStatus:
            count = db.query(func.count(Letter.id)).filter(
                Letter.category == category,
                Letter.status == status
            ).scalar()
            by_status[status.value] = count
        
        result[category] = {
            "total": total,
            "by_status": by_status
        }
    
    return result


@router.get("/by_employee")
def get_statistics_by_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Получить статистику по конкретному сотруднику.
    
    Показывает:
    - Общее количество назначенных писем
    - Количество по статусам
    - Количество обработанных писем
    
    Args:
        employee_id: ID сотрудника
        db: Сессия базы данных
    
    Returns:
        dict: Статистика сотрудника
    """
    # Общее количество писем сотрудника
    total = db.query(func.count(Letter.id)).filter(
        Letter.employee_id == employee_id
    ).scalar()
    
    # По статусам
    by_status = {}
    for status in LetterStatus:
        count = db.query(func.count(Letter.id)).filter(
            Letter.employee_id == employee_id,
            Letter.status == status
        ).scalar()
        by_status[status.value] = count
    
    # Обработанные (отправленные)
    processed = by_status.get(LetterStatus.SENT.value, 0)
    
    return {
        "employee_id": employee_id,
        "total_letters": total,
        "by_status": by_status,
        "processed": processed
    }

