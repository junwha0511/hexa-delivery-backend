class OrderDAO():
    def __init__(self, oid, exp_time, fee, location, group_link, rid, uid):
        self.oid = oid
        self.exp_time = exp_time
        self.fee = fee
        self.location = location
        self.group_link = group_link
        self.rid = rid
        self.uid = uid

    def to_json(self):
        res = {}
        res["oid"] = self.oid
        res["exp_time"] = self.exp_time
        res["fee"] = self.fee
        res["location"] = self.location
        res["group_link"] = self.group_link
        res["rid"] = self.rid
        res["uid"] = self.uid
        return res

# order 간략 정보 DTO (메인 페이지)
class OrderBriefDTO():
    def __init__(self, oid, name, exp_time):
        self.oid = oid
        self.name = name
        self.exp_time = exp_time

    def to_json(self):
        res = {}
        res["oid"] = self.oid
        res["name"] = self.name
        res["exp_time"] = self.exp_time

        return res


# order 프리뷰 정보 DTO (게시판 전용)
class OrderPreviewDTO():
    def __init__(self, oid, name, category, exp_time, fee):
        self.oid = oid
        self.name = name
        self.category = category
        self.exp_time = exp_time
        self.fee = fee    

    def to_json(self):
        res = {}
        res["oid"] = self.oid
        res["name"] = self.name
        res["category"] = self.category
        res["exp_time"] = self.exp_time
        res["fee"] = self.fee

        return res

# order 상세 정보 DTO
class OrderDetailDTO():
    def __init__(self, oid, name, exp_time, location, category, fee, menu_link, group_link):
        self.oid = oid
        self.name = name
        self.exp_time = exp_time
        self.location = location
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
        res["category"] = self.category
        res["fee"] = self.fee
        res["menu_link"] = self.menu_link
        res["group_link"] = self.group_link

        return res

class UserDTO():
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

class RestaurantDTO:
    def __init__(self, rid, name):
        self.rid = rid
        self.name = name
    def to_json(self):
        res = {}
        res["rid"] = self.rid
        res["name"] = self.name
        
        return res