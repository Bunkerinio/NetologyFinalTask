from VK_Operator import VK_Bot_personal
from DB_Operator import VK_Database
from VK_Operator import VK_Bot
import time

### Подтягивание токенов и параметров БД
with open(r"...VK_group_token.txt") as file:
    group_token = file.read()
with open(r"...\VK_personal_token.txt") as file:
    personal_token = file.read()
DB = ""
DB_user = ""
DB_password = ""
group_id =

# group_token = "Вставить групповой токен ВК"
# personal_token = "Вставить персональный токен ВК"
# DB = "Вставить название пустой БД"
# DB_user = "Вставить юзера пустой БД"
# DB_password = "Вставить пароль от пустой БД"
# group_id = "Вставить id сообщества"

###Инициализация экземпляров класса и экстренный перезапуск с задержкой в 30 сек
def main_function():
    try:
        Database_engine = VK_Database(DB, DB_user, DB_password)
        Search_engine = VK_Bot_personal(personal_token)
        Bot = VK_Bot(group_token, group_id)
        Database_engine.start()
        Bot.start(Search_engine, Database_engine)
    except Exception as error:
        print(f"Код был остановлен ошибкой: {error} и будет перезапущен через 5 секунд")
        time.sleep(5)
        Bot.send_error_message()
        main_function()

main_function()

