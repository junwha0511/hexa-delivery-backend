from settings import *
import sqlite3
from flask_api import status
from flask import Flask, jsonify, request 

connect = sqlite3.connect(DATABASE, isolation_level=None)

def init_db():
    cursor = connect.cursor()

    # User info 테이블 생성
    cursor.execute("CREATE TABLE IF NOT EXISTS user \
        (uid integer PRIMARY KEY, name text, email_address text, auth_time DATETIME DEFAULT CURRENT_TIMESTAMP)")

    # User auth 테이블 생성 (uid 근원)
    cursor.execute("CREATE TABLE IF NOT EXISTS user_auth \
        (uid integer PRIMARY KEY, email_address text, exp_time DATETIME NOT NULL, auth_number text NOT NULL, verified text, \
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

# Verify parameters and return 400 and error message if some parameters were missing
def verify_parameters(req_params, actual_params, is_header=False):
    req_params = set(req_params)
    actual_params = set(actual_params)
    diff = req_params - actual_params
    if len(diff) > 0:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "required {} not exists: ".format("header" if is_header else "parameter") + ", ".join(diff) 
        return jsonify(res), status.HTTP_400_BAD_REQUEST
    
    return None