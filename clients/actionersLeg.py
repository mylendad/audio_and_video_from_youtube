from datetime import date
from clients.sqlite3_client import PostgresClient

class UserActioner:
    GET_USER = """
        SELECT user_id, username, chat_id, last_updated_date FROM users WHERE user_id = %s;
        """

    CREATE_USER = """
        INSERT INTO users (user_id, username, chat_id, last_updated_date) VALUES (?, ?, ?, ?);
        """

    UPDATE_LAST_DATE = """
        UPDATE users SET last_updated_date = ? WHERE user_id = ?;
        """

    def __init__(self, database_client: PostgresClient):
        self.database_client = database_client

    def setup(self):
        self.database_client.create_conn()

    def shutdown(self):
        self.database_client.close_conn()

    def get_user(self, user_id: str):
        user = self.database_client.execute_select_command(self.GET_USER % user_id)
        return user[0] if user else []



    def create_user(self, user_id: str, username: str, chat_id: int, last_updated_date=int):
        self.database_client.execute_command(self.CREATE_USER, (user_id, username, chat_id, last_updated_date))

    def update_date(self, user_id: str, update_date: date):
        self.database_client.execute_command(self.UPDATE_LAST_DATE, (update_date, user_id))
# last_updated_date

# user_actioner = UserActioner(SQLiteClient("users.db"))
# user_actioner.setup()
# user = user_actioner.get_user("1")
# print(user) # (1, 'luchanos', 123)
# user_2 = {"user_id": 4, "username": "test", "chat_id": 456456}
# user_actioner.create_user(**user_2)