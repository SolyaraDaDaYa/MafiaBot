from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

mafiacalldata = CallbackData('kill', 'user')
mafiachoicecalldata = CallbackData('choice', 'count')
mafiadoncalldata = CallbackData('don', 'user')

# mafiafirst = InlineKeyboardMarkup(
#     inline_keyboard=
#     [
#         [InlineKeyboardButton(text="6 игроков", callback_data="sixuser")],
#         [InlineKeyboardButton(text="9 игроков", callback_data="nineuser")],
#     ]
# )

mafiaselectnum = InlineKeyboardMarkup(
    inline_keyboard=
    [
        [InlineKeyboardButton(text="Присоедениться", callback_data="entergame"),],
    ]
)

# mafiamafiakill = InlineKeyboardMarkup(
#     inline_keyboard=
#     [
#         [InlineKeyboardButton(text=f"{i}", callback_data=f"kill{i}") for i in range(1,len(game_users))],
#     ]
# )
