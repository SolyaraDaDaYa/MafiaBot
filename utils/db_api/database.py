import asyncio
from loader import bot
from keyboards.inline import mafiabuttons
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from gino import Gino
from gino.schema import GinoSchemaVisitor
from data.config import POSTGRES_URI
from aiogram import types
from aiogram.dispatcher import FSMContext
from sqlalchemy import (Column, Integer, String, BigInteger)
from sqlalchemy import sql
import random
db = Gino()


class Users(db.Model):
    __tablename__ = 'Users'
    query: sql.Select

    id = Column(Integer, primary_key=True, unique=True)
    user_id = Column(BigInteger, unique=True)
    username = Column(String)
    full_name = Column(String)
    user_link = Column(String)


class GameRoom(db.Model):
    __tablename__ = 'GameRoom'
    query: sql.Select

    id = Column(Integer, primary_key=True, unique=True)
    game_room_id = Column(BigInteger, key=True)
    guser_id = Column(BigInteger, unique=True, nullable=True)
    guser_num = Column(Integer, nullable=True)
    guser_role = Column(String, nullable=True)
    guser_name = Column(String, nullable=True)


# Документация
# http://gino.fantix.pro/en/latest/tutorials/tutorial.html

async def create_db():
    # Устанавливаем связь с базой данных
    await db.set_bind(POSTGRES_URI)
    db.gino: GinoSchemaVisitor

    # Создаем таблицы
    #await db.gino.drop_all() # для тестов
    await db.gino.create_all()


class DBCommands:
    db.gino: GinoSchemaVisitor

    async def get_user(self, user_id):
        user = await Users.query.where(Users.user_id == user_id).gino.first()
        return user

    async def add_new_user(self):
        user = types.User.get_current()
        old_user = await self.get_user(user.id)
        if old_user:
            return old_user
        new_user = Users()
        new_user.user_id = user.id
        new_user.username = user.username
        new_user.full_name = user.full_name
        new_user.user_link = user.url

        await new_user.create()
        return new_user

    async def get_user_url(self, anketa_id):
        user = await Users.query.where(Users.user_id == anketa_id).gino.first()
        return user.user_link

    async def create_game_room(self, users_id, users_names, usercount):
        # roleslist = ['Вор', 'Мафия']
        if usercount == 6:
            roleslist = ['Дон(мафия)','Мирный житель','Мафия','Вор','Доктор','Шериф']
        elif usercount == 9:
            roleslist = ['Дон(мафия)', 'Мирный житель', 'Мафия', 'Мирный житель', 'Доктор', 'Шериф', 'Маньяк', 'Мафия', 'Вор']

        key = users_id[0]
        iterusers = zip([x for x in range(1,usercount + 1)], users_id, users_names)
        for num, user, user_name in iterusers:
            room = GameRoom()
            room.game_room_id = key
            room.guser_id = user
            room.guser_num = num
            room.guser_role = roleslist.pop(random.randint(0, len(roleslist) - 1))
            room.guser_name = user_name
            await room.create()

    async def get_game_room_key(self, user_id):
        users = await GameRoom.query.where(GameRoom.guser_id == user_id).gino.first()
        return users.game_room_id

    async def delete_game_room(self, key):
        games = await GameRoom.query.where(GameRoom.game_room_id == key).gino.all()
        [await game.delete() for game in games]

    async def get_all_users(self, key):
        users = await GameRoom.query.where(GameRoom.game_room_id == key).gino.all()
        return users

    async def get_users_roles(self,game_users,role):
        if role == 'maf':
            mafia = []
            for user in game_users:
                if user.get('user_role') == 'Мафия' or user.get('user_role') == 'Дон(мафия)':
                    mafia.append(user)
            if mafia == []:
                return 0
            else:
                return mafia
        elif role == 'don':
            don = 0
            for user in game_users:
                if user['user_role'] == 'Дон(мафия)':
                    don = user
                    break
            return don
        elif role == 'doc':
            doctor = 0
            for user in game_users:
                if user.get('user_role') == 'Доктор':
                    doctor = user
                    break
            return doctor
        elif role == 'sher':
            sherif = 0
            for user in game_users:
                if user.get('user_role') == 'Шериф':
                    sherif = user
                    break
            return sherif
        elif role == 'vor':
            vor = 0
            for user in game_users:
                if user.get('user_role') == 'Вор':
                    vor = user
                    break
            return vor
        elif role == 'mani':
            maniac = 0
            for user in game_users:
                if user.get('user_role') == 'Маньяк':
                    maniac = user
                    break
            return maniac

    async def text_to_roles(self, game_users, role, ishealuser=None, maniacisheal=None, ismute=None):
        sorted_salaries = sorted(game_users, key=lambda d: d['user_num'])
        if role == 'maf':
            mafia = await self.get_users_roles(game_users=game_users, role='maf')
            if mafia != 0:
                mafiamafiakill = InlineKeyboardMarkup(
                    inline_keyboard=
                    [
                        [InlineKeyboardButton(text=f"{user.get('user_num')} {user['user_name']}",
                                              callback_data=mafiabuttons.mafiacalldata.new(user=user['user'])) for user
                         in sorted_salaries],
                    ]
                )
                mafiadoncheck = InlineKeyboardMarkup(
                    inline_keyboard=
                    [
                        [InlineKeyboardButton(text=f"{user.get('user_num')} {user['user_name']}",
                                              callback_data=mafiabuttons.mafiadoncalldata.new(user=user['user'])) for
                         user in sorted_salaries],
                    ]
                )
                for maf in mafia:
                    await bot.send_message(chat_id=maf.get('user'), text=f'Выберите свою цель\nВы можете общаться через этого бота(в любой момент игры)',
                                                 reply_markup=mafiamafiakill)
                    await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд
                    if maf['user_role'] == 'Дон(мафия)':
                        await bot.send_message(chat_id=maf.get('user'),
                                               text='Выберите кого проверить',
                                               reply_markup=mafiadoncheck)
                        await asyncio.sleep(delay=0.3)  # чтобы не получить бан за флуд

                return mafia
            else:
                return 0

        elif role == 'vor':
            vor = await self.get_users_roles(game_users=game_users, role='vor')
            if vor != 0:
                for user in sorted_salaries:
                    if user['user'] == ismute:
                        sorted_salaries.remove(user)
                        break
                    elif ismute == None:
                        break
                mafiavor = InlineKeyboardMarkup(
                    inline_keyboard=
                    [
                        [InlineKeyboardButton(text=f"{user.get('user_num')} {user['user_name']}", callback_data=mafiabuttons.mafiacalldata.new(user=user['user'])) for user in sorted_salaries],
                    ]
                )

                await bot.send_message(chat_id=vor.get('user'), text='Выберите кого замутить', reply_markup=mafiavor)

            return vor

        elif role == 'mani':
            maniac = await self.get_users_roles(game_users=game_users, role='mani')
            if maniac != 0:
                for user in sorted_salaries:
                    if user['user_num'] == maniacisheal:
                        sorted_salaries.remove(user)
                        break
                    elif maniacisheal == None:
                        break
                mafiamaniac = InlineKeyboardMarkup(
                    inline_keyboard=
                    [
                        [InlineKeyboardButton(text=f"{user.get('user_num')} {user['user_name']}",
                                              callback_data=mafiabuttons.mafiacalldata.new(user=user['user'])) for user
                         in sorted_salaries],
                    ]
                )

                await bot.send_message(chat_id=maniac.get('user'), text='Выберите кого убить\nЕсли выбрать себя вы излечитесь', reply_markup=mafiamaniac)

        elif role == 'doc':
            doctor = await self.get_users_roles(game_users=game_users, role='doc')
            if doctor != 0:
                for user in sorted_salaries:
                    if user['user_num'] == ishealuser:
                        sorted_salaries.remove(user)
                        break
                    elif ishealuser == None:
                        break
                mafiadoctor = InlineKeyboardMarkup(
                    inline_keyboard=
                    [
                        [InlineKeyboardButton(text=f"{user.get('user_num')} {user['user_name']}",
                                              callback_data=mafiabuttons.mafiacalldata.new(user=user['user'])) for user
                         in sorted_salaries],
                    ]
                )

                await bot.send_message(chat_id=doctor.get("user"), text='Выберите кого вылечить',
                                       reply_markup=mafiadoctor)

            return doctor

        elif role == 'sher':
            sherif = await self.get_users_roles(game_users=game_users, role='sher')
            if sherif != 0:
                mafiasherif = InlineKeyboardMarkup(
                    inline_keyboard=
                    [
                        [InlineKeyboardButton(text=f"{user.get('user_num')} {user['user_name']}",
                                              callback_data=mafiabuttons.mafiacalldata.new(user=user['user'])) for user
                         in sorted_salaries],
                    ]
                )
                await bot.send_message(chat_id=sherif.get("user"), text='Выберите кого проверить',
                                       reply_markup=mafiasherif)

            return sherif

    async def deleteroom(self, call:types.CallbackQuery, state: FSMContext, chat_id):
        users_room_key = await self.get_game_room_key(user_id=call.from_user.id)
        users_room = await self.get_all_users(key=users_room_key)
        for user in users_room:
            await state.storage.reset_state(chat=chat_id, user=user.guser_id)
            await state.storage.reset_state(chat=user.guser_id, user=user.guser_id)
            await state.storage.reset_data(chat=user.guser_id, user=user.guser_id)
            try:
                await bot.restrict_chat_member(chat_id=chat_id, user_id=user.guser_id,
                                               can_send_other_messages=True)
            except:
                pass
        await self.delete_game_room(key=users_room_key)
