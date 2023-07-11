from flask import Flask, jsonify, request 
from flask_api import status
# from flask_jwt_extended import JWTManager
import smtplib
from email.mime.text import MIMEText
from random import randrange
from datetime import datetime, timedelta
import re
from settings import *
from utils import *
from models import *
import bcrypt
import jwt

app = Flask(__name__)

init_db()

# 로그인 - 인증번호 전송
@app.route("/login/send_auth_number", methods=['POST'])
def login_send_auth_number():
    req = request.form

    # 필수 parameter 확인: email_address 
    verify_result = verify_parameters(["email_address"], req.keys())
    if verify_result != None:
        return verify_result
    
    # email validation 실시. 이메일 형식을 따르며, 반드시 unist.ac.kr 이메일 이어야 함.
    email_validation = re.compile('^[a-zA-Z0-9+-\_.]+@.*')
    if not email_validation.match(req['email_address']):
        return {RES_STATUS_KEY: status.HTTP_400_BAD_REQUEST, RES_ERROR_MESSAGE: 'email validation error'}, status.HTTP_400_BAD_REQUEST

    # 인증번호 생성 및 email 발송
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login('hexa.delivery@gmail.com', GMAIL_APP_KEY)
    auth_number = randrange(1000, 10000)
    msg = MIMEText('인증번호: {}\n\n앱으로 돌아가 인증번호를 입력해주세요!'.format(auth_number))
    msg['From'] = 'hexa.delivery@gmail.com'
    msg['Subject'] = 'HeXA Delivery: 인증번호 확인'
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
    cursor.execute('SELECT uid, email_address FROM user_auth WHERE email_address="{}"'.format(req_email_address))
    user = cursor.fetchall()
    uid = -1

    # 새로운 유저일 경우 새 uid 생성 후 DB에 insert
    if(len(user) == 0):
        cursor.execute("SELECT max(uid) FROM user_auth")
        max_num = cursor.fetchall()
        print(max_num)
        uid = -1
        if len(max_num) != 1 or max_num[0][0] == None:
            uid = 0
        else: 
            uid = max_num[0][0] + 1
            print(uid)
        cursor.execute("INSERT INTO user_auth(uid, email_address, exp_time, auth_number, verified) VALUES(?, ?, ?, ?, ?)", (uid, req_email_address, exp_time, auth_number, 'FALSE'))
    else: # 기존 유저일 경우 기존 uid 선택 후 DB update
        uid = user[0][0]  
        cursor.execute("UPDATE user_auth SET exp_time='{}', auth_number='{}', verified='{}' WHERE uid='{}'".format(exp_time, auth_number, 'FALSE', uid))
    
    connect.commit()
    
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    res[RES_DATA_KEY] = {"uid": uid, "exp_time": exp_time}
    return jsonify(res), status.HTTP_201_CREATED

# 로그인 - 인증번호 확인
@app.route("/login/verify_auth_number", methods=['POST'])
def verify_auth_number():
    req = request.form

    # 필수 parameter 확인: uid, email_address, auth_number
    auth_required_parameter = ("uid", "auth_number")
    verify_result = verify_parameters(auth_required_parameter, req.keys())
    if verify_result != None:
        return verify_result
    
    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()
    
    # DB에서 인증번호 유효성 확인
    cursor.execute('SELECT uid, auth_number, exp_time FROM user_auth WHERE uid ="{}"'.format(req["uid"]))
    user_auth_list = cursor.fetchall()

    # 존재하지 않는 uid
    if len(user_auth_list) == 0:
        return {RES_STATUS_KEY: status.HTTP_403_FORBIDDEN, RES_ERROR_MESSAGE: "uid not exists"}, status.HTTP_403_FORBIDDEN
    
    uid, auth_number, exp_time = user_auth_list[0]

    # 잘못된 인증번호
    if(auth_number != req["auth_number"]):
        return {RES_STATUS_KEY: status.HTTP_417_EXPECTATION_FAILED, RES_ERROR_MESSAGE: "wrong authentication number"}, status.HTTP_417_EXPECTATION_FAILED
    
    # 인증시간이 만료됨
    if(datetime.strptime(exp_time, '%Y-%m-%d %H:%M:%S.%f') < datetime.now()):
        return {RES_STATUS_KEY: status.HTTP_410_GONE, RES_ERROR_MESSAGE: "expired authentication number."}, status.HTTP_410_GONE
    
    # 유저 정보로 password 생성 + 테이블 업데이트
    encrypted_password = bcrypt.hashpw((str(uid) + str(auth_number)).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cursor.execute("UPDATE user_auth SET verified='{}' WHERE uid={}".format("TRUE", uid))

    # DB에 유저 정보 저장
    cursor.execute('SELECT * FROM user WHERE uid={}'.format(uid))
    u = cursor.fetchall()

    # 새로운 유저
    if(len(u)==0):
        cursor.execute("INSERT INTO user(uid) VALUES (?)", (uid,))
    cursor.execute('UPDATE user_auth SET auth_time="{}" WHERE uid="{}"'.format(datetime.now().strftime(DATETIME_FORMAT_STRING), uid))
    
    connect.commit()

    # password를 포함하여 JWT token 발행
    password_json = {
    "password": encrypted_password,
    }
    jwt_token = jwt.encode(password_json, JWT_SECRET_KEY, algorithm="HS256")
    
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    res[RES_DATA_KEY] = {"uid": uid, HEADER_ACCESS_TOKEN: jwt_token}
    return jsonify(res), status.HTTP_201_CREATED

# 자동로그인 확인

'''
- jwt token을 헤더로 받음
- jwt token이 오늘 유효한지 확인 (오늘 내 만료일 경우 갱신 필요하다는 문구 GONE)
- 모두 유효할 경우 200 OK  
'''
@app.route("/login/login", methods=['GET'])
def login():
    req_param = request.args.to_dict()
    req_header = request.headers
    
    # 필수 parameter/header 확인
    header_verify_result = verify_parameters([HEADER_ACCESS_TOKEN], req_header.keys(), is_header=True)
    if header_verify_result != None:
        return header_verify_result
    param_verify_result = verify_parameters(["uid"], req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    # DB 연결   
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # Authentication
    verify_jwt_result = verify_access_token_with_user(cursor, req_header[HEADER_ACCESS_TOKEN], req_param["uid"])
    if verify_jwt_result != None:
        return verify_jwt_result
    
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = "ok"

    return res, status.HTTP_200_OK

# 유저 정보 확인
# null인지 확인해서 수정 요청 status 412
@app.route("/user/info", methods=['GET'])
def user_info():
    req_header = request.headers
    req_param = request.args.to_dict()

    # 필수 parameter/header 확인
    header_verify_result = verify_parameters([HEADER_ACCESS_TOKEN], req_header.keys(), is_header=True)
    if header_verify_result != None:
        return header_verify_result
    param_verify_result = verify_parameters(["uid"], req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    uid = req_param["uid"]
    
    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()
    
    # Authentication
    verify_jwt_result = verify_access_token_with_user(cursor, req_header[HEADER_ACCESS_TOKEN], uid)
    if verify_jwt_result != None:
        return verify_jwt_result

    cursor.execute("SELECT * FROM user WHERE uid={}".format(uid))
    u = cursor.fetchall()
    
    if len(u) == 0:
        return {RES_STATUS_KEY: status.HTTP_404_NOT_FOUND, RES_ERROR_MESSAGE: "user not exists"}, status.HTTP_404_NOT_FOUND
        
    # userDTO 인스턴스 생성
    user = UserDTO(*u[0])

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = user.to_json()
    return jsonify(res)


# 유저 정보 업데이트
@app.route("/user/update", methods=['POST'])
def user_update():
    req_header = request.headers
    req_param = request.form

    # 필수 parameter/headaer 확인
    header_verify_result = verify_parameters([HEADER_ACCESS_TOKEN], req_header.keys(), is_header=True)
    if header_verify_result != None:
        return header_verify_result
    user_update_required_parameters = ("uid", "name", "email_address")
    param_verify_result = verify_parameters(user_update_required_parameters, req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # jwt 토큰 유효성 확인
    verify_jwt_result = verify_access_token_with_user(cursor, req_header[HEADER_ACCESS_TOKEN], req_param["uid"])
    if verify_jwt_result != None:
        return verify_jwt_result
    
    # 유저 정보 UPDATE
    cursor.execute("UPDATE user SET name='{}', email_address='{}' WHERE uid='{}'".format(req_param["name"], req_param["email_address"] ,req_param["uid"]))
    connect.commit()

    # userDTO 인스턴스 생성
    user = UserDTO(req_param["uid"], req_param["name"], req_param["email_address"])

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    res[RES_DATA_KEY] = user.to_json()
    return jsonify(res)

# 유저 - 주문 리스트
@app.route("/user/list", methods=['GET'])
def my_page_list():
    req_param = request.args.to_dict()
    req_header = request.headers
    
    # 필수 parameter/header 확인
    header_verify_result = verify_parameters([HEADER_ACCESS_TOKEN], req_header.keys(), is_header=True)
    if header_verify_result != None:
        return header_verify_result
    param_verify_result = verify_parameters(["uid"], req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    # DB 연결   
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # Authentication
    verify_jwt_result = verify_access_token_with_user(cursor, req_header[HEADER_ACCESS_TOKEN], req_param["uid"])
    if verify_jwt_result != None:
        return verify_jwt_result
    
    # uid와 연결된 oid 기반으로 order SELECT
    cursor.execute("SELECT oid, name, category, exp_time, fee FROM order_info INNER JOIN restaurant WHERE uid='{}'".format(req_param["uid"]))
    
    # OrderBreifDTO 인스턴스 리스트 생성
    order_list = cursor.fetchall()
    order_list = [OrderPreviewDTO(*o).to_json() for o in order_list]

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = order_list

    return jsonify(res), status.HTTP_200_OK

'''
TODO(junwha): 테스트용 모임 dummy data 생성 스크립트 필요
TODO(junwha): 모임 마감 기준을 exp_time으로 잡고, 결과 필터링시 datetime.now()보다 앞선 것들만 조회
'''
# 메인 페이지
'''
상위 3개 LIMIT으로 일부 정보만 SELECT
'''
# 게시판 페이지
@app.route("/order/top_list", methods=['GET'])
def top_list():    
    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # order 3개 select
    cursor.execute("SELECT oid, name, exp_time FROM order_info INNER JOIN restaurant ON order_info.rid=restaurant.rid WHERE Datetime(exp_time)>'{}' ORDER BY exp_time LIMIT 3".format(datetime.now().isoformat()))
    
    # OrderBreifDTO 인스턴스 리스트 생성
    order_list = cursor.fetchall()
    order_list = [OrderBriefDTO(*o).to_json() for o in order_list]

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = order_list

    return jsonify(res), status.HTTP_200_OK

# 게시판 페이지
@app.route("/order/list", methods=['GET'])
def board_list():
    req_param = request.args.to_dict()

    # 필수 parameter 확인
    param_verify_result = verify_parameters(["category"], req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # 카테고리에 속한 order 10개 select
    cursor.execute("SELECT oid, name, category, exp_time, fee FROM order_info AS o INNER JOIN restaurant AS r ON o.rid=r.rid \
                   WHERE r.category='{}' AND Datetime(o.exp_time)>'{}' ORDER BY exp_time LIMIT 10".format(req_param["category"], datetime.now().isoformat()))

    # OrderBreifDTO 인스턴스 리스트 생성
    order_list = cursor.fetchall()
    order_list = [OrderPreviewDTO(*o).to_json() for o in order_list]

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = order_list

    return jsonify(res), status.HTTP_200_OK


# 모임 생성 페이지
@app.route("/order/create", methods=['POST'])
def order_create():
    req_param = request.form
    req_header = request.headers
    
    # 필수 parameter/header 확인
    header_verify_result = verify_parameters([HEADER_ACCESS_TOKEN], req_header.keys(), is_header=True)
    if header_verify_result != None:
        return header_verify_result
    required_params = list(ORDER_DAO_REQUIRED_PARAMETERS)
    required_params.remove("oid")
    param_verify_result = verify_parameters(required_params, req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    # DB 연결   
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # # Authentication
    verify_jwt_result = verify_access_token_with_user(cursor, req_header[HEADER_ACCESS_TOKEN], req_param["uid"])
    if verify_jwt_result != None:
        return verify_jwt_result
    
    # OrderDAO 인스턴스 생성
    cursor.execute("SELECT oid FROM order_info")
    oid = len(cursor.fetchall()) + 1
    param_data = [oid if param_name == "oid" else req_param[param_name] for param_name in ORDER_DAO_REQUIRED_PARAMETERS]
    new_order = OrderDAO(*param_data)
    
    # INSERT to order_info 테이블
    cursor.execute("INSERT INTO order_info({}) VALUES({})".format(",".join(ORDER_DAO_REQUIRED_PARAMETERS), ",".join(["?"]*len(ORDER_DAO_REQUIRED_PARAMETERS))),
                   param_data)
    connect.commit()

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    res[RES_DATA_KEY] = new_order.to_json()
    return jsonify(res), status.HTTP_201_CREATED


# 모임 상세 페이지
@app.route("/order/detail", methods=['GET'])
def order_detail():
    req = request.args.to_dict()

    # 필수 parameter 확인
    param_verify_result = verify_parameters("oid", req.keys())
    if param_verify_result != None:
        return param_verify_result

    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    # DB에서 oid 기반으로 order 정보 select
    cursor.execute("SELECT oid, name, exp_time, location, category, fee, menu_link, group_link \
                    FROM order_info AS o INNER JOIN restaurant AS r ON o.rid=r.rid WHERE o.oid='{}' LIMIT 10".format(req["oid"]))

    o = cursor.fetchall()

    # 존재하지 않는 oid
    if(len(o) == 0):
        return {RES_STATUS_KEY: status.HTTP_400_BAD_REQUEST, RES_ERROR_MESSAGE: "not exist oid"}, status.HTTP_400_BAD_REQUEST

    # OrderDetailDTO 인스턴스 생성
    order = OrderDetailDTO(*o[0])
    
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = order.to_json()
    return jsonify(res), status.HTTP_200_OK

'''
모임 마감
'''
# 모임 생성 페이지
@app.route("/order/close", methods=['POST'])
def order_close():
    req_param = request.form
    req_header = request.headers
    
    # 필수 parameter/header 확인
    header_verify_result = verify_parameters([HEADER_ACCESS_TOKEN], req_header.keys(), is_header=True)
    if header_verify_result != None:
        return header_verify_result
    param_verify_result = verify_parameters(["oid", "uid"], req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    # DB 연결   
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    oid = req_param["oid"]
    uid = req_param["uid"]
    
    # # Authentication
    verify_jwt_result = verify_access_token_with_user(cursor, req_header[HEADER_ACCESS_TOKEN], uid)
    if verify_jwt_result != None:
        return verify_jwt_result
    
    
    cursor.execute("SELECT oid, uid FROM order_info WHERE oid={}".format(oid))
    
    order_result = cursor.fetchall()
    
    if len(order_result) == 0:
        return {RES_STATUS_KEY: status.HTTP_404_NOT_FOUND, RES_ERROR_MESSAGE: "order not exists"}, status.HTTP_404_NOT_FOUND
    if str(order_result[0][1]) != str(uid):
        return {RES_STATUS_KEY: status.HTTP_401_UNAUTHORIZED, RES_ERROR_MESSAGE: "order was not created by this user"}, status.HTTP_401_UNAUTHORIZED
    
    # INSERT to order_info 테이블
    exp_time = datetime.now().isoformat()
    cursor.execute("UPDATE order_info SET exp_time='{}' WHERE oid={}".format(exp_time, oid))
    connect.commit()

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_202_ACCEPTED
    res[RES_DATA_KEY] = {"oid": oid, "closed_at": exp_time}
    return jsonify(res), status.HTTP_202_ACCEPTED

'''
가게 검색
'''
@app.route("/store/search", methods=['GET'])
def store_search():    
    req_param = request.args.to_dict()
    
    # DB 연결
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    param_verify_result = verify_parameters(["query"], req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    query = req_param["query"]
    
    # 10개 select
    cursor.execute("SELECT rid, name FROM restaurant WHERE name LIKE '%{}%' OR category LIKE '%{}%' LIMIT 10".format(query, query))
    print("SELECT rid, name FROM restaurant WHERE name LIKE '%{}%' OR category LIKE '%{}%' LIMIT 10".format(query, query))
    # RestaurantDTO 인스턴스 리스트 생성
    restaurant_list = cursor.fetchall()
    restaurant_list = [RestaurantDTO(*r).to_json() for r in restaurant_list]

    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = restaurant_list

    return jsonify(res), status.HTTP_200_OK

'''
가게 추가
'''
# 모임 생성 페이지
@app.route("/store/create", methods=['POST'])
def store_create():
    req_param = request.form
    req_header = request.headers
        
    # 필수 parameter/header 확인
    header_verify_result = verify_parameters([HEADER_ACCESS_TOKEN], req_header.keys(), is_header=True)
    if header_verify_result != None:
        return header_verify_result
    required_params = list(RESTAURANT_DAO_REQUIRED_PARAMETERS)
    required_params.remove("rid")
    param_verify_result = verify_parameters(required_params, req_param.keys())
    if param_verify_result != None:
        return param_verify_result
    
    # DB 연결   
    connect = sqlite3.connect(DATABASE, isolation_level=None)
    cursor = connect.cursor()

    cursor.execute("SELECT rid FROM restaurant")
    rid = len(cursor.fetchall()) + 1
    
    # Authentication
    verify_jwt_result = verify_access_token_with_user(cursor, req_header[HEADER_ACCESS_TOKEN], 0) # Only first user can create store (ADMIN)
    if verify_jwt_result != None:
        return verify_jwt_result
    
    # INSERT to order_info 테이블
    values = [rid if param=="rid" else req_param[param] for param in RESTAURANT_DAO_REQUIRED_PARAMETERS]
    
    result = True
    cursor.execute("INSERT INTO restaurant({}) VALUES({})".format(",".join(RESTAURANT_DAO_REQUIRED_PARAMETERS), ",".join(["?"]*len(RESTAURANT_DAO_REQUIRED_PARAMETERS))), values)
    connect.commit()
  
    res = {}
    if result:
        res[RES_STATUS_KEY] = status.HTTP_201_CREATED
        res[RES_DATA_KEY] = dict(zip(RESTAURANT_DAO_REQUIRED_PARAMETERS, values))
    else:
        res[RES_STATUS_KEY] = status.HTTP_406_NOT_ACCEPTABLE
        res[RES_ERROR_MESSAGE] = "DB couldn't work now"

    return jsonify(res), res[RES_STATUS_KEY]


if __name__ == "__main__":
    app.run(port=7777)
