import vk_api.vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.bot_longpoll import VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload
import requests
import datetime
from io import BytesIO

now = datetime.datetime.now().year

class VK_Bot_personal:

    def __init__(self, personal_token):
        self.personal_vk = vk_api.VkApi(token=personal_token)
        self.personal_vk_api = self.personal_vk.get_api()
        self.offset = 0
        self.response = None

    def search_users(self, sex, hometown, age_from, age_to):
        return self.personal_vk_api.users.search(count=1, offset=self.offset, sort=0,
                                                 age_from=age_from,
                                                 age_to=age_to,
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

    def start(self, s_engine, db_engine):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.message["text"].lower() == "привет":
                    self.user_info = self.vk_api.users.get(user_id=event.object["message"]["from_id"],
                                                           fields="sex, bdate, city, status")[0]
                    # print(self.user_info)
                    self.user_id = self.user_info["id"]
                    username = self.user_info["first_name"]
                    self.sex = self.user_info["sex"]
                    try:
                        self.hometown = int(self.user_info["city"]["id"])
                    except KeyError:
                        self.hometown = 1
                    if "bdate" in self.user_info.keys():
                        if int(self.user_info["bdate"].split(sep=".")[-1]) < 100:
                            if int(self.user_info["bdate"].split(sep=".")[-1]) < 30:
                                self.bdate = now - int(self.user_info["bdate"].split(sep=".")[-1]) - 1900
                            else:
                                self.bdate = now - int(self.user_info["bdate"].split(sep=".")[-1]) - 2000
                        else:
                            self.bdate = now - int(self.user_info["bdate"].split(sep=".")[-1])
                    s_engine.offset = db_engine.search_number_definition(self.user_id)
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
                    db_engine.database_user_record(self.user_id, self.user_info)
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
                    else:
                        keyboard = vk_api.keyboard.VkKeyboard(one_time=True)
                        keyboard.add_callback_button("Поехали", color=VkKeyboardColor.POSITIVE,
                                                     payload={"type": "start_search"})
                        self.send_message(event.object["message"]["peer_id"], "Поехали",
                                          keyboard=keyboard.get_keyboard())
                elif event.object.payload.get('type') == "start_search":
                    self.searching(event.object.peer_id, s_engine)
                elif event.object.payload.get('type') == "like" or event.object.payload.get('type') == "dislike":
                    if event.object.payload.get('type') == "like":
                        #print("like")
                        db_engine.database_inserting(True, self.search_result, self.user_id, s_engine.offset)
                    else:
                        #print("dislike")
                        db_engine.database_inserting(False, self.search_result, self.user_id, s_engine.offset)
                    self.searching(event.object.peer_id, s_engine)

    def choosing_age(self, event):
        self.send_message(event.object.peer_id, f"Я вижу, что тебе {self.bdate} лет (года). "
                                                f"Поищем в диапазоне {self.bdate - 2} - {self.bdate + 2}?",
                          keyboard=self.create_callback_keyboard("Нет, я введу возраст сам", "Давай",
                                                                 "choose_age_2",
                                                                 "start_search"))

    def send_photo(self, vk, peer_id, message, keyboard, s_engine):
        self.top_photos_links(self.search_result['items'][0]['id'], s_engine)
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

    def top_photos_links(self, id, s_engine):
        self.photos_links = []
        list_of_most_liked_photos = []
        dict_of_photos_for_likes = {}
        s_engine.top_photos(id)
        # print(Search_engine.response)
        if s_engine.response is None:
            self.photos_links = None
            return None
        else:
            # print(f"response {Search_engine.response}")
            for _ in s_engine.response["items"]:
                # print(_["likes"]["count"])
                list_of_most_liked_photos.append(_["likes"]["count"])
                dict_of_photos_for_likes[
                    _["likes"]["count"]] = f'photo{s_engine.response["items"][0]["owner_id"]}_{_["id"]}'
            list_of_most_liked_photos.sort(reverse=True)
            if int(s_engine.response["count"]) >= 3:
                for i in range(0, 3):
                    for k, v in dict_of_photos_for_likes.items():
                        if k == list_of_most_liked_photos[i]:
                            self.photos_links.append(v)
            else:
                for i in range(0, s_engine.response["count"]):
                    for k, v in dict_of_photos_for_likes.items():
                        if k == list_of_most_liked_photos[i]:
                            self.photos_links.append(v)
            return self.photos_links

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

    def searching(self, peer_id, s_engine):
        self.attachment = []
        self.search_result = s_engine.search_users(self.search_sex, self.hometown, self.age_from, self.age_to)
        # pprint(self.search_result)
        s_engine.offset += 1
        message = f"Как тебе {self.search_result['items'][0]['first_name']} " \
                  f"{self.search_result['items'][0]['last_name']}? " \
                  f"https://vk.com/id{self.search_result['items'][0]['id']}"
        keyboard = self.create_callback_keyboard("Не нравится", "Нравится", "dislike",
                                                 "like")
        self.send_photo(self.vk_api, peer_id, message, keyboard, s_engine)

    def upload_photo(self, url):
        img = requests.get(url).content
        f = BytesIO(img)
        response = VkUpload(self.vk_api).photo_messages(f)[0]
        owner_id = response['owner_id']
        photo_id = response['id']
        return f'photo{owner_id}_{photo_id}'


