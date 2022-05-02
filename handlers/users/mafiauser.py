from loader import dp, bot
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from utils.db_api.database import DBCommands
from states.mafiastate import MafiaRoles, MafiaGametime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline import mafiabuttons
import asyncio
db = DBCommands()


async def mafia_vote_kick(call: CallbackQuery, state: FSMContext, chat_id, game_users, whokilluser, don):
    await call.message.edit_reply_markup()
    for user in game_users:
        if user['user'] == whokilluser:
            if call.from_user.id == don['user']:
                user['mafiakickvote'] += 1.5
            else:
                user['mafiakickvote'] += 1.0
    await state.storage.update_data(chat=chat_id, game_users=game_users)


async def kick_users(state: FSMContext,kickedusers,chat_id):
    for kickuser in kickedusers:
        await state.storage.reset_state(chat=chat_id, user=kickuser['user'])
        await state.storage.reset_state(chat=kickuser['user'], user=kickuser['user'])


async def auction_unmute(call: CallbackQuery, state: FSMContext,game_users1,chat_id,ismute):
    mafia = await db.get_users_roles(game_users=game_users1, role='maf')
    if len(mafia) < (len(game_users1) - len(mafia)):
        for user in game_users1:
            if user['user'] == ismute:
                await state.storage.set_state(chat=chat_id, user=user['user'], state=MafiaGametime.dayvote)
            else:
                await state.storage.set_state(chat=chat_id, user=user['user'], state=MafiaGametime.dayvote)
                try:
                    await bot.restrict_chat_member(chat_id=chat_id, user_id=user['user'],
                                                   can_send_other_messages=True)  # размут челов
                except:
                    pass

        await state.storage.update_data(chat=chat_id, game_users=game_users1, ismute=0)
    else:
        await db.deleteroom(call=call, state=state, chat_id=chat_id)
        await bot.send_message(chat_id=chat_id, text='Игра окончена\nМафия победила')


async def text_auction(game_users,chat_id):
    kickcheck = [user.get('kick') for user in game_users]
    kickedusers = []
    if kickcheck.count(True):
        for user in game_users:
            if user.get('kick') == True: # тут break не надо
                await bot.send_message(chat_id=chat_id, text=f'Этой ночью умер игрок №{user.get("user_num")} {user["user_name"]}\nЕго роль: {user["user_role"]}')
                await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
                game_users.remove(user)
                kickedusers.append(user)
    else:
        await bot.send_message(chat_id=chat_id, text='Этой ночью никто не умер')

    mafia = await db.get_users_roles(game_users=game_users, role='maf')
    if mafia != 0:
        if len(mafia) < (len(game_users) - len(mafia)):
            mafiaauction = InlineKeyboardMarkup(
                inline_keyboard=
                [
                    [InlineKeyboardButton(text=f"{user.get('user_num')} {user['user_name']}", callback_data=mafiabuttons.mafiacalldata.new(user=user['user'])) for user in game_users],
                    [InlineKeyboardButton(text='Пропустить', callback_data=mafiabuttons.mafiacalldata.new(user='skip'))]
                ]
            )
            await bot.send_message(chat_id=chat_id, text='Голосование', reply_markup=mafiaauction)
            return (game_users, kickedusers)
        else:
            return (game_users, kickedusers)
    else:
        return 0, kickedusers


@dp.message_handler(state=MafiaRoles.mafia)
async def do_mafia_chat(message: Message, state: FSMContext):

    userdata = await state.storage.get_data(user=message.from_user.id)
    chat_id = userdata.get('chat_id')
    chatadata = await state.storage.get_data(chat=chat_id)
    mafia = chatadata.get('mafia')

    text = f'<b>№{userdata.get("user_num")}</b>\n {message.text}'
    for user in mafia:
        if user.get('user') != message.from_user.id:
            await bot.send_message(chat_id=user.get('user'), text=text)
            await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд


@dp.callback_query_handler(mafiabuttons.mafiacalldata.filter(), state=MafiaRoles.vor)
async def vor_mute_user(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.message.edit_reply_markup()
    whomuteuser = int(callback_data['user'])
    userdata = await state.storage.get_data(user=call.from_user.id)
    chat_id = userdata.get('chat_id')
    chatadata = await state.storage.get_data(chat=chat_id)
    ismute = chatadata['ismute']
    game_users = chatadata.get('game_users')

    for user in game_users:
        if user['user'] == whomuteuser:
            ismute = user['user']
            await bot.send_message(chat_id=chat_id, text=f'Игрок №{user["user_num"]} в муте.')
            break

    await state.storage.update_data(chat=chat_id, ismute=ismute)
    await bot.send_message(chat_id=chat_id, text='Вор сделал свой выбор')
    await asyncio.sleep(0.5)
    # сообщения мафии
    mafia = await db.text_to_roles(game_users=game_users, role='maf')
    if mafia != 0:
        await bot.send_message(chat_id=chat_id, text='Просыпается мафия')
    else:
        await db.text_to_roles(game_users=game_users, role='mani')
        await bot.send_message(chat_id=chat_id, text='Просыпается маньяк')


@dp.callback_query_handler(mafiabuttons.mafiadoncalldata.filter(), state=MafiaRoles.mafia)
async def don_check_user(call: CallbackQuery, callback_data: dict, state: FSMContext):
    whomcheckuser = int(callback_data['user'])
    userdata = await state.storage.get_data(user=call.from_user.id)
    chat_id = userdata.get('chat_id')
    chatadata = await state.storage.get_data(chat=chat_id)
    ismute = chatadata['ismute']
    game_users = chatadata.get('game_users')
    if call.from_user.id == ismute:
        await call.message.edit_text(text='Тебя замутили')
    else:
        for user in game_users:
            if user.get('user') == whomcheckuser:
                if user.get('user_role') == 'Шериф':
                    await call.message.edit_text(text=f'Игрок №{user.get("user_num")} {user["user_name"]} шериф.')
                    await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
                else:
                    await call.message.edit_text(text=f'Игрок №{user.get("user_num")} {user["user_name"]} не шериф.')
                    await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
                break


@dp.callback_query_handler(mafiabuttons.mafiacalldata.filter(), state=MafiaRoles.mafia)
async def mafia_kill_user(call: CallbackQuery, callback_data: dict, state: FSMContext):
    whokilluser = int(callback_data['user'])
    userdata = await state.storage.get_data(user=call.from_user.id)
    chat_id = userdata.get('chat_id')
    chatadata = await state.storage.get_data(chat=chat_id)
    game_users = chatadata.get('game_users')
    ismute = chatadata['ismute']
    mafia = chatadata['mafia']
    mafiavotecount = chatadata['mafiavotecount']
    mafiavotecount += 1

    mafiacankill = True
    for maf in mafia:
        if maf['user'] == ismute:
            mafiacankill = False
            break

    if mafiacankill:
        don = await db.get_users_roles(game_users=game_users, role='don')

        if mafiavotecount != len(mafia):
            await mafia_vote_kick(call=call, state=state, chat_id=chat_id, game_users=game_users, whokilluser=whokilluser, don=don)
            await state.storage.update_data(chat=chat_id, game_users=game_users, mafiavotecount=mafiavotecount)
        else:
            await mafia_vote_kick(call=call, state=state, chat_id=chat_id, game_users=game_users, whokilluser=whokilluser, don=don)
            await bot.send_message(chat_id=chat_id, text='Мафия сделала свой выбор')

            mafiavotes = sorted(game_users, key=lambda d: d['mafiakickvote'], reverse=True)
            for user in game_users:
                if user['user'] == mafiavotes[0].get('user'):
                    user['kick'] = True
                user['mafiakickvote'] = 0.0
            await state.storage.update_data(chat=chat_id, game_users=game_users, mafiavotecount=0)

            # сообщение маньякичу
            maniacisheal = chatadata['maniacisheal']
            maniac = await db.text_to_roles(game_users=game_users, role='mani', maniacisheal=maniacisheal)
            if maniac != 0:
                await bot.send_message(chat_id=chat_id, text='Просыпается маньяк')
            else:
                ishealuser = chatadata['isheal']
                doctor = await db.text_to_roles(game_users=game_users, role='doc', ishealuser=ishealuser)
                if doctor != 0:
                    await bot.send_message(chat_id=chat_id, text='Просыпается доктор')
                else:
                    sherif = await db.text_to_roles(game_users=game_users, role='sher')
                    if sherif != 0:
                        await bot.send_message(chat_id=chat_id, text='Просыпается шериф')
    else:
        if mafiavotecount != len(mafia):
            await call.message.edit_text(text='Одного из вас замутили!')
            await state.storage.update_data(chat=chat_id, mafiavotecount=mafiavotecount)
        else:
            await call.message.edit_text(text='Одного из вас замутили!')
            await state.storage.update_data(chat=chat_id, mafiavotecount=0)
            await bot.send_message(chat_id=chat_id, text='Мафия сделала свой выбор')
            # сообщение маньякичу
            maniacisheal = chatadata['maniacisheal']
            maniac = await db.text_to_roles(game_users=game_users, role='mani', maniacisheal=maniacisheal)
            if maniac != 0:
                await bot.send_message(chat_id=chat_id, text='Просыпается маньяк')
            else:
                ishealuser = chatadata['isheal']
                doctor = await db.text_to_roles(game_users=game_users, role='doc', ishealuser=ishealuser)
                if doctor != 0:
                    await bot.send_message(chat_id=chat_id, text='Просыпается доктор')
                else:
                    sherif = await db.text_to_roles(game_users=game_users, role='sher')
                    if sherif != 0:
                        await bot.send_message(chat_id=chat_id, text='Просыпается шериф')


@dp.callback_query_handler(mafiabuttons.mafiacalldata.filter(), state=MafiaRoles.maniac)
async def maniac_user(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.message.edit_reply_markup()
    whoselectmaniacuser = int(callback_data['user'])
    userdata = await state.storage.get_data(user=call.from_user.id)
    chat_id = userdata.get('chat_id')
    chatadata = await state.storage.get_data(chat=chat_id)
    maniacisheal = chatadata['maniacisheal']
    ismute = chatadata['ismute']
    game_users = chatadata.get('game_users')
    if call.from_user.id == ismute:
        await call.message.edit_text(text='Тебя замутили')
        await asyncio.sleep(2)
    else:
        for user in game_users:
            if user['user'] == whoselectmaniacuser:
                if user['user_role'] == 'Маньяк':
                    user['kick'] = False
                    maniacisheal = user['user_num']
                else:
                    user['kick'] = True
                    maniacisheal = None
                break
        await state.storage.update_data(chat=chat_id, game_users=game_users, maniacisheal=maniacisheal)

    await bot.send_message(chat_id=chat_id, text='Маньяк сделал свой выбор')
    # сообщение доктору
    ishealuser = chatadata['isheal']
    doctor = await db.text_to_roles(game_users=game_users, role='doc', ishealuser=ishealuser)
    if doctor != 0:
        await bot.send_message(chat_id=chat_id, text='Просыпается доктор')
    else:
        sherif = await db.text_to_roles(game_users=game_users, role='sher')
        if sherif != 0:
            await bot.send_message(chat_id=chat_id, text='Просыпается шериф')


@dp.callback_query_handler(mafiabuttons.mafiacalldata.filter(), state=MafiaRoles.doctor)
async def doctor_heal_user(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.message.edit_reply_markup()
    whohealuser = int(callback_data['user'])
    userdata = await state.storage.get_data(user=call.from_user.id)
    chat_id = userdata.get('chat_id')
    chatadata = await state.storage.get_data(chat=chat_id)
    isheal = chatadata['isheal']
    ismute = chatadata['ismute']
    game_users = chatadata.get('game_users')
    if call.from_user.id == ismute:
        await call.message.edit_text(text='Тебя замутили')
        await asyncio.sleep(2)
    else:
        for user in game_users:
            if user.get('user') == whohealuser:
                user['kick'] = False
                isheal = user.get('user_num')
                break

        await state.storage.update_data(chat=chat_id, game_users=game_users, isheal=isheal)
    await bot.send_message(chat_id=chat_id, text='Доктор сделал свой выбор')

    # сообщение шерифу
    sherif = await db.text_to_roles(game_users=game_users, role='sher')
    if sherif != 0:
        await bot.send_message(chat_id=chat_id, text='Просыпается шериф')
    else:
        await bot.send_message(chat_id=chat_id, text='Город просыпается')
        game_users1,kickedusers = await text_auction(game_users=game_users, chat_id=chat_id)
        maniac = await db.get_users_roles(game_users=game_users1, role='mani')
        if len(kickedusers) != 0: # кикать челов
            await kick_users(state=state,kickedusers=kickedusers,chat_id=chat_id)
        if game_users1 != 0:
            if maniac != 0 and (len(game_users1) - 1) <= 1:
                await db.deleteroom(call=call, state=state, chat_id=chat_id)
                await bot.send_message(chat_id=chat_id, text='Игра окончена\nМаньяк победил')
            else:
                await auction_unmute(call=call,state=state,game_users1=game_users1,chat_id=chat_id, ismute=ismute)
        else:
            if maniac != 0 and (len(game_users1) - 1) <= 1:
                await db.deleteroom(call=call, state=state, chat_id=chat_id)
                await bot.send_message(chat_id=chat_id, text='Игра окончена\nМаньяк победил')
            else:
                await db.deleteroom(call=call,state=state,chat_id=chat_id)
                await bot.send_message(chat_id=chat_id,text='Игра окончена\nМирные победили')


@dp.callback_query_handler(mafiabuttons.mafiacalldata.filter(), state=MafiaRoles.sher)
async def sherif_check_user(call: CallbackQuery, callback_data: dict, state: FSMContext):
    whocheckuser = int(callback_data['user'])
    userdata = await state.storage.get_data(user=call.from_user.id)
    chat_id = userdata.get('chat_id')
    chatadata = await state.storage.get_data(chat=chat_id)
    ismute = chatadata['ismute']
    game_users = chatadata.get('game_users')
    if call.from_user.id == ismute:
        await call.message.edit_text(text='Тебя замутили')
        await asyncio.sleep(2)
    else:
        for user in game_users:
            if user.get('user') == whocheckuser:
                if user.get('user_role') == 'Мафия' or user.get('user_role') == 'Дон(мафия)':
                    await call.message.edit_text(text=f'Игрок №{user.get("user_num")} {user["user_name"]} мафия.')
                    await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
                else:
                    await call.message.edit_text(text=f'Игрок №{user.get("user_num")} {user["user_name"]} не мафия.')
                    await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
                break
    await bot.send_message(chat_id=chat_id, text='Город просыпается')
    await asyncio.sleep(1)
    game_users1,kickedusers = await text_auction(game_users=game_users, chat_id=chat_id)
    maniac = await db.get_users_roles(game_users=game_users1, role='mani')
    if len(kickedusers) != 0: # кикать челов
        await kick_users(state=state,kickedusers=kickedusers,chat_id=chat_id)
    if game_users1 != 0:
        if maniac != 0 and (len(game_users1) - 1) <= 1:
            await db.deleteroom(call=call, state=state, chat_id=chat_id)
            await bot.send_message(chat_id=chat_id, text='Игра окончена\nМаньяк победил')
        else:
            await auction_unmute(call=call, state=state, game_users1=game_users1, chat_id=chat_id, ismute=ismute)
    else:
        if maniac != 0 and (len(game_users1) - 1) <= 1:
            await db.deleteroom(call=call, state=state, chat_id=chat_id)
            await bot.send_message(chat_id=chat_id, text='Игра окончена\nМаньяк победил')
        else:
            await db.deleteroom(call=call,state=state,chat_id=chat_id)
            await bot.send_message(chat_id=chat_id,text='Игра окончена\nМирные победили')