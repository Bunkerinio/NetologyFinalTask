import psycopg2
from psycopg2 import Error

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

    def database_user_record(self, user_id, user_info):
        _list = []
        try:
            with self.conn.cursor() as cur:
                ins_query = f"""select user_vk_id from uservk_table;"""
                cur.execute(ins_query)
                result = cur.fetchall()
                for row in result:
                    _list.append(row[0])
                if user_id in _list:
                    print("Запись о данном пользователе имеется в БД")
                else:
                    ins_query = f""" insert into UserVK_Table (user_vk_id, user_vk_name)
                                        values ({user_id}, 
                                        '{user_info['first_name']} {user_info['last_name']}') """
                    cur.execute(ins_query)
                    self.conn.commit()
                    print("Запись о новом пользователе добавлена")
        except (Exception, Error) as error:
            print("Ошибка при работе с БД (database_user_record)", error)
            self.conn.commit()

    def database_inserting(self, search_bool, search_result, user_id, offset):
        ins_search_user_id = search_result['items'][0]['id']
        ins_search_user_name = f"{search_result['items'][0]['first_name']} " \
                               f"{search_result['items'][0]['last_name']}"
        try:
            with self.conn.cursor() as cur:
                ins_query = f""" insert into SearchVK_Table (search_number, search_vk_id, search_vk_name, search_result)
                                  values ({offset}, {ins_search_user_id}, 
                                  '{ins_search_user_name}', {search_bool})"""
                cur.execute(ins_query)
                self.conn.commit()
                # print("Вставка успешна")
                ins_query = f"""select user_id from uservk_table where user_vk_id = {user_id};"""
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

    def search_number_definition(self, user_id):
        try:
            with self.conn.cursor() as cur:
                ins_query = f"""select user_id from uservk_table where user_vk_id = {user_id};"""
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

