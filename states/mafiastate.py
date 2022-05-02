from aiogram.dispatcher.filters.state import StatesGroup, State


class MafiaStart(StatesGroup):
    enter = State()
    dontvote = State()


class MafiaRoles(StatesGroup):
    mafia = State()
    mir = State()
    doctor = State()
    sher = State()
    vor = State()
    maniac = State()


class MafiaGametime(StatesGroup):
    dayvote = State()
    daycantvote = State()