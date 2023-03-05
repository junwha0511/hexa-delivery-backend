
from dotenv import dotenv_values

server_secure_config = dotenv_values(".env") 

DATABASE = "test.db"

ORDERDAO_REQUIRED_PARAMETERS = ("exp_time", "meeting_place", "group_link", "rid", "member_num", "uid")
ORDER_CATEGORY = ('치킨', '피자', '양식', '한식', '중식', '일식', '분식', '야식', '간식')

RES_STATUS_KEY = "status"
RES_DATA_KEY = "data"
RES_ERROR_MESSAGE = "error_message"

JWT_SECRET_KEY = server_secure_config["JWT_SECRET_KEY"]
ENCRYPTED_KEY = server_secure_config["ENCRYPTED_KEY"]
GMAIL_APP_KEY = server_secure_config["GMAIL_APP_KEY"]