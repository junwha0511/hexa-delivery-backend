from flask import Flask, jsonify, request

ORDER_FIELD_OID = "oid"
ORDER_REQUIRED_PARAMETERS = ("name", "exp_time", "fee", "location", "group_link", "category")
ORDER_CATEGORY = ('치킨', '피자', '양식', '한식', '중식', '일식', '분식', '야식', '간식')

RES_STATUS_KEY = "status"
RES_DATA_KEY = "data"
RES_ERROR_MESSAGE = "message"

STATUS_REQUEST_SUCCESS = 200
STATUS_CREATE_SUCCESS = 201
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404



class Order():
    def __init__(self, oid, name, exp_time, fee, location, group_link, category):
        self.oid = oid
        self.name = name
        self.exp_time = exp_time
        self.fee = fee
        self.location = location
        self.group_link = group_link
        self.category = category

    def get_data_from_order(self):
        res = {}
        res["oid"] = self.oid
        res["name"] = self.name
        res["exp_time"] = self.exp_time
        res["fee"] = self.fee
        res["location"] = self.location
        res["group_link"] = self.group_link
        res["category"] = self.category
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
app.order_count = 0
app.orders = {}


# 메인 페이지 



## todo: 유저 생성(회원가입) 관련 api 설계하지 않음.
# 마이 페이지

## todo: 유저 생성(회원가입) 관련 api 설계하지 않음.
# 로그인 페이지


## todo: 어떤 게시판인지(치킨, 피자 등) parameter로 넘겨줘야 함
# 게시판 페이지
@app.route("/board/list", methods=['GET'])
def board_list():
    req_category = request.args.to_dict()
    if not "category" in req_category:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "Not exist required parameter: category"
        return jsonify(res)
    
    if not req_category["category"] in ORDER_CATEGORY:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "User sended a category which doesn't exist: " + req_category["category"]
        return jsonify(res)

    board = []
    for i in app.orders:
        if app.orders[i].category == req_category["category"]: 
            board.append(app.orders[i].get_data_from_order())

    res = {}
    res[RES_STATUS_KEY] = STATUS_REQUEST_SUCCESS
    res[RES_DATA_KEY] = board
    return jsonify(res)
    

# 모임 생성 페이지
@app.route("/order/create", methods=['POST'])
def order_create():
    req = request.form
    for param in ORDER_REQUIRED_PARAMETERS:
        ## todo: error message에 부족한 paramter가 2개 이상 일때 알려줄 수 없음. 수정필요
        if not json_has_key(req, param):
            res = {}
            res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
            res[RES_ERROR_MESSAGE] = "Not exist required parameter: " + param
            return jsonify(res)

    param_data = [req[param_name] for param_name in ORDER_REQUIRED_PARAMETERS]
    new_order = Order(app.order_count, *param_data)
    put_order(new_order)

    res = {}
    res[RES_STATUS_KEY] = STATUS_CREATE_SUCCESS
    res[RES_DATA_KEY] = new_order.get_data_from_order()
    
    return jsonify(res)


# 모임 상세 페이지
@app.route("/order/detail", methods=['GET'])
def order_detail():
    req_param = request.args.to_dict()
    if not "oid" in req_param:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "Not exist required parameter: oid"
        return jsonify(res)
    
    if int(req_param["oid"]) > (app.order_count-1) or int(req_param["oid"]) < 0:
        res = {}
        res[RES_STATUS_KEY] = STATUS_BAD_REQUEST
        res[RES_ERROR_MESSAGE] = "User sended an oid which doesn't exist: " + req_param["oid"]
        return jsonify(res)


    order = app.orders[int(req_param["oid"])]
    res = {}
    res[RES_STATUS_KEY] = STATUS_REQUEST_SUCCESS
    res[RES_DATA_KEY] = order.get_data_from_order()
    return jsonify(res)