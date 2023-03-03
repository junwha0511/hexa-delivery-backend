from flask import Flask, jsonify, request 
from flask_api import status
# from flask_jwt_extended import JWTManager
import sqlite3
import smtplib
from email.mime.text import MIMEText
from random import randrange
from datetime import datetime, timedelta
import re
import bcrypt
import jwt
import dotenv
from dotenv import dotenv_values

DATABASE = "test.db"
connect = sqlite3.connect(DATABASE, isolation_level=None)
cursor = connect.cursor()

server_secure_config = dotenv_values(".env") 

# User info 테이블 생성
cursor.execute("CREATE TABLE IF NOT EXISTS user \
    (uid integer PRIMARY KEY, name text, email_address, auth_time DATETIME DEFAULT CURRENT_TIMESTAMP)")

# User auth 테이블 생성 (uid 근원)
cursor.execute("CREATE TABLE IF NOT EXISTS user_auth \
    (uid integer PRIMARY KEY, exp_time DATETIME NOT NULL, auth_number text NOT NULL, verified text, \
        FOREIGN KEY(uid) REFERENCES user(uid))")

# restaurant info 테이블 생성
cursor.execute("CREATE TABLE IF NOT EXISTS restaurant \
    (rid integer PRIMARY KEY, name text NOT NULL, location text NOT NULL, category text NOT NULL, fee integer NOT NULL, menu_link text)")

# Order info 테이블 생성
cursor.execute("CREATE TABLE IF NOT EXISTS order_info \
    (oid integer PRIMARY KEY, exp_time DATETIME NOT NULL, meeting_place text NOT NULL, group_link text NOT NULL, rid integer, member_num integer NOT NULL, uid integer, \
        FOREIGN KEY (rid) REFERENCES restaurant(rid), FOREIGN KEY (uid) REFERENCES user(uid) )")

# User - Order테이블 생성
cursor.execute("CREATE TABLE IF NOT EXISTS user_order_relationship \
    (uid integer, oid integer, PRIMARY KEY (uid, oid), \
        FOREIGN KEY (uid) REFERENCES restaurant(uid), FOREIGN KEY (oid) REFERENCES restaurant(oid) )")


ORDERDAO_REQUIRED_PARAMETERS = ("exp_time", "meeting_place", "group_link", "rid", "member_num", "uid")
ORDER_CATEGORY = ('치킨', '피자', '양식', '한식', '중식', '일식', '분식', '야식', '간식')

RES_STATUS_KEY = "status"
RES_DATA_KEY = "data"
RES_ERROR_MESSAGE = "error_message"

SECURE_CONFIG_JWT_FIELD = "jwt_secret_key"
SECURE_CONFIG_ENCRYPTED_FIELD = "encrypted_key"
JWT_SECRET_KEY = server_secure_config[SECURE_CONFIG_JWT_FIELD]
ENCRYPTED_KEY = server_secure_config[SECURE_CONFIG_ENCRYPTED_FIELD]

class OrderDAO():
    def __init__(self, oid, exp_time, meeting_place, group_link, rid, member_num, uid):
        self.oid = oid
        self.exp_time = exp_time
        self.meeting_place = meeting_place
        self.group_link = group_link
        self.rid = rid
        self.member_num = member_num
        self.uid = uid

    def to_json(self):
        res = {}
        res["oid"] = self.oid
        res["exp_time"] = self.exp_time
        res["meeting_place"] = self.meeting_place
        res["group_link"] = self.group_link
        res["rid"] = self.rid
        res["member_num"] = self.member_num
        res["uid"] = self.uid
        return res

# order 간략 정보 DTO (게시판 전용)
class OrderBreifDTO():
    def __init__(self, oid, name, category, exp_time, member_num, fee):
        self.oid = oid
        self.name = name
        self.category = category
        self.exp_time = exp_time
        self.member_num = member_num
        self.fee = fee    

    def to_json(self):
        res = {}
        res["oid"] = self.oid
        res["name"] = self.name
        res["category"] = self.category
        res["exp_time"] = self.exp_time
        res["member_num"] = self.member_num      
        res["fee"] = self.fee

        return res

# order 상세 정보 DTO
class OrderDetailDTO():
    def __init__(self, oid, name, exp_time, location, member_num, category, fee, menu_link, group_link):
        self.oid = oid
        self.name = name
        self.exp_time = exp_time
        self.location = location
        self.member_num = member_num
        self.category = category
        self.fee = fee
        self.menu_link = menu_link
        self.group_link = group_link          

    def to_json(self):
        res = {}
        res["oid"] = self.oid
        res["name"] = self.name
        res["exp_time"] = self.exp_time
        res["location"] = self.location
        res["member_num"] = self.member_num
        res["category"] = self.category
        res["fee"] = self.fee
        res["menu_link"] = self.menu_link
        res["group_link"] = self.group_link

        return res

class userDTO():
    def __init__(self, uid, name, email_address):
        self.uid = uid
        self.name = name
        self.email_address = email_address
    
    def to_json(self):
        res = {}
        res["uid"] = self.uid
        res["name"] = self.name
        res["email_address"] = self.email_address
        
        return res

# json에 key가 존재하는지 확인
def json_has_key(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True

def verify_jwt_token(token, uid, auth_number):
    # Extract Password from JWT Token
    password = jwt.decode(token, JWT_SECRET_KEY, algorithms="HS256")["password"].encode("utf-8")

    # Hash UID and Auth number again (bcrypt)
    # hash_uid_authnum = bcrypt.hashpw((uid + auth_number).encode("utf-8"), ENCRYPTED_KEY).decode("utf-8")

    # Compare two strings and return the result
    checkPw = bcrypt.checkpw(password, (uid+auth_number).encode("utf-8"))
    if(checkPw):
        return True
    
    return False

app = Flask(__name__)


# 메인 페이지
'''
상위 3개 LIMIT으로 일부 정보만 SELECT
'''

# 마이 페이지 - 주문 리스트
@app.route("/mypage/list", methods=['GET'])
def my_page_list():
    req = request.args.to_dict()

    # 필수 parameter 확인: uid 
    if "uid" not in req:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "not exist required parameter: uid"
        return jsonify(res)

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # uid와 연결된 oid 기반으로 order SELECT
    # todo: implement this part.

    connect.commit()

    # OrderBreifDTO 인스턴스 리스트 생성
    order_list = cursor.fetchall()
    order_list = [OrderBreifDTO(*tuple).to_json() for tuple in order_list]

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = order_list

    return jsonify(res)


# 로그인 - 인증번호 전송
@app.route("/login/send_auth_number", methods=['POST'])
def login_send_auth_number():
    req = request.args.to_dict()

    # 필수 parameter 확인: email_address 
    if "email_address" not in req:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "not exist required parameter: email_address"
        return jsonify(res)

    # email validation 실시. 이메일 형식을 따르며, 반드시 unist.ac.kr 이메일 이어야 함.
    email_validation = re.compile('^[a-zA-Z0-9+-\_.]+@unist.ac.kr')
    if not email_validation.match(req['email_address']):
        return {RES_STATUS_KEY: status.HTTP_400_BAD_REQUEST, RES_ERROR_MESSAGE: 'email validation error'}, status.HTTP_400_BAD_REQUEST

    # 인증번호 생성 및 email 발송
    smtp = smtplib.SMTP('smtp.naver.com', 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login('hexa_delivery@naver.com', 'HeXA.pro*')

    auth_number = randrange(10000)
    msg = MIMEText('{}'.format(auth_number))
    msg['From'] = 'hexa_delivery@naver.com'
    msg['Subject'] = '테스트'
    msg['To'] = req['email_address']
    smtp.sendmail('hexa_delivery@naver.com', '{}'.format(req['email_address']), msg.as_string())
    smtp.quit()

    # 만료시간은 현재시간 + 5분
    exp_time = datetime.now() + timedelta(minutes=5)

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # 이미 존재하는 유저인지 확인 (email_address 기반으로)
    req_email_address = req["email_address"]
    cursor.execute('SELECT uid, email_address FROM user WHERE email_address = "{}"'.format(req_email_address))
    user = cursor.fetchall()
    uid = -1

    # 새로운 유저일 경우 새 uid 생성 후 DB에 insert
    if(len(user) == 0):
        cursor.execute("SELECT * FROM user")
        uid = len(cursor.fetchall()) + 1
        cursor.execute("INSERT INTO user_auth(uid, exp_time, auth_number, verified) VALUES(?, ?, ?, ?)", (uid, exp_time, auth_number, 'FALSE'))
    else: # 기존 유저일 경우 기존 uid 선택 후 DB update
        uid = user[0][0]  
        cursor.execute("UPDATE user_auth SET exp_time='{}', auth_number='{}', verified='{}' WHERE uid='{}'".format(exp_time, auth_number, 'FALSE', uid))
    
    connect.commit()
    
    # RETURN UID, EXP_TIME
    return {RES_STATUS_KEY: status.HTTP_201_CREATED, RES_DATA_KEY: {"uid": uid, "exp_time": exp_time}}, status.HTTP_201_CREATED

# 로그인 - 인증번호 확인
@app.route("/login/verify_auth_number", methods=['POST'])
def verify_auth_number():
    req = request.args.to_dict()

    # 필수 parameter 확인: uid, email_address, auth_number
    auth_required_parameter = ("uid", "auth_number")
    for param in auth_required_parameter:
        if not json_has_key(req, param):
            res = {}
            res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
            res[RES_ERROR_MESSAGE] = "not exist required parameter: " + param
            return jsonify(res)

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()
    
    # DB에서 인증번호 유효성 확인
    cursor.execute('SELECT uid, auth_number, exp_time FROM user_auth WHERE uid ="{}"'.format(req["uid"]))
    user_auth_list = cursor.fetchall()

    # 존재하지 않는 uid
    if len(user_auth_list) == 0:
        return {RES_STATUS_KEY: status.HTTP_403_FORBIDDEN, RES_ERROR_MESSAGE: "not exist uid"}, status.HTTP_403_FORBIDDEN
    uid, auth_number, exp_time = user_auth_list[0]

    # 잘못된 인증번호
    if(auth_number != req["auth_number"]):
        return {RES_STATUS_KEY: status.HTTP_417_EXPECTATION_FAILED, RES_ERROR_MESSAGE: "wrong authentication number"}, status.HTTP_417_EXPECTATION_FAILED

    # 인증시간이 만료됨
    if(datetime.strptime(exp_time, '%Y-%m-%d %H:%M:%S.%f') < datetime.now()):
        return {RES_STATUS_KEY: status.HTTP_410_GONE, RES_ERROR_MESSAGE: "expired authentication number."}, status.HTTP_410_GONE

    # 이제 유저 인증이 성공했음을 확신할 수 있다.
    # verified 업데이트
    cursor.execute('UPDATE user_auth SET verified={} WHERE uid="{}"'.format("TRUE", uid))

    # DB에 유저 정보 저장
    cursor.execute('SELECT * FROM user WHERE uid={}'.format(uid))
    u = cursor.fetchall()

    # 새로운 유저
    if(len(u)==0): 
        cursor.execute("INSERT INTO user(uid, auth_time) VALUES(?, ?)", (uid, datetime.now() + timedelta(days=90)))
    else: # 이미 존재하는 유저
        cursor.execute('UPDATE user SET auth_time="{}" WHERE uid="{}"'.format(datetime.now() + timedelta(days=90), uid))

    connect.commit()

    # 유저 정보로 bcrypt -> hash 값 기반으로 JWT token 발행
    encrypted_password = bcrypt.hashpw((str(uid) + str(auth_number)).encode("utf-8"), bcrypt.gensalt()).decode("utf-8") # str 객체, bytes로 인코드, salt를 이용하여 암호화
    password_json = {
    "password": encrypted_password,
    }
    jwt_token = jwt.encode(password_json, JWT_SECRET_KEY, algorithm="HS256")

    # RETURN UID, JWT
    return {RES_STATUS_KEY: status.HTTP_201_CREATED, RES_DATA_KEY: {"uid": uid, "access_token": jwt_token}}, status.HTTP_201_CREATED

# 유저 정보 확인
# null인지 확인해서 수정 요청 status 412
@app.route("/user/info", methods=['GET'])
def user_info():
    req_header = request.headers
    req_body = request.args.to_dict()

    # 필수 parameter 확인
    if 'access_token' not in req_header:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "not exist header: access_token"
        return jsonify(res)
    if 'uid' not in req_body:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "not exist required parameter: uid"
        return jsonify(res)

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # jwt 토큰 유효성 확인
    cursor.execute("SELECT auth_number FROM user_auth WHERE uid='{}'".format(req_body["uid"]))
    auth_num = cursor.fetchall()[0][0]
    isVerifed = verify_jwt_token(req_header["access_token"], req_body["uid"], auth_num)

    if (~isVerifed):
        return {RES_STATUS_KEY: status.HTTP_401_UNAUTHORIZED, RES_ERROR_MESSAGE: "unauthorized jwt token"}, status.HTTP_401_UNAUTHORIZED

    # 유저 정보 SELECT
    cursor.execute("SELECT uid, name, email_address FROM user WHERE uid='{}'".format(req_body["uid"]))
    connect.commit()

    u = cursor.fetchall()

    # 존재하지 않는 uid
    if(len(u) == 0):
        return {RES_STATUS_KEY: status.HTTP_404_NOT_FOUND, RES_ERROR_MESSAGE: "not exist uid"}, status.HTTP_404_NOT_FOUND

    # userDTO 인스턴스 생성
    user = userDTO(u[0])

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = user.to_json()
    return jsonify(res)


# 유저 정보 업데이트
@app.route("/user/update", methods=['POST'])
def user_update():
    req_header = request.headers
    req_body = request.args.to_dict()

    # 필수 parameter 확인
    if 'jwt_token' not in request.req_header:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "not exist header: jwt_token"
        return jsonify(res)
    
    user_update_required_parameters = ("uid", "name", "email_address")
    for param in user_update_required_parameters:
        if not json_has_key(req, param):
            res = {}
            res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
            res[RES_ERROR_MESSAGE] = "not exist required parameter: " + param
            return jsonify(res)
    
    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # jwt 토큰 유효성 확인
    cursor.execute("SELECT auth_number FROM user_auth WHERE uid='{}'".format(req_body["uid"]))
    auth_num = cursor.fetchall()[0]
    isVerifed = verify_jwt_token(req_header["jwt_token"], req_body["uid"], auth_num)

    if (~isVerifed):
        return {RES_STATUS_KEY: status.HTTP_401_UNAUTHORIZED, RES_ERROR_MESSAGE: "unauthorized jwt token"}, status.HTTP_401_UNAUTHORIZED

    # 존재하지 않는 uid 케이스 처리
    cursor.execute("SELECT * FROM user WHERE uid='{}'".format(req_body["uid"]))
    uid_check = cursor.fetchall()
    if(len(uid_check) == 0):
        return {RES_STATUS_KEY: status.HTTP_404_NOT_FOUND, RES_ERROR_MESSAGE: "not exist uid"}, status.HTTP_404_NOT_FOUND

    # 유저 정보 UPDATE
    cursor.execute("UPDATE user SET name='{}', email_address='{}' WHERE uid='{}'".format(req_body["name"], req_body["email_address"] ,req_body["uid"]))
    connect.commit()

    u = cursor.fetchall()

    # userDTO 인스턴스 생성
    user = userDTO(u[0])

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    res[RES_DATA_KEY] = user.to_json()
    return jsonify(res)

# 자동로그인 확인
'''
TODO(KOO-DH): 
    - jwt token을 헤더로 받음
    https://stackoverflow.com/questions/33265812/best-http-authorization-header-type-for-jwt
    - jwt token이 오늘 유효한지 확인 (오늘 내 만료일 경우 갱신 필요하다는 문구 FORBIDDEN)
    - 모두 유효할 경우 200 OK  
'''

# 게시판 페이지
@app.route("/board/list", methods=['GET'])
def board_list():
    req = request.args.to_dict()

    # 필수 parameter 확인
    if "category" not in req:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "not exist required parameter: category"
        return jsonify(res)
    if not req["category"] in ORDER_CATEGORY:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "User sended a category which doesn't exist: " + req["category"]
        return jsonify(res)

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # 카테고리에 속한 order 10개 select
    cursor.execute("SELECT o.oid, r.name, r.category, o.exp_time, o.member_num, r.fee FROM order_info AS o INNER JOIN restaurant AS r ON o.rid=r.rid \
                   WHERE r.category='{}' LIMIT 10".format(req_category["category"]))

    connect.commit()

    # OrderBreifDTO 인스턴스 리스트 생성
    order_list = cursor.fetchall()
    order_list = [OrderBreifDTO(*tuple).to_json() for tuple in order_list]

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = order_list

    return jsonify(res)


# 모임 생성 페이지
@app.route("/order/create", methods=['POST'])
def order_create():
    req = request.form

    # 필수 parameter 확인
    for param in ORDERDAO_REQUIRED_PARAMETERS:
        if not json_has_key(req, param):
            res = {}
            res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
            res[RES_ERROR_MESSAGE] = "not exist required parameter: " + param
            return jsonify(res)

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # OrderDAO 인스턴스 생성
    cursor.execute("SELECT * FROM order_info")
    oid = len(cursor.fetchall()) + 1
    param_data = [req[param_name] for param_name in ORDERDAO_REQUIRED_PARAMETERS]
    new_order = OrderDAO(oid, *param_data)
    
    # INSERT to order_info 테이블
    cursor.execute("INSERT INTO order_info(oid, exp_time, meeting_place, group_link, rid, member_num, uid) VALUES(?,?,?,?,?,?,?)",
                   (new_order.oid, new_order.exp_time, new_order.meeting_place, new_order.group_link, new_order.rid, new_order.member_num, new_order.uid))
    # INSERT to user_order_relationship 테이블               
    cursor.execute("INSERT INTO user_order_relationship(uid, oid) VALUES(?, ?)", (new_order.uid, new_order.oid))
    
    connect.commit()

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    res[RES_DATA_KEY] = new_order.to_json()
    return jsonify(res)


# 모임 상세 페이지
@app.route("/order/detail", methods=['GET'])
def order_detail():
    req = request.args.to_dict()

    # 필수 parameter 확인
    if "oid" not in req:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "not exist required parameter: oid"
        return jsonify(res)

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # DB에서 oid 기반으로 order 정보 select
    cursor.execute("SELECT o.oid, r.name, o.exp_time, r.location, o.member_num, r.category, r.fee, r.menu_link, o.group_link \
                    FROM order_info AS o INNER JOIN restaurant AS r ON o.rid=r.rid WHERE o.oid='{}' LIMIT 10".format(req["oid"]))
    connect.commit()

    o = cursor.fetchall()

    # 존재하지 않는 oid
    if(len(o) == 0):
        return {RES_STATUS_KEY: status.HTTP_400_BAD_REQUEST, RES_ERROR_MESSAGE: "not exist oid"}, status.HTTP_400_BAD_REQUEST

    # OrderDetailDTO 인스턴스 생성
    order = OrderDetailDTO(o[0])

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = order.to_json()
    return jsonify(res)
