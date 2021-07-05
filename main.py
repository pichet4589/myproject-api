import io
import pymysql
import base64
from flask import Flask, request, jsonify
from pytesseract import pytesseract
from PIL import Image
from app import app
from db_config import mysql
import jwt
from datetime import datetime, timedelta
from functools import wraps
import hashlib

@app.route('/',methods=['GET'])
def index():
     return "<h1>Welcome to Python Flask server !!</h1>"

@app.route('/ping')
def ping():
    return ping

EXP_TIME   = 3          
JWT_ALG    = 'HS256'        

def auth_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify(
                {
                    'message':'Token is missing'
                }
            ),403

        try:
            token = jwt.decode(
                auth_header,
                app.secret_key, 
                algorithms=[JWT_ALG]
            )
        except Exception as e:
            return jsonify(
                {
                    'message':'Token is invalid'
                }
            ),403
        
        return f(*args, **kwargs)
    return decorated
##############################################################################
# Login
@app.route('/login', methods=['POST'])
def login():
    
    credentials = request.get_json()   

    username = credentials['username']
    password = credentials['password']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "SELECT * FROM login WHERE username=%s"
    sql_where = (username,)
    cursor.execute(sql, sql_where)
    row = cursor.fetchone()
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    if username == username and row[2] == password_hash:
        auth_token = jwt.encode(
            {
                'username':username,
                'exp':datetime.utcnow()+timedelta(minutes=EXP_TIME)
            },
            app.secret_key,     
            JWT_ALG            
            )
        return jsonify(
                {
                 'message':'Authenticated',
                 'auth_token':auth_token,
                 'status':200
                }
            ),200
    else:
        return jsonify(
        {
         'message':'ชื่อผู้ใช้หรือรหัสผ่านผิด'
         }
    )

# ######## ตรวจสอบจดหมาย #########
@app.route('/check_letter', methods=['GET'])
# @auth_token_required
def check_letter():
        args = request.args
        _id = args['id']
        _username = args['name']
        try:
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            if _id and _username:
                name = _username.split()
                _name = list(name)
                if len(_name) > 1:
                    cursor.execute("SELECT  letter.id,letter.user_id,letter.date,user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_id,category.category_name,status_letter.status_id,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s AND  user.member_id LIKE %s   AND user.user_id = letter.user_id  AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id ORDER BY date DESC",
                               ("%" + _name[0] + "%", "%" + _name[1] + "%",  _id + "%"))
                else:
                    cursor.execute("SELECT  letter.id,letter.user_id,letter.date,user.member_id,user.user_fname,letter.export_name,user.user_lname,department.department_name,category.category_id,category.category_name,status_letter.status_id,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND  user.member_id LIKE %s AND user.user_id = letter.user_id  AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id ORDER BY date DESC",
                               ("%" + _name[0] + "%",  _id + "%"))
            elif _id:
                cursor.execute("SELECT  letter.id,letter.user_id,letter.date,user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_id,category.category_name,status_letter.status_id,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.member_id LIKE %s AND user.user_id = letter.user_id  AND user.user_id = letter.user_id AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id ORDER BY date DESC",
                               ( _id + "%"))
            elif _username:
                name = _username.split()
                _name = list(name)
                if len(_name) > 1:
                    cursor.execute("SELECT  letter.id,letter.user_id,letter.date,user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_id,category.category_name,status_letter.status_id,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s  AND user.user_id = letter.user_id AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id ORDER BY date DESC",
                               ("%" + _name[0] + "%", "%" + _name[1] + "%"))
                else:
                    cursor.execute("SELECT  letter.id,letter.user_id,letter.date,user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_id,category.category_name,status_letter.status_id,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND user.user_id = letter.user_id AND letter.status_id = status_letter.status_id AND user.department_id = department.department_id AND category.category_id = letter.category_id  ORDER BY date DESC",
                               ("%" + _name[0] + "%"))          
            else:
                cursor.execute("SELECT letter.id,letter.user_id,letter.date,user.member_id,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,letter.export_name,category.category_id,category.category_name,status_letter.status_id,status_letter.status_name FROM  user JOIN category JOIN department JOIN faculty JOIN letter JOIN prefix JOIN status_letter JOIN usertype WHERE faculty.faculty_id = department.faculty_id AND department.department_id = user.department_id AND user.user_id = letter.user_id  AND user.prefix_id = prefix.prefix_id AND user.usertype_id = usertype.usertype_id  AND letter.category_id = category.category_id AND letter.status_id = status_letter.status_id ORDER BY date DESC")
            if cursor.rowcount == 0:
                return res("data not found",None,404)
            rows = cursor.fetchall()
            return res("success",rows,200)
        finally:
            cursor.close()
            conn.close()


########## ค้นหาชื่อด้วยแป้นพิมพ์ #################
@app.route('/search_user', methods=['POST'])
# @auth_token_required
def search_user():
        if request.form:
            key = request.form["name"]
        try:
            conn = mysql.connect()
            name = list(key.split())
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            if len(name) > 1:
                cursor.execute("SELECT user_id,user.member_id,prefix.prefix_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_id,department.department_name,faculty.faculty_id,faculty.faculty_name,usertype.usertype_id,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE  user.user_fname LIKE %s AND user.user_lname LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id  AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
                               ("%" + name[0] + "%", "%" + name[1] + "%"))
            else:
                cursor.execute("SELECT user_id,user.member_id,prefix.prefix_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_id,department.department_name,faculty.faculty_id,faculty.faculty_name,usertype.usertype_id,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE  user.user_fname LIKE %s  AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id  AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
                               ("%" + name[0] + "%"))
            if cursor.rowcount == 0:
                return res("data not found",None,404)
            rows = cursor.fetchall()
            return res("success",rows,200)
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()
    
########################################
@app.route('/search_id', methods=['POST'])
def search_id():
        if request.form:
            _id = request.form["id"]
        try:
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT  user.user_id,user.member_id,user.user_fname,user.user_lname,department.department_id,department.department_name,faculty.faculty_id,faculty.faculty_name,prefix.prefix_id,prefix.prefix_name,usertype.usertype_id,usertype.userType_name FROM user JOIN department JOIN faculty JOIN prefix JOIN usertype WHERE USER.member_id LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id   AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
                            (_id + "%"))
            if cursor.rowcount == 0:
                return res("data not found",None,404)
            rows = cursor.fetchall()
            return res("success",rows,200)
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()

##################################################################
@app.route('/search_department', methods=['POST'])
def search_department():
        if request.form:
            _id = request.form["id"]
        try:
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT department.department_id,department.department_name FROM department JOIN faculty WHERE  faculty.faculty_id LIKE %s AND department.faculty_id = faculty.faculty_id",
                            ("%" + _id + "%"))
            if cursor.rowcount == 0:
                return res("data not found",None,404)
            rows = cursor.fetchall()
            return res("success",rows,200)
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()

##################################################################
@app.route('/letter', methods=['GET'])
def get_letter():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM letter")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
@app.route('/user', methods=['GET'])
def get_user():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM user")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
@app.route('/category', methods=['GET'])
def get_category():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM category")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        

@app.route('/status_letter', methods=['GET'])
def get_status_letter():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM status_letter")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@app.route('/department', methods=['GET'])
def get_department():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM department")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        

@app.route('/faculty', methods=['GET'])
def get_faculty():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM faculty")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
@app.route('/prefix', methods=['GET'])
def get_prefix():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM prefix")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
@app.route('/status', methods=['GET'])
def get_status():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM status")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
@app.route('/usertype', methods=['GET'])
def get_usertype():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM usertype")
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
###############################################################################################

@app.route('/add_letter', methods=['POST'])
def add_letter():
    try:
        _json = request.json
        _user = _json['user_id']
        _exportname = _json['export_name']
        _category = _json['category_id']
        _status = "2" 

        sql = "INSERT INTO `letter` (`id`, `user_id`, `export_name`, `category_id`, `status_id`) VALUES (NULL,%s, %s, %s, %s)"
        data = (_user,_exportname, _category, _status)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

        
@app.route('/update_letter', methods=['PUT'])
def update_letter():
    try:
        _json = request.json
        _id = _json['id']
        _userfname = _json['user_id']
        _exportname = _json['export_name']
        _category = _json['category_id']
        _statusname = _json['status_id']
        
        sql = "UPDATE letter SET user_id=%s, export_name=%s, category_id=%s, status_id=%s WHERE id=%s"
        data = ( _userfname, _exportname, _category, _statusname, _id)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

        
@app.route('/delete_letter/<string:id>', methods=['DELETE'])
def delete_letter(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM letter WHERE id=%s", (id,))
        conn.commit()
        return res("success",None,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

###############################################################################################

@app.route('/add_faculty', methods=['POST'])
def add_faculty():
    try:
        _json = request.json
        _id = _json['faculty_id']
        _name = _json['faculty_name']
            
        sql = "INSERT INTO `faculty` (`faculty_id`, `faculty_name`) VALUES (%s, %s)"
        data = (_id,_name)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
     
@app.route('/update_faculty', methods=['PUT'])
def update_faculty():
    try:
        _json = request.json
        _id = _json['faculty_id']
        _name = _json['faculty_name']
    
        sql = "UPDATE faculty SET faculty_name=%s WHERE faculty_id=%s"
        data = ( _name, _id)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
  
@app.route('/delete_faculty/<string:id>', methods=['DELETE'])
def delete_faculty(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM faculty WHERE faculty_id=%s", (id,))
        conn.commit()
        return res("success",None,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

###############################################################################################

@app.route('/add_prefix', methods=['POST'])
def add_prefix():
    try:
        _json = request.json
        _id = _json['prefix_id']
        _name = _json['prefix_name']
            
        sql = "INSERT INTO `prefix` (`prefix_id`, `prefix_name`) VALUES (%s, %s)"
        data = (_id,_name)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
     
@app.route('/update_prefix', methods=['PUT'])
def update_prefix():
    try:
        _json = request.json
        _id = _json['prefix_id']
        _name = _json['prefix_name']
    
        sql = "UPDATE prefix SET prefix_name=%s WHERE prefix_id=%s"
        data = ( _name, _id)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
  
@app.route('/delete_prefix/<string:id>', methods=['DELETE'])
def delete_prefix(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prefix WHERE prefix_id=%s", (id,))
        conn.commit()
        return res("success",None,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

###############################################################################################

@app.route('/add_category', methods=['POST'])
def add_category():
    try:
        _json = request.json
        _id = _json['category_id']
        _name = _json['category_name']
            
        sql = "INSERT INTO `category` (`category_id`, `category_name`) VALUES (%s, %s)"
        data = (_id,_name)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
     
@app.route('/update_category', methods=['PUT'])
def update_category():
    try:
        _json = request.json
        _id = _json['category_id']
        _name = _json['category_name']
    
        sql = "UPDATE category SET category_name=%s WHERE category_id=%s"
        data = ( _name, _id)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
  
@app.route('/delete_category/<string:id>', methods=['DELETE'])
def delete_category(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM category WHERE category_id=%s", (id,))
        conn.commit()
        return res("success",None,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

###############################################################################################

@app.route('/add_status', methods=['POST'])
def add_status():
    try:
        _json = request.json
        _id = _json['status_id']
        _name = _json['status_name']
            
        sql = "INSERT INTO `status_letter` (`status_id`, `status_name`) VALUES (%s, %s)"
        data = (_id,_name)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
     
@app.route('/update_status', methods=['PUT'])
def update_status():
    try:
        _json = request.json
        _id = _json['status_id']
        _name = _json['status_name']
    
        sql = "UPDATE status_letter SET status_name=%s WHERE status_id=%s"
        data = ( _name, _id)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
  
@app.route('/delete_status/<string:id>', methods=['DELETE'])
def delete_status(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM status_letter WHERE status_id=%s", (id,))
        conn.commit()
        return res("success",None,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

###############################################################################################

@app.route('/add_department', methods=['POST'])
def add_department(): 
    try:
        _json = request.json
        _id = _json['department_id']
        _name = _json['department_name']
        _faculty = _json['faculty_id']
            
        sql = "INSERT INTO `department` (`department_id`, `department_name`, `faculty_id`) VALUES (%s, %s, %s)"
        data = (_id,_name, _faculty)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
     
@app.route('/update_department', methods=['PUT'])
def update_department(): 
    try:
        _json = request.json
        _id = _json['department_id']
        _name = _json['department_name']
        _faculty = _json['faculty_id']
        
        sql = "UPDATE department SET department_name=%s, faculty_id=%s WHERE department_id=%s"
        data = ( _name, _faculty, _id)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return res("success",request.json,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

        
@app.route('/delete_department/<string:id>', methods=['DELETE'])
def delete_department(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM department WHERE department_id=%s", (id,))
        conn.commit()
        return res("success",None,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

################อัปโหลดและค้นหารายชื่อ#########################################################

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if request.method == "POST":
#         if request.files:
#             image = request.files["image"]
#             # name = request.form["name"]
#             text = pytesseract.image_to_string(
#                 Image.open(image), lang="tha+eng")
#         try:
#             conn = mysql.connect()
#             cursor = conn.cursor(pymysql.cursors.DictCursor)
#             name = text.strip()
#             fullname = list(name.split())
            
#             if len(fullname) > 1:
#                 cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name,position.position_name FROM user JOIN department JOIN prefix JOIN faculty JOIN usertype JOIN position WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s AND department.department_id = user.department_id AND prefix.prefix_id = user.prefix_id AND faculty.faculty_id = user.faculty_id AND usertype.usertype_id = user.usertype_id AND position.position_id = user.position_id",
#                                ("%" + fullname[0] + "%", "%" + fullname[1] + "%"))
#             else:
#                 cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name,position.position_name FROM user JOIN department JOIN prefix JOIN faculty JOIN usertype JOIN position WHERE user.user_fname LIKE %s AND  department.department_id = user.department_id AND prefix.prefix_id = user.prefix_id AND faculty.faculty_id = user.faculty_id AND usertype.usertype_id = user.usertype_id AND position.position_id = user.position_id",
#                                ("%" + fullname[0] + "%"))
#             if cursor.rowcount == 0:
#                 return "ไม่พบข้อมูลผู้ใช้"
#             rows = cursor.fetchall()
#             return res("success",rows)
#         except Exception as e:
#             print(e)
#         finally:
#             cursor.close()
#             conn.close()

###############################################################################################

# @app.route('/upload_base64', methods=['POST'])
# def upload_base64():
#         if request.form:
#             name = request.form["name"]
#             imgstring  = name.split('base64,')[-1].strip()
#             image_string = io.BytesIO(base64.b64decode(imgstring))
#             image = Image.open(image_string)
#             text = pytesseract.image_to_string(image, lang="tha+eng")
#         try:
#             conn = mysql.connect()
#             name = text.strip()
#             fullname = list(name.split())
#             cursor = conn.cursor(pymysql.cursors.DictCursor)
#             if len(name) > 1:
#                 cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
#                                             ("%" + fullname[0] + "%", "%" + fullname[1] + "%"))
#             else:
#                 cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE user.user_fname LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
#                                            ("%" + fullname[0] + "%"))
#             if cursor.rowcount == 0:
#                 return not_found()
#             rows = cursor.fetchall()
#             return res("success",rows)
#         except Exception as e:
#             print(e)
#         finally:
#             cursor.close()
#             conn.close()

# @app.route('/upload_base64', methods=['POST'])
# def upload_base64():
#         if request.form:
#             name = request.form["name"]
#             imgstring = name
#             imgstring  = imgstring.split('base64,')[-1].strip()
#             image_string = io.BytesIO(base64.b64decode(imgstring))
#             image = Image.open(image_string)
#             text = pytesseract.image_to_string(image, lang="tha+eng")
#         try:
#             conn = mysql.connect()
#             name = text.strip()
#             fullname = list(name.split())
#             cursor = conn.cursor(pymysql.cursors.DictCursor)
#             if len(fullname) > 1:
#                 cursor.execute("SELECT user.user_id,user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
#                                             ("%" + fullname[0] + "%", "%" + fullname[1] + "%"))
#             else:
#                 cursor.execute("SELECT user.user_id,user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE user.user_fname LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
#                                            ("%" + fullname[0] + "%"))
#             if cursor.rowcount == 0:
#                 return not_found()
#             rows = cursor.fetchall()
#             return res("success",rows,200)
#         except Exception as e:
#             print(e)
#         finally:
#             cursor.close()
#             conn.close()

@app.route('/upload_base64', methods=['POST'])
def upload_base64():
        if request.form:
            name = request.form["name"]
            imgstring = name
            imgstring  = imgstring.split('base64,')[-1].strip()
            image_string = io.BytesIO(base64.b64decode(imgstring))
            image = Image.open(image_string)
            text = pytesseract.image_to_string(image, lang="tha+eng")
        try:
            conn = mysql.connect()
            name = text.strip()
            fullname = list(name.split())
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            if len(fullname) > 1:
                cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name FROM user JOIN prefix on user.prefix_id = prefix.prefix_id JOIN department on user.department_id = department.department_id JOIN faculty ON department.faculty_id = faculty.faculty_id JOIN usertype on user.usertype_id = usertype.usertype_id WHERE user.user_fname LIKE %s OR user.user_lname LIKE %s ",
                                            ("%" + fullname[0] + "%", "%" + fullname[1] + "%"))
            else:
                cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE user.user_fname LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id",
                                           ("%" + fullname[0] + "%"))
            if cursor.rowcount == 0:
                return not_found()
            rows = cursor.fetchall()
            return res("success",rows,200)
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()

###############################################################################################

@app.route('/upload_sender', methods=['POST'])
def upload_sender():
        if request.form:
            name = request.form["name"]
            imgstring  = name.split('base64,')[-1].strip()
            image_string = io.BytesIO(base64.b64decode(imgstring))
            image = Image.open(image_string)
            text = pytesseract.image_to_string(image, lang="tha+eng")
            name = text.strip()
            return res("success",name,200)
       
######################################################################


@app.route('/adduser', methods=['POST'])
def adduser():
    try:
        _json = request.json
        _member = _json['member_id']
        _prefix = _json['prefix_id']
        _userfname = _json['user_fname']
        _userlname = _json['user_lname']
        _department = _json['department_id']
        _usertype = _json['usertype_id']

        conn = mysql.connect()
        cursor = conn.cursor()
        if len(_member) == 13 or _member == "-" :
            if  _member == "-" :
                sql = "INSERT INTO user(member_id, prefix_id, user_fname, user_lname, department_id, usertype_id) VALUES(%s, %s, %s, %s, %s, %s)"
                data = (_member, _prefix, _userfname, _userlname,_department, _usertype)
            else:
                cursor.execute("SELECT COUNT(user.member_id) FROM user WHERE user.member_id LIKE %s",("%" + _member + "%"))
                rows = cursor.fetchone()
                if rows[0] == 1 or rows[0] > 1 :
                    return res("รหัสซ้ำ",_member,422)
                else:
                    sql = "INSERT INTO user(member_id, prefix_id, user_fname, user_lname, department_id, usertype_id) VALUES(%s, %s, %s, %s, %s, %s)"
                    data = (_member, _prefix, _userfname, _userlname,_department, _usertype,)
            cursor.execute(sql, data)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            sql = "SELECT user_id,user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_id,department.department_name,faculty.faculty_id,faculty.faculty_name,usertype.usertype_id,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE  user.user_fname LIKE %s AND user.user_lname LIKE %s AND user.member_id LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id  AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id"
            data = ("%" +  _userfname + "%", "%" + _userlname + "%", "%" + _member + "%")
            cursor.execute(sql, data)
            conn.commit()           
            rows = cursor.fetchall()
            print(rows)
            return res("success",rows,200)
        else:
            return res("รหัสไม่ถูกต้อง",_member,422)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

########################################
@app.route('/delete_user/<string:id>', methods=['DELETE'])
def delete_user(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE user_id=%s", (id,))
        conn.commit()
        return res("success",None,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/update_user', methods=['PUT'])
def update_user():
    try:
        _json = request.json
        _userid = _json['id']
        _member = _json['member_id']
        _prefix = _json['prefix_id']
        _userfname = _json['user_fname']
        _userlname = _json['user_lname']
        _department = _json['department_id']
        _usertype = _json['usertype_id']
        
        sql = "UPDATE user SET member_id=%s, prefix_id=%s, user_fname=%s, user_lname=%s, department_id=%s, usertype_id=%s WHERE user_id=%s"
        data = (_member, _prefix, _userfname, _userlname,_department, _usertype, _userid)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT user_id,user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_id,department.department_name,faculty.faculty_id,faculty.faculty_name,usertype.usertype_id,usertype.userType_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype  WHERE  user.user_fname LIKE %s AND user.user_lname LIKE %s AND user.member_id LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id  AND user.usertype_id = usertype.usertype_id AND department.faculty_id = faculty.faculty_id"
        data = ("%" +  _userfname + "%", "%" + _userlname + "%", "%" + _member + "%")
        cursor.execute(sql, data)
        conn.commit()
        rows = cursor.fetchall()
        return res("success",rows,200)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


# def res(status,data):
#     message = {
#         'status': status,
#         'data': data,
#     }
#     resp = jsonify(message)
#     resp.status_code = 200
#     return resp

def res(status,data,code):
    message = {
        'status': status,
        'data': data,
        'code': code
    }
    resp = jsonify(message)
    resp.status_code = 200
    return resp


if __name__ == '__main__':
    app.run()
  
