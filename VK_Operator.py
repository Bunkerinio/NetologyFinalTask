import vk_api.vk_api

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

