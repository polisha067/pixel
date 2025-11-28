"""
Базовый класс для всех AI агентов.

Агенты - это специализированные помощники для генерации ответов
в разных стилях и для разных ситуаций. Каждый агент имеет свой промпт
с инструкциями по стилю и тону ответа.

Все агенты наследуются от BaseAgent и реализуют метод generate_response().
"""

from abc import ABC, abstractmethod
from backend.services.yandex_ai import send_request_to_yandex


class BaseAgent(ABC):
    """
    Базовый класс для всех агентов генерации ответов.
    
    Это абстрактный класс (ABC) - его нельзя использовать напрямую,
    только через наследование. Каждый конкретный агент должен
    реализовать метод generate_response().
    """
    
    def __init__(self, name: str, system_instruction: str):
        """
        Инициализирует агента.
        
        Args:
            name: Название агента (для отладки)
            system_instruction: Системная инструкция - описание роли и стиля агента
        """
        self.name = name
        self.system_instruction = system_instruction
    
    @abstractmethod
    def generate_response(self, letter_text: str) -> str:
        """
        Генерирует ответ на письмо.
        
        Это абстрактный метод - каждый конкретный агент должен
        реализовать его по-своему.
        
        Args:
            letter_text: Текст входящего письма
        
        Returns:
            str: Сгенерированный ответ
        
        Raises:
            NotImplementedError: Если метод не реализован в дочернем классе
        """
        raise NotImplementedError("Метод generate_response() должен быть реализован в дочернем классе!")
    
    def _build_prompt(self, letter_text: str, additional_instructions: str = "") -> str:
        """
        Строит полный промпт для отправки в нейросеть.
        
        Объединяет системную инструкцию, дополнительные инструкции
        и текст письма в один промпт.
        
        Args:
            letter_text: Текст входящего письма
            additional_instructions: Дополнительные инструкции (опционально)
        
        Returns:
            str: Полный промпт для нейросети
        """
        prompt = f"""{self.system_instruction}

{additional_instructions}

Входящее письмо от клиента:
{letter_text}

Сгенерируй профессиональный ответ банка на это письмо."""
        
        return prompt

