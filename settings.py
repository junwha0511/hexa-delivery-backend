
from dotenv import dotenv_values
import bcrypt

server_secure_config = dotenv_values("/keys/.env") 

DATABASE = "/server/test.db"

ORDER_DAO_REQUIRED_PARAMETERS = ("oid", "exp_time", "fee", "location", "group_link", "rid", "uid")
RESTAURANT_DAO_REQUIRED_PARAMETERS = ("rid", "name", "category", "creator")
ORDER_CATEGORY = ('치킨', '피자', '양식', '한식', '중식', '일식', '분식', '야식', '간식')

RES_STATUS_KEY = "status"
RES_DATA_KEY = "data"
RES_ERROR_MESSAGE = "error_message"

HEADER_ACCESS_TOKEN = "Access-Token"

JWT_SECRET_KEY = server_secure_config["JWT_SECRET_KEY"]
# BCRYPT_SALT = server_secure_config["BCRYPT_SALT"] # bcrypt.gensalt()
EMAIL_APP_KEY = server_secure_config["EMAIL_APP_KEY"]

DATETIME_FORMAT_STRING = '%m/%d/%Y'
TOKEN_EXP_CYCLE = 90

BOARD_LIMIT = 10
