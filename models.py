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
