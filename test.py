from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from flask_api import status
from settings import RES_DATA_KEY, RES_STATUS_KEY, RES_ERROR_MESSAGE

test_bp = Blueprint("test", __name__, url_prefix="/test")


@test_bp.route("/login/login", methods=["GET"])
def login_login():
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_400_BAD_REQUEST
    return res, status.HTTP_400_BAD_REQUEST


@test_bp.route("/login/send_auth_number", methods=["POST"])
def send_auth_number():
    exp_time = datetime.now() + timedelta(minutes=5)
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    res[RES_DATA_KEY] = {"exp_time": exp_time, "uid": 10000}

    return jsonify(res), status.HTTP_201_CREATED


@test_bp.route("/login/verify_auth_number", methods=["POST"])
def verify_auth_number():
    req = request.form
    if req["auth_number"] == "0000":
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_201_CREATED
        res[RES_DATA_KEY] = {"Access-Token": "12345", "uid": 10000}
        return jsonify(res), status.HTTP_201_CREATED
    else:
        res = {}
        res[RES_STATUS_KEY] = status.HTTP_417_EXPECTATION_FAILED
        res[RES_ERROR_MESSAGE] = "wrong authentication number"
        return jsonify(res), status.HTTP_417_EXPECTATION_FAILED


@test_bp.route("/user/info", methods=["GET"])
def user_info():
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = {"email_address": "delivery@test.com", "name": "test", "uid": 10000}
    return jsonify(res), status.HTTP_200_OK


@test_bp.route("/user/list", methods=["GET"])
def user_list():
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = {"data": []}
    return jsonify(res), status.HTTP_200_OK


@test_bp.route("/order/list", methods=["GET"])
def order_list():
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = [
        {"category": "치킨", "exp_time": "2024-11-15T23:14:00.000", "fee": 100, "name": "치킨집", "oid": 20},
        {"category": "치킨", "exp_time": "2023-11-15T23:14:00.000", "fee": 100, "name": "치킨집", "oid": 20},
        {"category": "치킨", "exp_time": "2023-11-15T23:14:00.000", "fee": 100, "name": "치킨집", "oid": 20},
    ]
    return jsonify(res), status.HTTP_200_OK


@test_bp.route("/order/create", methods=["POST"])
def order_create():
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_201_CREATED
    return res, status.HTTP_201_CREATED


@test_bp.route("/order/detail")
def order_detail():
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = {"category": "치킨", "exp_time": "2023-11-15T23:14:00.000", "fee": 100, "group_link": "https://www.baemin.com/order/group?groupOrderKey=Z3JvdXAtb3JkZXI6djE6Y29udGV4dDphNjc3ZTgwZWU5NzM0MTQyOTkxY2VkYjE1OWQxM2E0NQ==&shopNo=14309961", "location": "as", "name": "치킨집", "oid": 20}
    return jsonify(res), status.HTTP_200_OK


@test_bp.route("/order/top_list", methods=["GET"])
def order_top_list():
    res = {}
    res[RES_STATUS_KEY] = status.HTTP_200_OK
    res[RES_DATA_KEY] = [
        {"exp_time": "2023-11-15T23:14:00.000", "name": "치킨집", "oid": 20},
        {"exp_time": "2023-11-15T23:14:00.000", "name": "치킨집", "oid": 20},
        {"exp_time": "2023-11-15T23:14:00.000", "name": "치킨집", "oid": 20},
    ]
    return jsonify(res), status.HTTP_200_OK
