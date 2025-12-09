from aiogram.fsm.state import StatesGroup, State

class ChooseName(StatesGroup):
    personal_name = State()
    tandem_name = State()