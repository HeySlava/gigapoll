from abc import ABC
from abc import abstractmethod

from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from gigapoll.data.models import Button
from gigapoll.enums import Modes
from gigapoll.exc import StrategyFinishedError
from gigapoll.services import template_service


class TemplateCreationStrategy(ABC):

    def __init__(self, state: FSMContext):
        self.state = state
        self.step = 0

    @abstractmethod
    async def _get_question_by_step(self, step: int) -> str:
        pass

    @abstractmethod
    async def _process_answer_by_step(self, answer: str, step: int) -> None:
        pass

    @abstractmethod
    async def save_template(self, user_id: int, session: Session) -> None:
        pass

    async def get_next_question(self) -> str:
        if self.step == 0:
            return (
                'Введи техническое имя для шаблона. '
                'Ты можешь использовать его при поиска шаблона не '
                'выходя из чата.\n\n'
                'Например: @gigapoll_bot "ТВОЕ НАЗВАНИЕ"'
            )
        elif self.step == 1:
            return (
                'Теперь введи описание опроса. '
                'Это то, что увидят пользователи'
            )
        else:
            question = await self._get_question_by_step(self.step)
            return question

    async def process_answer(self, answer: str) -> None:
        if self.step == 0:
            n = 2
            if len(answer) <= n:
                raise ValueError(f'Название должно быть длиннее {n} символов')
            await self.state.update_data(name=answer)
        elif self.step == 1:
            await self.state.update_data(description=answer)
        else:
            await self._process_answer_by_step(answer, self.step)

        self.step += 1

    async def go_back(self) -> bool:
        if self.step > 0:
            self.step -= 1
            return True
        return False


class PlusMinusStrategy(TemplateCreationStrategy):

    async def _get_question_by_step(self, step: int) -> str:
        if step == 2:
            return 'Введите название кнопки для положительного ответа'
        elif step == 3:
            return 'Введите название кнопки для негативного ответа'
        raise StrategyFinishedError('There is not more questions')

    async def _process_answer_by_step(self, answer: str, step: int) -> None:
        if step == 2:
            await self.state.update_data(positive_choice=answer)
        elif step == 3:
            await self.state.update_data(negative_choice=answer)

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
        except Exception:
            session.rollback()
            raise


STRATEGY_REGISTRY: dict[Modes, type[TemplateCreationStrategy]] = {
    Modes.PLUS_MINUS: PlusMinusStrategy,
}
