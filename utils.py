from settings import *
import sqlite3
from flask_api import status
from flask import Flask, jsonify, request 
import bcrypt
import jwt
from datetime import datetime, timedelta

connect = sqlite3.connect(DATABASE, isolation_level=None)

def init_db():
    cursor = connect.cursor()

    # User info 테이블 생성
    cursor.execute("CREATE TABLE IF NOT EXISTS user \
        (uid integer PRIMARY KEY, name text, email_address text)")

    # User auth 테이블 생성 (uid 근원)
    cursor.execute("CREATE TABLE IF NOT EXISTS user_auth \
        (uid integer PRIMARY KEY, email_address text, exp_time DATETIME NOT NULL, auth_number text NOT NULL, auth_time DATETIME, verified text, \
            FOREIGN KEY(uid) REFERENCES user(uid))")

    # restaurant info 테이블 생성
    cursor.execute("CREATE TABLE IF NOT EXISTS restaurant \
        (rid integer PRIMARY KEY, name text NOT NULL, category text NOT NULL, menu_link text)")

    # Order info 테이블 생성
    cursor.execute("CREATE TABLE IF NOT EXISTS order_info \
        (oid integer PRIMARY KEY, exp_time DATETIME NOT NULL, fee integer NOT NULL, location text NOT NULL, group_link text NOT NULL, rid integer, member_num integer NOT NULL, uid integer, \
            FOREIGN KEY (rid) REFERENCES restaurant(rid), FOREIGN KEY (uid) REFERENCES user(uid) )")

    
# json에 key가 존재하는지 확인
def json_has_key(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True

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

def verify_jwt_token(token, uid, auth_number):
    # Extract Password from JWT Token
    password = jwt.decode(token, JWT_SECRET_KEY, algorithms="HS256")["password"]
    result = bcrypt.checkpw((str(uid)+str(auth_number)).encode("utf-8"), password.encode("utf-8"))
    
    if result:
        return True
    
    return False

def check_uid_exists(cursor, uid):
    # 유저 정보 SELECT
    cursor.execute("SELECT uid, name, email_address FROM user WHERE uid='{}'".format(uid))

    u = cursor.fetchall()

    # 존재하지 않는 uid
    if(len(u) == 0):
        return {RES_STATUS_KEY: status.HTTP_404_NOT_FOUND, RES_ERROR_MESSAGE: "uid not exists"}, status.HTTP_404_NOT_FOUND
    
    return None

# jwt 토큰 유효성 확인
def verify_access_token_with_user(cursor, token, uid):
    uid_check_result = check_uid_exists(cursor, uid)
    if uid_check_result != None:
        return uid_check_result
    
    # Assert that auth_number must have the row for uid
    cursor.execute("SELECT auth_number, auth_time FROM user_auth WHERE uid='{}'".format(uid))
    is_verified = False
    # try:
    auth_number, auth_time = cursor.fetchone()
    auth_time = datetime.strptime(auth_time, DATETIME_FORMAT_STRING)
    # Check if the token has been expired
    if (datetime.now() - auth_time) > timedelta(days=TOKEN_EXP_CYCLE):
        return {RES_STATUS_KEY: status.HTTP_410_GONE, RES_ERROR_MESSAGE: "access token expired"}, status.HTTP_410_GONE
    is_verified = verify_jwt_token(token, uid, auth_number)
    # except:
    #     is_verified = False
        
    if not is_verified:
        return {RES_STATUS_KEY: status.HTTP_401_UNAUTHORIZED, RES_ERROR_MESSAGE: "unauthorized access token"}, status.HTTP_401_UNAUTHORIZED
    
    return None

