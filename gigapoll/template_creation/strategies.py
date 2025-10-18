from abc import ABC
from abc import abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.orm import Session

from gigapoll.data.models import Button
from gigapoll.enums import Modes
from gigapoll.services import template_service


class TemplateCreationStrategy(ABC):

    def __init__(self, state: FSMContext):
        self.state = state
        self.step = 0

    @abstractmethod
    async def get_next_question(self) -> str:
        pass

    @abstractmethod
    async def process_answer(self, message: Message) -> bool:
        pass

    @abstractmethod
    async def save_template(self, user_id: int, session: Session) -> None:
        pass


class PlusMinusStrategy(TemplateCreationStrategy):

    @property
    def total_steps(self) -> int:
        return 2

    async def get_next_question(self) -> str:
        if self.step == 0:
            return 'Введите название кнопки для положительного ответа'
        elif self.step == 1:
            return 'Введите название кнопки для негативного ответа'
        return ''

    async def process_answer(self, message: Message) -> bool:
        if self.step == 0:
            await self.state.update_data(positive_choice=message.text)
        elif self.step == 1:
            await self.state.update_data(negative_choice=message.text)

        self.step += 1
        return self.step < self.total_steps

    async def save_template(self, user_id: int, session: Session) -> None:
        user_data = await self.state.get_data()

        try:
            template = template_service.create_template(
                user_id=user_id,
                template_name=user_data['name'],
                description=user_data['description'],
                mode=user_data['mode'],
                session=session
            )

            session.flush()

            positive_choice = Button(
                template_id=template.id,
                value=user_data['positive_choice'],
                is_positive=True
            )
            negative_choice = Button(
                template_id=template.id,
                value=user_data['negative_choice'],
                is_negative=True
            )

            session.add_all([positive_choice, negative_choice])

            session.commit()

        except Exception as e:
            print(f'Ошибка при сохранении: {e}')
            session.rollback()
            raise


STRATEGY_REGISTRY: dict[Modes, type[TemplateCreationStrategy]] = {
    Modes.PLUS_MINUS: PlusMinusStrategy,
}
