from loader import dp, bot
from aiogram.dispatcher.filters import Text,Command,ChatTypeFilter
from aiogram.types import CallbackQuery, Message, ChatType
from keyboards.inline import mafiabuttons
from aiogram.dispatcher import FSMContext
from utils.db_api.database import DBCommands
from states.mafiastate import MafiaStart, MafiaRoles, MafiaGametime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

db = DBCommands()


async def text_all_roles(game_users):
    for user in game_users:
        textuserole = user.get('user_role')
        await bot.send_message(chat_id=user.get('user'), text=f'Твоя роль: {textuserole}\nТвой номер: №{user.get("user_num")}')
        rolestate = dp.current_state(user=user.get('user'), chat=user.get('user'))
        if (textuserole == 'Мафия') or (textuserole == 'Дон(мафия)'):
            await rolestate.set_state(state=MafiaRoles.mafia)
        elif textuserole == 'Доктор':
            await rolestate.set_state(state=MafiaRoles.doctor)
        elif textuserole == 'Шериф':
            await rolestate.set_state(state=MafiaRoles.sher)
        elif textuserole == 'Мирный житель':
            await rolestate.set_state(state=MafiaRoles.mir)
        elif textuserole == 'Вор':
            await rolestate.set_state(state=MafiaRoles.vor)
        elif textuserole == 'Маньяк':
            await rolestate.set_state(state=MafiaRoles.maniac)
        await asyncio.sleep(delay=0.5)  # чтобы не получить бан за флуд

async def get_all_game_users(key):
    users = await db.get_all_users(key=key)
    game_users = []
    for user in users:
        game_users.append({'user': user.guser_id,
                           'user_num': user.guser_num,
                           'user_role': user.guser_role,
                           'user_name': user.guser_name,
                           'kick': False,
                           'kickvote': 0,
                           'mafiakickvote': 0.0})
    await text_all_roles(game_users)

    return game_users


class EnterGame:
    async def entergame_1(self, call: CallbackQuery, state: FSMContext, user, num, usercount, roomuserslist, roomusersnamelist):
        try:
            await bot.send_message(chat_id=user.user_id, text='Вы присоеденились к игре')
            await state.storage.update_data(chat=call.message.chat.id, num=num, roomuserslist=roomuserslist,
                                            roomusersnamelist=roomusersnamelist)
            await call.message.edit_text(
                text=f'Ожидание игроков...\nЧтобы присоедениться к игре нажмите на кнопку снизу\n{num}/{usercount}',
                reply_markup=mafiabuttons.mafiaselectnum)
            await MafiaStart.enter.set()
            await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
        except:
            pass

    async def entergame_2(self, call: CallbackQuery, state: FSMContext, user, num, roomuserslist, roomusersnamelist):
        try:
            await bot.send_message(chat_id=user.user_id, text='Вы присоеденились к игре')
            await state.storage.update_data(chat=call.message.chat.id, num=num, roomuserslist=roomuserslist,
                                            roomusersnamelist=roomusersnamelist)
            await call.message.edit_text(text=f'Игра начинается...')
            await MafiaStart.enter.set()
        except:
            pass


class VoteGame:
    async def getvotes_1(self, call: CallbackQuery, state: FSMContext, game_users, voteuser=None, skipvote=None, votenum=None, mafiaauction=None):
        if voteuser == 'skip':
            skipvote += 1

            await call.message.edit_text(text=f'Голосование   {votenum}/{len(game_users)}', reply_markup=mafiaauction)
            await state.storage.update_data(chat=call.message.chat.id, skipvote=skipvote, votenum=votenum)
            await MafiaGametime.daycantvote.set()
            await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд

        else:
            for user in game_users:
                if user.get('user') == int(voteuser):
                    user['kickvote'] += 1
                    break

            await call.message.edit_text(text=f'Голосование   {votenum}/{len(game_users)}', reply_markup=mafiaauction)
            await state.storage.update_data(chat=call.message.chat.id, game_users=game_users, votenum=votenum)
            await MafiaGametime.daycantvote.set()
            await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд

    async def getvotes_2(self, call: CallbackQuery, state: FSMContext, game_users, voteuser=None, skipvote=None, votenum=None):
        if voteuser == 'skip':
            skipvote += 1
            await state.storage.update_data(chat=call.message.chat.id, skipvote=skipvote, votenum=votenum)
            await MafiaGametime.daycantvote.set()
            await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд

        else:
            for user in game_users:
                if user.get('user') == int(voteuser):
                    user['kickvote'] += 1
                    break
            await state.storage.update_data(chat=call.message.chat.id, game_users=game_users, votenum=votenum)
            await MafiaGametime.daycantvote.set()
            await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд

    async def voteending(self, call: CallbackQuery, game_users):
        await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
        await call.message.answer(text='Город засыпает')
        for user in game_users:
            try:
                await bot.restrict_chat_member(chat_id=call.message.chat.id, user_id=user['user'])  # мут челов
            except:
                pass
        await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд


vtcommands = VoteGame()
entgamecommands = EnterGame()


@dp.message_handler(Text, state=MafiaGametime)
async def do_chat_group(message: Message):
    if message.is_forward():
        await message.delete()


@dp.message_handler(Command('mafia'), ChatTypeFilter(chat_type=ChatType.SUPERGROUP))
async def get_mafia_choice(message: Message):
    await message.answer(text='Перед игрой напишите команду start у бота в лс')
    mafiastartchoice = InlineKeyboardMarkup(
        inline_keyboard=
        [
            [InlineKeyboardButton(text=f"6 игроков", callback_data=mafiabuttons.mafiachoicecalldata.new(count=6))],#тут менять на нужное колво для тестов
            [InlineKeyboardButton(text=f"9 игроков", callback_data=mafiabuttons.mafiachoicecalldata.new(count=9))]
        ]
    )
    await message.answer(text=f'Выберите режим игры', reply_markup=mafiastartchoice)


@dp.callback_query_handler(mafiabuttons.mafiachoicecalldata.filter())
async def get_start_mafia(call: CallbackQuery, callback_data: dict, state: FSMContext):
    usercount = int(callback_data['count'])
    num = 0
    await state.storage.update_data(chat=call.message.chat.id, num=num, mafiavotecount=0, usercount=usercount, roomuserslist=[], roomusersnamelist=[], isheal=None, ismute=None, maniacisheal=None, skipvote=0, votenum=0)
    await call.message.edit_text(text=f'Ожидание игроков...\nЧтобы присоедениться к игре нажмите на кнопку снизу\n{num}/{usercount}',reply_markup=mafiabuttons.mafiaselectnum)
    await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд


@dp.callback_query_handler(text='entergame')
async def enter_game_mafia(call: CallbackQuery, state: FSMContext):
    data = await state.storage.get_data(chat=call.message.chat.id)
    num = data['num']
    usercount = data['usercount']
    roomuserslist = data['roomuserslist']
    roomusersnamelist = data['roomusersnamelist']
    num += 1
    user = await db.add_new_user()
    roomusersnamelist.append(user.full_name)
    roomuserslist.append(user.user_id)

    if num != usercount:
        await entgamecommands.entergame_1(call=call, state=state, user=user, num=num, usercount=usercount, roomuserslist=roomuserslist, roomusersnamelist=roomusersnamelist)
    else:
        await entgamecommands.entergame_2(call=call, state=state, user=user, num=num, roomuserslist=roomuserslist, roomusersnamelist=roomusersnamelist)

        await call.message.answer(text='Город засыпает')
        await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд

        data = await state.storage.get_data(chat=call.message.chat.id)
        roomuserslist = data.get('roomuserslist')
        roomusersnamelist = data['roomusersnamelist']
        await db.create_game_room(users_id=roomuserslist, users_names=roomusersnamelist, usercount=usercount)

        key = await db.get_game_room_key(user_id=call.from_user.id)
        game_users = await get_all_game_users(key=key)

        await state.storage.update_data(chat=call.message.chat.id, game_users=game_users)

        for user in game_users:
            await state.storage.update_data(user=user.get('user'), chat_id=call.message.chat.id, user_num=user.get("user_num"))
            try:
                await bot.restrict_chat_member(chat_id=call.message.chat.id, user_id=user['user'])#мут челов
            except:
                pass
        await call.message.answer(text='Просыпается вор')
        await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
        await db.text_to_roles(game_users=game_users, role='vor')
        mafia = await db.get_users_roles(game_users=game_users, role='maf')

        await state.storage.update_data(chat=call.message.chat.id, mafia=mafia)


@dp.callback_query_handler(mafiabuttons.mafiacalldata.filter(), state=MafiaGametime.dayvote)
async def get_auction_data(call: CallbackQuery, callback_data: dict, state: FSMContext):
    voteuser = callback_data['user']

    data = await state.storage.get_data(chat=call.message.chat.id)
    game_users = data['game_users']
    votenum = data['votenum']
    skipvote = data['skipvote']

    chat_id = call.message.chat.id
    votenum += 1

    mafiaauction = InlineKeyboardMarkup(
        inline_keyboard=
        [
            [InlineKeyboardButton(text=f"{user.get('user_num')}  {user['user_name']}",
                                  callback_data=mafiabuttons.mafiacalldata.new(user=user['user'])) for user in
             game_users],
            [InlineKeyboardButton(text='Пропустить', callback_data=mafiabuttons.mafiacalldata.new(user='skip'))]
        ]
    )

    if votenum != len(game_users):
        await vtcommands.getvotes_1(call=call, state=state,game_users=game_users,voteuser=voteuser,skipvote=skipvote,votenum=votenum ,mafiaauction=mafiaauction)

    else:  # тут можно сделать окончание
        await vtcommands.getvotes_2(call=call, state=state,game_users=game_users,voteuser=voteuser,skipvote=skipvote,votenum=votenum)

        data = await state.storage.get_data(chat=chat_id)
        game_users = data['game_users']
        if data['skipvote'] >= (len(game_users) + 1)//2:
            await call.message.edit_text(text=f'Большинство проголосовало за пропуск')
            for user in game_users:
                user['kickvote'] = 0
                await state.storage.set_state(user=user['user'], chat=chat_id, state=MafiaStart.enter)
            await state.storage.update_data(chat=chat_id, skipvote=0, votenum=0)
            # тут была проверка на mafia !=0
            vor = await db.text_to_roles(game_users=game_users, role='vor')
            if vor != 0:
                await vtcommands.voteending(call=call,game_users=game_users)
                await call.message.answer(text='Просыпается вор')
            else:
                mafia = await db.text_to_roles(game_users=game_users, role='maf')
                if mafia != 0:
                    await vtcommands.voteending(call=call,game_users=game_users)
                    await call.message.answer(text='Просыпается мафия')
                else:
                    await db.text_to_roles(game_users=game_users, role='mani')
                    await vtcommands.voteending(call=call, game_users=game_users)
                    await call.message.answer(text='Просыпается маньяк')

        else:  # тут конец игры
            kickuserlist = sorted(game_users, key=lambda d: d['kickvote'], reverse=True)
            if kickuserlist[0].get('kickvote') > kickuserlist[1].get('kickvote'):
                kickuser = kickuserlist[0]
                for user in game_users:
                    if user['user'] == kickuser['user']:
                        game_users.remove(user)
                    else:
                        user['kickvote'] = 0
                await state.storage.reset_state(chat=chat_id, user=kickuser['user'])
                await state.storage.reset_state(chat=kickuser['user'], user=kickuser['user'])
                await call.message.edit_text(text=f'Был изгнан игрок №{kickuser.get("user_num")} {kickuser["user_name"]}\nЕго роль: {kickuser["user_role"]}')
                try:
                    await bot.restrict_chat_member(chat_id=chat_id, user_id=kickuser['user'])
                except:
                    pass
                await state.storage.update_data(chat=chat_id, game_users=game_users, skipvote=0, votenum=0)

                for user in game_users:
                    user_id = user['user']
                    await state.storage.set_state(user=user_id, chat=chat_id, state=MafiaStart.enter)

                mafia = await db.get_users_roles(game_users=game_users, role='maf')
                maniac = await db.get_users_roles(game_users=game_users, role='mani')
                if mafia != 0:
                    if len(mafia) < (len(game_users) - len(mafia)):
                        vor = await db.text_to_roles(game_users=game_users, role='vor')
                        if vor != 0:
                            await vtcommands.voteending(call=call, game_users=game_users)
                            await call.message.answer(text='Просыпается вор')
                        else:
                            await vtcommands.voteending(call=call, game_users=game_users)
                            await db.text_to_roles(game_users=game_users, role='maf')
                            await call.message.answer(text='Просыпается мафия')
                    else:  # завершение игры
                        if maniac != 0 and (len(game_users) - 1) <= 1:
                            await db.deleteroom(call=call, state=state, chat_id=chat_id)
                            await bot.send_message(chat_id=chat_id, text='Игра окончена\nМаньяк победил')
                        else:
                            await db.deleteroom(call=call, state=state, chat_id=chat_id)
                            await call.message.answer(text="Игра окончена\nМафия победила")
                else:  # завершение игры
                    if maniac != 0 and (len(game_users) - 1) <= 1:
                        await db.deleteroom(call=call, state=state, chat_id=chat_id)
                        await bot.send_message(chat_id=chat_id, text='Игра окончена\nМаньяк победил')
                    elif maniac != 0 and (len(game_users) - 1) > 1:
                        vor = await db.text_to_roles(game_users=game_users, role='vor')
                        if vor != 0:
                            await vtcommands.voteending(call=call,game_users=game_users)
                            await call.message.answer(text='Просыпается вор')
                        else:
                            await vtcommands.voteending(call=call,game_users=game_users)
                            await db.text_to_roles(game_users=game_users, role='mani')
                            await call.message.answer(text='Просыпается маньяк')
                    else:
                        await db.deleteroom(call=call,state=state,chat_id=chat_id)
                        await call.message.answer(text='Игра окончена\nМирные победили')
            else:
                await state.storage.update_data(chat=chat_id, skipvote=0, votenum=0)
                for user in game_users:
                    user['kickvote'] = 0
                    await state.storage.set_state(chat=chat_id, user=user['user'], state=MafiaGametime.dayvote)
                await call.message.edit_text(text='Голоса распределились поровну, голосуем заново', reply_markup=mafiaauction)
