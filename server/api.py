from flask import Flask, jsonify, request
from flask_api import status
# from flask_jwt_extended import JWTManager
import sqlite3
import smtplib
from email.mime.text import MIMEText
from random import randrange
from datetime import datetime, timedelta
import re

DATABASE = "test.db"
connect = sqlite3.connect(DATABASE, isolation_level=None)
cursor = connect.cursor()

# User info 테이블 생성
cursor.execute("CREATE TABLE IF NOT EXISTS user \
    (uid integer PRIMARY KEY, name text NOT NULL, email_address text NOT NULL, auth_time DATETIME DEFAULT CURRENT_TIMESTAMP)")

# User auth 테이블 생성
cursor.execute("CREATE TABLE IF NOT EXISTS user_auth \
    (uid integer PRIMARY KEY, exp_time DATETIME NOT NULL, auth_number text NOT NULL, \
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


ORDER_FIELD_OID = "oid"
ORDER_REQUIRED_PARAMETERS = ("exp_time", "meeting_place", "group_link", "rid", "member_num", "uid")
ORDER_CATEGORY = ('치킨', '피자', '양식', '한식', '중식', '일식', '분식', '야식', '간식')

RES_STATUS_KEY = "status"
RES_DATA_KEY = "data"
RES_ERROR_MESSAGE = "message"
RES_EXP_TIME = "exp_time"

STATUS_REQUEST_SUCCESS = 200
STATUS_CREATE_SUCCESS = 201
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404


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


class OrderDescDTO():
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


# json에 key가 존재하는지 확인
def json_has_key(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True


# app.orders에 새로운 order 삽입
def put_order(order):
    app.orders[app.order_count] = order
    app.order_count = app.order_count + 1


app = Flask(__name__)
# app.config.update(
#     DEBUG=True,
#     JWT_SECRET_KEY="HEXA_DELIVERY"
# )
# jwt = JWTManager(app)
app.order_count = 0
app.orders = {}


# 메인 페이지

# 마이 페이지

# 로그인 - 인증번호 전송
@app.route("/login/send_auth_number", methods=['POST'])
def login_send_auth_number():
    req = request.args.to_dict()

    if "email_address" not in req:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "Not exist required parameter: category"
        return jsonify(res)

    email_validation = re.compile('^[a-zA-Z0-9+-\_.]+@unist.ac.kr')
    if not email_validation.match(req['email_address']):
        return {RES_STATUS_KEY: status.HTTP_400_BAD_REQUEST, RES_ERROR_MESSAGE: 'email validation error'}, status.HTTP_400_BAD_REQUEST
    
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    req_email_address = req["email_address"]
    cursor.execute('SELECT uid, email_address FROM user WHERE email_address = "{}"'.format(req_email_address))
    email = cursor.fetchall()
    uid = -1

    # 새로운 유저 uid 생성
    if(len(email) == 0):
        cursor.execute("SELECT * FROM user")
        uid = len(cursor.fetchall()) + 1
    else:
        uid = email[0][0]  # 기존 uid 선택

    smtp = smtplib.SMTP('smtp.office365.com', 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login('hexa_delivery@outlook.kr', 'HeXA.pro*')

    auth_number = randrange(10000)
    msg = MIMEText('{}'.format(auth_number))
    msg['Subject'] = '테스트'
    msg['To'] = req_email_address
    smtp.sendmail('hexa_delivery@outlook.kr', '{}'.format(req_email_address), msg.as_string())
    smtp.quit()

    exp_time = datetime.now() + timedelta(minutes=5)
    cursor.execute("INSERT INTO user_auth(uid, exp_time, auth_number) VALUES(?, ?, ?)", (uid, exp_time, auth_number))

    return {RES_STATUS_KEY: status.HTTP_201_CREATED, RES_EXP_TIME: exp_time}, status.HTTP_201_CREATED

# 로그인 - 인증번호 확인

# 로그인 페이지


# 게시판 페이지
@app.route("/board/list", methods=['GET'])
def board_list():
    ### Validation ###
    req_category = request.args.to_dict()
    if "category" not in req_category:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "Not exist required parameter: category"
        return jsonify(res)
    if not req_category["category"] in ORDER_CATEGORY:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "User sended a category which doesn't exist: " + req_category["category"]
        return jsonify(res)

    ### Connect to DB ###
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    ### Main Logic ###
    cursor.execute("SELECT o.oid, r.name, r.category, o.exp_time, o.member_num, r.fee FROM order_info AS o INNER JOIN restaurant AS r ON o.rid=r.rid \
                   WHERE r.category='{}' LIMIT 10".format(req_category["category"]))
    order_list = cursor.fetchall()
    order_list = [OrderDescDTO(*tuple).to_json() for tuple in order_list]

    res = {}
    res[RES_STATUS_KEY] = STATUS_REQUEST_SUCCESS
    res[RES_DATA_KEY] = order_list

    return jsonify(res)


# 모임 생성 페이지
@app.route("/order/create", methods=['POST'])
def order_create():
    req = request.form
    for param in ORDER_REQUIRED_PARAMETERS:
        # todo: error message에 부족한 paramter가 2개 이상 일때 알려줄 수 없음. 수정필요
        if not json_has_key(req, param):
            res = {}
            res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
            res[RES_ERROR_MESSAGE] = "Not exist required parameter: " + param
            return jsonify(res)

    param_data = [req[param_name] for param_name in ORDER_REQUIRED_PARAMETERS]
    new_order = OrderDAO(app.order_count, *param_data)
    put_order(new_order)

    cursor.execute("INSERT INTO order_info(oid, exp_time, meeting_place, group_link, rid, member_num, uid) VALUES(?,?,?,?,?,?,?)",
                   (new_order.oid, new_order.exp_time, new_order.meeting_place, new_order.group_link, new_order.rid, new_order.member_num, new_order.uid))
    cursor.execute("INSERT INTO user_order_relationship(uid, oid) VALUES(?, ?)", (new_order.uid, new_order.oid))
    connect.commit()

    res = {}
    res[RES_STATUS_KEY] = STATUS_CREATE_SUCCESS
    res[RES_DATA_KEY] = new_order.to_json()
    return jsonify(res)


# 모임 상세 페이지
@app.route("/order/detail", methods=['GET'])
def order_detail():
    req_param = request.args.to_dict()
    if "oid" not in req_param:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "Not exist required parameter: oid"
        return jsonify(res)

    if int(req_param["oid"]) > (app.order_count - 1) or int(req_param["oid"]) < 0:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "User sended an oid which doesn't exist: " + req_param["oid"]
        return jsonify(res)

    order = app.orders[int(req_param["oid"])]
    res = {}
    res[RES_STATUS_KEY] = STATUS_REQUEST_SUCCESS
    res[RES_DATA_KEY] = order.to_json()
    return jsonify(res)
