from aiogram.fsm.state import State, StatesGroup

__all__ = ['BroadcastStatesGroup']


class BroadcastStatesGroup(StatesGroup):
    get_message = State()
    add_button = State()
    get_button_text = State()
    get_button_url = State()
