"""
Сервис маршрутизации писем к сотрудникам.

Этот модуль отвечает за:
- Нахождение подходящего сотрудника по категории письма
- Назначение письма сотруднику
- Логику распределения нагрузки (если несколько сотрудников в одной категории)

Когда письмо классифицировано по категории (например, "credit"),
система находит сотрудника, который работает с этой категорией,
и назначает ему письмо.
"""

from sqlalchemy.orm import Session
from backend.database import crud
from backend.database.models import Employee, Letter


def route_letter(db: Session, letter_id: int, category: str) -> Employee:
    """
    Назначает письмо сотруднику по категории.
    
    Это ключевая функция маршрутизации:
    1. Находит всех сотрудников, работающих с данной категорией
    2. Выбирает одного из них (пока просто первого, можно улучшить логику)
    3. Назначает письмо этому сотруднику
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма для назначения
        category: Категория услуги (credit, insurance и т.д.)
    
    Returns:
        Employee: Сотрудник, которому назначено письмо
    
    Raises:
        ValueError: Если не найдено ни одного сотрудника для этой категории
    
    Пример:
        employee = route_letter(db, letter_id=1, category="credit")
        print(f"Письмо назначено сотруднику: {employee.user.name}")
    """
    # Находим всех сотрудников, работающих с данной категорией
    employees = crud.get_employees_by_category(db, category)
    
    # Проверяем, что есть хотя бы один сотрудник
    if not employees:
        raise ValueError(
            f"Не найдено ни одного сотрудника для категории '{category}'. "
            f"Пожалуйста, зарегистрируйте сотрудника с этой категорией."
        )
    
    # TODO: Улучшить логику выбора сотрудника
    # Сейчас просто берем первого сотрудника из списка
    # В будущем можно учитывать:
    # - Загруженность сотрудника (количество писем в работе)
    # - Специализацию (если сотрудник работает с несколькими категориями)
    # - Время ответа сотрудника
    selected_employee = employees[0]
    
    # Назначаем письмо выбранному сотруднику
    crud.assign_letter_to_employee(db, letter_id, selected_employee.id)
    
    print(f"✅ Письмо {letter_id} назначено сотруднику {selected_employee.user.name} (категория: {category})")
    
    return selected_employee


def get_available_employee_for_category(db: Session, category: str) -> Employee:
    """
    Получает доступного сотрудника для категории.
    
    Используется для проверки, есть ли сотрудники для категории,
    перед созданием письма.
    
    Args:
        db: Сессия базы данных
        category: Категория услуги
    
    Returns:
        Employee или None, если сотрудников нет
    """
    employees = crud.get_employees_by_category(db, category)
    
    if employees:
        return employees[0]  # Возвращаем первого доступного
    else:
        return None


def check_category_has_employees(db: Session, category: str) -> bool:
    """
    Проверяет, есть ли сотрудники для категории.
    
    Args:
        db: Сессия базы данных
        category: Категория услуги
    
    Returns:
        bool: True если есть сотрудники, False если нет
    """
    employees = crud.get_employees_by_category(db, category)
    return len(employees) > 0

