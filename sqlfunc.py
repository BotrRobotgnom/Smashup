import pymysql
from config import sql
import json


def transform_sql_to_norm(rows):            
    l_row = []
    for k in rows.items():
        l_row.append(k[1])
    return l_row


def sql_py(key, sql_quest):
    key_print = "sqlfunc.py: "

    try:
        connection = pymysql.connect(
            host=sql['host'],
            port=3306,
            user=sql['user'],
            password=sql['password'],
            database=sql['db_name'],
            cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                if key == "get":
                    cursor.execute("SELECT * FROM smashup WHERE server_id = %s", (sql_quest[0]))
                    rows = cursor.fetchone()
                    if rows is None:
                        sample_list = []
                        list_to_json_array = json.dumps(sample_list)
                        cursor.execute("INSERT INTO smashup (server_id, back_play, now_play, next_play) "
                                       "VALUES (%s, %s, %s, %s)",
                                       (str(sql_quest[0]), list_to_json_array, list_to_json_array, list_to_json_array))
                        connection.commit()

                        cursor.execute("SELECT * FROM smashup WHERE server_id = %s", (sql_quest[0]))
                        rows = cursor.fetchone()
                    return rows
                elif key == "update":
                    cursor.execute("UPDATE smashup SET back_play = %s, now_play = %s, next_play = %s "
                                   "WHERE server_id = %s", (sql_quest[1], sql_quest[2], sql_quest[3], sql_quest[0]))
                    connection.commit()
                elif key == "update_next":
                    cursor.execute("UPDATE smashup SET next_play = %s "
                                   "WHERE server_id = %s", (sql_quest[1], sql_quest[0]))
                    connection.commit()
        finally:
            connection.close()
    except Exception as ex:
        print(f"{key_print}Connection refused...")
        print(ex)
