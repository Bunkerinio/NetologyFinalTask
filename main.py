import vk_api.vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.bot_longpoll import VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload
import requests
from io import BytesIO
import datetime
import psycopg2
from psycopg2 import Error


now = datetime.datetime.now().year


class VK_Bot:

    def __init__(self, group_token, group_id, server_name: str = "Empty"):
        self.server_name = server_name
        self.vk = vk_api.VkApi(token=group_token)
        self.long_poll = VkBotLongPoll(self.vk, group_id, wait=20)
        self.vk_api = self.vk.get_api()
        self.user_id = 0
        self.user_info = {}
        self.bdate = 0
        self.sex = 0
        self.city = ""
        self.status = 0
        self.search_sex = 0
        self.age_from = self.bdate - 2
        self.age_to = self.bdate + 2
        self.search_status = 0
        self.search_city = ""
        self.search_result = {}
        self.upload = VkUpload(self.vk)
        self.http = requests.Session()
        self.list_of_most_liked_photos = []
        self.searching_id = 1
        self.hometown = 0
        self.photos_links = []
        self.attachment = []

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.message["text"].lower() == "привет":
                    self.user_info = self.vk_api.users.get(user_id=event.object["message"]["from_id"],
                                                           fields="sex, bdate, city, status")[0]
                    # print(self.user_info)
                    self.user_id = self.user_info["id"]
                    username = self.user_info["first_name"]
                    self.sex = self.user_info["sex"]
                    self.hometown = int(self.user_info["city"]["id"])
                    if "bdate" in self.user_info.keys():
                        if int(self.user_info["bdate"].split(sep=".")[-1]) < 100:
                            if int(self.user_info["bdate"].split(sep=".")[-1]) < 30:
                                self.bdate = now - int(self.user_info["bdate"].split(sep=".")[-1]) - 1900
                            else:
                                self.bdate = now - int(self.user_info["bdate"].split(sep=".")[-1]) - 2000
                        else:
                            self.bdate = now - int(self.user_info["bdate"].split(sep=".")[-1])
                    Search_engine.offset = Database_engine.search_number_definition()
                    self.status = self.user_info["status"]
                    self.age_from = self.bdate - 2
                    self.age_to = self.bdate + 2
                    self.send_message(event.object["message"]["peer_id"], f"{username}, привет!")
                    if self.sex == 1:
                        self.send_message(event.object["message"]["peer_id"], "Поищем парня?",
                                          keyboard=self.create_callback_keyboard("Не угадал", "Давай",
                                                                                 "search_sex_1", "choose_age"))
                        self.search_sex = 2
                    elif self.sex == 2:
                        self.send_message(event.object["message"]["peer_id"], "Поищем девушку?",
                                          keyboard=self.create_callback_keyboard("Не угадал", "Давай",
                                                                                 "search_sex_2", "choose_age"))
                        self.search_sex = 1
                    else:
                        self.send_message(event.object["message"]["peer_id"], "Кого будем искать??",
                                          keyboard=self.create_callback_keyboard("Парня", "Девушку", "search_sex_2",
                                                                                 "search_sex_1"))
                    Database_engine.database_user_record()
                else:
                    self.send_message(event.object["message"]["peer_id"], "Напиши, привет")
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                if event.object.payload.get('type') == "search_sex_2":
                    self.search_sex = 2
                    self.choosing_age(event)
                elif event.object.payload.get('type') == "search_sex_1":
                    self.search_sex = 1
                    self.choosing_age(event)
                elif event.object.payload.get('type') == "choose_age":
                    self.choosing_age(event)
                elif event.object.payload.get('type') == "choose_age_2":
                    self.send_message(event.object.peer_id, "Введи диапазон возрастов через дефис, "
                                                            "например 25-28")
                    for event in self.long_poll.listen():
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            self.age_from = event.message["text"].split(sep="-")[0]
                            self.age_to = event.message["text"].split(sep="-")[1]
                            break
                    if self.age_from >= self.age_to:
                        keyboard = vk_api.keyboard.VkKeyboard(one_time=True)
                        keyboard.add_callback_button("Еще разок", color=VkKeyboardColor.NEGATIVE,
                                                     payload={"type": "choose_age_2"})
                        self.send_message(event.object["message"]["peer_id"], "Что-то пошло не так. Давай еще раз",
                                          keyboard=keyboard.get_keyboard())
                    keyboard = vk_api.keyboard.VkKeyboard(one_time=True)
                    keyboard.add_callback_button("Поехали", color=VkKeyboardColor.POSITIVE,
                                                 payload={"type": "start_search"})
                    self.send_message(event.object["message"]["peer_id"], "Поехали",
                                      keyboard=keyboard.get_keyboard())
                elif event.object.payload.get('type') == "start_search":
                    self.searching(event.object.peer_id)
                elif event.object.payload.get('type') == "like" or event.object.payload.get('type') == "dislike":
                    if event.object.payload.get('type') == "like":
                        print("like")
                        Database_engine.database_inserting(True)
                    else:
                        print("dislike")
                        Database_engine.database_inserting(False)
                    self.searching(event.object.peer_id)

    def choosing_age(self, event):
        self.send_message(event.object.peer_id, f"Я вижу, что тебе {self.bdate} лет (года). "
                                                f"Поищем в диапазоне {self.bdate - 2} - {self.bdate + 2}?",
                          keyboard=self.create_callback_keyboard("Нет, я введу возраст сам", "Давай",
                                                                 "choose_age_2",
                                                                 "start_search"))

    def send_photo(self, vk, peer_id, message, keyboard):
        self.top_photos_links(self.search_result['items'][0]['id'])
        if self.search_result['items'][0]['is_closed'] == True:
            vk.messages.send(
                random_id=0,
                peer_id=peer_id,
                attachment=self.upload_photo(self.search_result['items'][0]['photo_max']),
                message=f"{message} (приватный профиль)",
                keyboard=keyboard
            )
        else:
            vk.messages.send(
                random_id=0,
                peer_id=peer_id,
                attachment=self.photos_links,
                message=message,
                keyboard=keyboard
            )

    def top_photos_links(self, id):
        self.photos_links = []
        list_of_most_liked_photos = []
        dict_of_photos_for_likes = {}
        Search_engine.top_photos(id)
        # print(Search_engine.response)
        if Search_engine.response is None:
            self.photos_links = None
            return None
        else:
            # print(f"response {Search_engine.response}")
            for _ in Search_engine.response["items"]:
                # print(_["likes"]["count"])
                list_of_most_liked_photos.append(_["likes"]["count"])
                dict_of_photos_for_likes[
                    _["likes"]["count"]] = f'photo{Search_engine.response["items"][0]["owner_id"]}_{_["id"]}'
            list_of_most_liked_photos.sort(reverse=True)
            if int(Search_engine.response["count"]) >= 3:
                for i in range(0, 3):
                    for k, v in dict_of_photos_for_likes.items():
                        if k == list_of_most_liked_photos[i]:
                            self.photos_links.append(v)
            else:
                for i in range(0, Search_engine.response["count"]):
                    for k, v in dict_of_photos_for_likes.items():
                        if k == list_of_most_liked_photos[i]:
                            self.photos_links.append(v)
            return self.photos_links

    def get_user_name(self, user_id):
        return self.vk_api.users.get(user_id=user_id)[0]['first_name']

    def get_user_city(self, user_id):
        return self.vk_api.users.get(user_id=user_id, fields="city")[0]["city"]['title']

    def get_user_sex(self, user_id):
        if self.vk_api.users.get(user_id=user_id, fields="sex")[0]["sex"] == 1:
            return "female"
        else:
            return "male"

    def get_user_bdate(self, user_id):
        return self.vk_api.users.get(user_id=user_id, fields="bdate")[0]["bdate"]

    def send_message(self, peer_id, message, keyboard=None, attachment=None):
        self.vk.get_api().messages.send(peer_id=peer_id, message=message, random_id=0, keyboard=keyboard,
                                        attachment=attachment)

    def create_keyboard(self, btn_text_no, btn_text_yes):
        keyboard = vk_api.keyboard.VkKeyboard(one_time=True)
        keyboard.add_button(btn_text_no, color=VkKeyboardColor.NEGATIVE)
        keyboard.add_button(btn_text_yes, color=VkKeyboardColor.POSITIVE)
        return keyboard.get_keyboard()

    def create_callback_keyboard(self, btn_text_no, btn_text_yes, payload_no, payload_yes):
        keyboard = vk_api.keyboard.VkKeyboard(one_time=True)
        keyboard.add_callback_button(btn_text_no, color=VkKeyboardColor.NEGATIVE, payload={"type": payload_no})
        keyboard.add_callback_button(btn_text_yes, color=VkKeyboardColor.POSITIVE, payload={"type": payload_yes})
        return keyboard.get_keyboard()

    def create_empty_keyboard(self):
        keyboard = vk_api.keyboard.VkKeyboard.get_empty_keyboard()
        return keyboard

    def searching(self, peer_id):
        self.attachment = []
        self.search_result = Search_engine.search_users(Bot.search_sex, Bot.hometown)
        # pprint(self.search_result)
        Search_engine.offset += 1
        message = f"Как тебе {self.search_result['items'][0]['first_name']} " \
                  f"{self.search_result['items'][0]['last_name']}? " \
                  f"https://vk.com/id{self.search_result['items'][0]['id']}"
        keyboard = self.create_callback_keyboard("Не нравится", "Нравится", "dislike",
                                                 "like")
        self.send_photo(self.vk_api, peer_id, message, keyboard)

    def upload_photo(self, url):
        img = requests.get(url).content
        f = BytesIO(img)
        response = VkUpload(self.vk_api).photo_messages(f)[0]
        owner_id = response['owner_id']
        photo_id = response['id']
        return f'photo{owner_id}_{photo_id}'

class VK_Bot_personal:

    def __init__(self, personal_token):
        self.personal_vk = vk_api.VkApi(token=personal_token)
        self.personal_vk_api = self.personal_vk.get_api()
        self.offset = 0
        self.response = None

    def search_users(self, sex, hometown):
        return self.personal_vk_api.users.search(count=1, offset=self.offset, sort=0,
                                                 age_from=Bot.age_from,
                                                 age_to=Bot.age_to,
                                                 sex=sex,
                                                 has_photo=1,
                                                 friend_status=0,
                                                 city_id=hometown,
                                                 #is_closed=False,
                                                 fields="bdate, photo_max, city")

    def top_photos(self, owner_id):
        try:
            self.response = self.personal_vk_api.photos.get(owner_id=owner_id,
                                                            album_id="profile",
                                                            extended=1,
                                                            fields="likes")
        except vk_api.exceptions.ApiError:
            print("Приватный профиль, загрузка фото невозможна")
            return None


class VK_Database:
    def __init__(self, DB, DB_user, DB_password):
        self.database = DB
        self.user = DB_user
        self.password = DB_password
        self.conn = psycopg2.connect(database=self.database,
                                     user=self.user,
                                     password=self.password)
        self.search_number = 0

    def start(self):
        try:
            with self.conn.cursor() as cur:
                create_table_query = '''
                create table if not exists UserVK_Table (
                user_id serial primary key,
                user_vk_id int not null,
                user_vk_name varchar(60) not null,
                unique (user_vk_id));
                create table if not exists SearchVK_Table (
                search_id serial primary key,
                search_number int not null,
                search_vk_id int not null,
                search_vk_name varchar(60) not null,
                search_result bool);
                create table if not exists UserSearchVK_table (
                sum_user_id int,
                sum_search_id int,
                foreign key (sum_user_id) references UserVK_Table (user_id),
                foreign key (sum_search_id) references SearchVK_Table (search_id));'''
                cur.execute(create_table_query)
                self.conn.commit()
                print("Конфигурация БД развернута")
        except (Exception, Error) as error:
            print("Ошибка при работе с БД (start)", error)

    def database_user_record(self):
        _list = []
        try:
            with self.conn.cursor() as cur:
                ins_query = f"""select user_vk_id from uservk_table;"""
                cur.execute(ins_query)
                result = cur.fetchall()
                for row in result:
                    _list.append(row[0])
                if Bot.user_id in _list:
                    print("Запись о данном пользователе имеется в БД")
                else:
                    ins_query = f""" insert into UserVK_Table (user_vk_id, user_vk_name)
                                        values ({Bot.user_id}, 
                                        '{Bot.user_info['first_name']} {Bot.user_info['last_name']}') """
                    cur.execute(ins_query)
                    self.conn.commit()
                    print("Запись о новом пользователе добавлена")
        except (Exception, Error) as error:
            print("Ошибка при работе с БД (database_user_record)", error)
            self.conn.commit()

    def database_inserting(self, search_result):
        ins_search_user_id = Bot.search_result['items'][0]['id']
        ins_search_user_name = f"{Bot.search_result['items'][0]['first_name']} " \
                               f"{Bot.search_result['items'][0]['last_name']}"
        try:
            with self.conn.cursor() as cur:
                ins_query = f""" insert into SearchVK_Table (search_number, search_vk_id, search_vk_name, search_result)
                                  values ({Search_engine.offset}, {ins_search_user_id}, 
                                  '{ins_search_user_name}', {search_result})"""
                cur.execute(ins_query)
                self.conn.commit()
                # print("Вставка успешна")
                ins_query = f"""select user_id from uservk_table where user_vk_id = {Bot.user_id};"""
                cur.execute(ins_query)
                sum_user_id = cur.fetchall()[0][0]
                # print(f"Вставка sum_user_id {sum_user_id}")
                ins_query = f"""select search_id from searchvk_table ORDER BY search_id DESC LIMIT 1;"""
                cur.execute(ins_query)
                sum_search_id = cur.fetchall()[0][0]
                # print(f"Вставка sum_search_id {sum_search_id}")
                ins_query = f""" insert into usersearchvk_table (sum_user_id, sum_search_id)
                                                  values ({sum_user_id}, {sum_search_id})"""
                cur.execute(ins_query)
                self.conn.commit()
                # print("Запись добавлена")
        except (Exception, Error) as error:
            print("Ошибка при работе с БД (database_inserting)", error)
            self.conn.commit()

    def search_number_definition(self):
        try:
            with self.conn.cursor() as cur:
                ins_query = f"""select user_id from uservk_table where user_vk_id = {Bot.user_id};"""
                cur.execute(ins_query)
                sum_user_id = cur.fetchall()
                if len(sum_user_id) != 0:
                    ins_query = f"""select sum_search_id from usersearchvk_table where sum_user_id = {sum_user_id[0][0]}
                    ORDER BY sum_search_id DESC LIMIT 1;"""
                    cur.execute(ins_query)
                    sum_search_id = cur.fetchall()
                    if len(sum_search_id) != 0:
                        ins_query = f"""select search_number from searchvk_table where search_id = {sum_search_id[0][0]} 
                        ORDER BY search_number DESC LIMIT 1;"""
                        cur.execute(ins_query)
                        return cur.fetchall()[0][0]
                    else:
                        return 0
                else:
                    return 0
        except (Exception, Error) as error:
            print("Ошибка при работе с БД (search_number_definition)", error)
            self.conn.commit()

### Подтягивание токенов и параметров БД
with open(r"...\VK_group_token.txt") as file:
    group_token = file.read()
with open(r"...\VK_personal_token.txt") as file:
    personal_token = file.read()

# group_token = "Вставить групповой токен ВК"
# personal_token = "Вставить персональный токен ВК"
DB = "Вставить название пустой БД"
DB_user = "Вставить юзера пустой БД"
DB_password = "Вставить пароль от пустой БД"

###Инициализация экземпляров класса
Bot = VK_Bot(group_token, 217451624, "server1")
Search_engine = VK_Bot_personal(personal_token)
Database_engine = VK_Database(DB, DB_user, DB_password)
Database_engine.start()
Bot.start()
