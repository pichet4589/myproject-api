import os
import pymysql
import json
from flask import Flask, request, jsonify
from pytesseract import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename
from app import app
from db_config import mysql
import io
import base64


# //////////////////////////////////////////////////////////////////////////////////

import jwt
from datetime import datetime, timedelta
from functools import wraps
import hashlib

# Global Values
##############################################################################
EXP_TIME   = 10             # Expire Time(Minutes)
JWT_ALG    = 'HS256'        # JWT Algorithm
##############################################################################

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
    credentials = request.get_json()    # Getting Credentials

    # Credentials
    username = credentials['username']
    password = credentials['password']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "SELECT * FROM login WHERE username=%s"
    sql_where = (username,)
	# print (generate_password_hash("P1ain-text-user-passw@rd", "sha256"))
    cursor.execute(sql, sql_where)
    row = cursor.fetchone()

     # Password Hash
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Checking Whether Username & Password Exist or Not
    if username == username and row[2] == password_hash:
        auth_token = jwt.encode(
            {
                'username':username,
                'exp':datetime.utcnow()+timedelta(minutes=EXP_TIME)
            },
            app.secret_key,     # Secret Key
            JWT_ALG             # JWT Algorithm
            )

            # If Credentials are Valid
        return jsonify(
                {
                 'message':'Authenticated',
                 'auth_token':auth_token,
                 'status':200
                }
            ),200
    else:
    # If Credentials are Invalid
        return jsonify(
        {
         'message':'ชื่อผู้ใช้หรือรหัสผ่านผิด'
    
         }
    )
    
# //////////////////////////////////////////////////////////////////////////////////

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','base64'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def hello_world():
    q = request.args.get('q')
    print(q)
    return {"สวัสดีครับ ค่ะ": q}, 201


@app.route('/ping')
def ping():
    return ping


# ////////////////////////////////////////////////////////////////////

@app.route('/upload1', methods=['POST'])
def upload_file12():
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
                cursor.execute("SELECT * FROM user  WHERE user.user_fname LIKE %s or user.user_lname LIKE %s ",
                                            ("%" + fullname[0] + "%", "%" + fullname[1] + "%"))
            else:
                cursor.execute("SELECT * FROM USER WHERE user.user_fname LIKE %s ",
                                           ("%" + fullname[0] + "%"))
            if cursor.rowcount == 0:
                    return jsonify(
                {
                    'message':'Token is invalid'
                }
            ),403
            rows = cursor.fetchall()
            resp = jsonify(rows)
            resp.status_code = 200
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()


# อัปโหลดรูปภาพ แปลง รูปภาพ ให้เป็น ข้อความ
@app.route('/upload_img', methods=['POST','GET'])
def upload_sender():
        if request.form:
            name = request.form["name"]
            imgstring  = name.split('base64,')[-1].strip()
            image_string = io.BytesIO(base64.b64decode(imgstring))
            image = Image.open(image_string)
            text = pytesseract.image_to_string(image, lang="tha+eng")
            name = text.strip()
            return name


@app.route('/search_user', methods=['POST'])
def search_user():
    if request.method == "POST":
        if request.form:
            key = request.form["name"]
        try:
            conn = mysql.connect()
            name = list(key.split())
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            if len(name) > 1:
                cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name,position.position_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype JOIN position WHERE  user.user_fname LIKE %s AND user.user_lname LIKE %s AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id AND user.faculty_id = faculty.faculty_id AND user.usertype_id = usertype.usertype_id AND user.position_id = position.position_id",
                               ("%" + name[0] + "%", "%" + name[1] + "%"))
            else:
                cursor.execute("SELECT user.member_id,prefix.prefix_name,user.user_fname,user.user_lname,department.department_name,faculty.faculty_name,usertype.userType_name,position.position_name FROM user JOIN prefix JOIN department JOIN faculty JOIN usertype JOIN position WHERE  user.user_fname LIKE %s  AND user.prefix_id = prefix.prefix_id AND user.department_id = department.department_id AND user.faculty_id = faculty.faculty_id AND user.usertype_id = usertype.usertype_id AND user.position_id = position.position_id",
                               ("%" + name[0] + "%"))
            if cursor.rowcount == 0:
                return "ไม่พบข้อมูลผู้ใช้"
            rows = cursor.fetchall()
            resp = jsonify(rows)
            resp.status_code = 200
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()

# @app.route('/search_user', methods=['POST'])
# def search_user():
#     if request.method == "POST":
#         if request.form:
#             key = request.form["name"]
#         try:
#             conn = mysql.connect()
#             name = list(key.split())
#             print(name)
#             cursor = conn.cursor(pymysql.cursors.DictCursor)
#             if len(name) > 1:
#                 cursor.execute("SELECT * FROM user  WHERE user.user_fname LIKE %s and user.user_lname LIKE %s ",
#                                ("%" + name[0] + "%", "%" + name[1] + "%"))
#             else:
#                 cursor.execute("SELECT * FROM USER WHERE user.user_fname LIKE %s ",
#                                ("%" + name[0] + "%"))
#             if cursor.rowcount == 0:
#                 return "ไม่พบข้อมูลผู้ใช้"
#             rows = cursor.fetchall()
#             resp = jsonify(rows)
#             resp.status_code = 200
#             return resp
#         except Exception as e:
#             print(e)
#         finally:
#             cursor.close()
#             conn.close()

# ////////////////////////////////////////////////////////////////////
# @app.route('/check_letter', methods=['GET'])
# def check_letter():

#         args = request.args
#         _id = args['id']
#         _username = args['name']
        
#         try:
#             conn = mysql.connect()
#             cursor = conn.cursor(pymysql.cursors.DictCursor)
#             if _id and _username:
#                 name = _username.split()
#                 name_id = list(name)
#                 print(name_id)
#                 if len(name_id) > 1:
#                      cursor.execute("SELECT * FROM letter JOIN user WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s AND  user.member_id LIKE %s   AND user.user_id = letter.user_id",
#                                ("%" + name_id[0] + "%", "%" + name_id[1] + "%", "%" + _id + "%"))
#                 else:
#                     cursor.execute("SELECT * FROM letter JOIN user WHERE user.user_fname LIKE %s AND  user.member_id LIKE %s AND user.user_id = letter.user_id",
#                                ("%" + name_id[0] + "%", "%" + _id + "%"))

#             elif _id:
#                 cursor.execute("SELECT * FROM letter JOIN user WHERE user.member_id LIKE %s AND user.user_id = letter.user_id",
#                                ("%" + _id + "%"))
#             elif _username:
#                 name = _username.split()
#                 name_id = list(name)
#                 print(name_id)
#                 if len(name_id) > 1:
#                     cursor.execute("SELECT * FROM letter JOIN user WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s  AND user.user_id = letter.user_id",
#                                ("%" + name_id[0] + "%", "%" + name_id[1] + "%"))
#                 else:
#                     cursor.execute("SELECT * FROM letter JOIN user WHERE user.user_fname LIKE %s AND user.user_id = letter.user_id",
#                                ("%" + name_id[0] + "%"))          
#             else:
#                 cursor.execute("SELECT user.user_fname,department.department_name,faculty.faculty_name,letter.export_name,category.category_name,status_letter.status_name FROM  user JOIN category JOIN department JOIN faculty JOIN letter JOIN position JOIN prefix JOIN status_letter JOIN usertype WHERE faculty.faculty_id = department.faculty_id AND department.department_id = user.department_id AND user.user_id = letter.user_id  AND user.prefix_id = prefix.prefix_id AND user.position_id = position.position_id AND user.usertype_id = usertype.usertype_id  AND letter.category_id = category.category_id AND letter.status_id = status_letter.status_id")
#             if cursor.rowcount == 0:
#                 return res("data not found",None)
#             rows = cursor.fetchall()
#             # res("success",rows)
#             return res("success",rows)
#         finally:
#             cursor.close()
#             conn.close()
######## ตรวจสอบจดหมาย #########
@app.route('/check_letter', methods=['GET'])
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
                     cursor.execute("SELECT  user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_name,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s AND  user.member_id LIKE %s   AND user.user_id = letter.user_id  AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id",
                               ("%" + _name[0] + "%", "%" + _name[1] + "%", "%" + _id + "%"))
                else:
                    cursor.execute("SELECT  user.member_id,user.user_fname,letter.export_name,user.user_lname,department.department_name,category.category_name,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND  user.member_id LIKE %s AND user.user_id = letter.user_id  AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id",
                               ("%" + _name[0] + "%", "%" + _id + "%"))

            elif _id:
                cursor.execute("SELECT  user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_name,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.member_id LIKE %s AND user.user_id = letter.user_id  AND user.user_id = letter.user_id AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id",
                               ("%" + _id + "%"))
            elif _username:
                name = _username.split()
                _name = list(name)
                if len(_name) > 1:
                    cursor.execute("SELECT  user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_name,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND user.user_lname LIKE %s  AND user.user_id = letter.user_id AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id",
                               ("%" + _name[0] + "%", "%" + _name[1] + "%"))
                else:
                    cursor.execute("SELECT  user.member_id,user.user_fname,user.user_lname,letter.export_name,department.department_name,category.category_name,status_letter.status_name FROM letter JOIN user JOIN status_letter JOIN department JOIN category WHERE user.user_fname LIKE %s AND user.user_id = letter.user_id AND letter.status_id = status_letter.status_id  AND user.department_id = department.department_id AND category.category_id = letter.category_id",
                               ("%" + _name[0] + "%"))          
            else:
                cursor.execute("SELECT user.user_fname,department.department_name,faculty.faculty_name,letter.export_name,category.category_name,status_letter.status_name FROM  user JOIN category JOIN department JOIN faculty JOIN letter JOIN position JOIN prefix JOIN status_letter JOIN usertype WHERE faculty.faculty_id = department.faculty_id AND department.department_id = user.department_id AND user.user_id = letter.user_id  AND user.prefix_id = prefix.prefix_id AND user.position_id = position.position_id AND user.usertype_id = usertype.usertype_id  AND letter.category_id = category.category_id AND letter.status_id = status_letter.status_id")
            if cursor.rowcount == 0:
                return res("data not found",None)
            rows = cursor.fetchall()
            return res("success",rows)
        finally:
            cursor.close()
            conn.close()


# get ข้อมูลจดหมาย
@app.route('/get_id_letter/<string:id>', methods=['GET'])
def get_id_letter(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM letter WHERE id=%s", (id))
        rows = cursor.fetchall()
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
      

@app.route('/letter', methods=['GET'])
def get_letter():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM letter")
        rows = cursor.fetchall()
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
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
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
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
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
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
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
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
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
        
@app.route('/position', methods=['GET'])
def get_position():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM position")
        rows = cursor.fetchall()
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
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
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
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
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
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
        print(rows)
        resp = jsonify(rows)
        resp.status_code = 200
        return resp
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
###############################################################################################

@app.route('/addletter', methods=['POST'])
def add_letter():
    conn = None
    try:
        _json = request.json
        _user = _json['user_id']
        _exportName = _json['exportName']
        _category = _json['category_id']
        _status = _json['status_id']

        # validate the received values
        if _user and _exportName and _category and _status and  request.method == 'POST':
            # save edits
            sql = "INSERT INTO `letter` (`id`, `user_id`, `exportName`, `category_id`, `status_id`) VALUES (NULL, %s, %s, %s, %s)"
            data = (_user,_exportName,  _category, _status)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            resp = jsonify('เพิ่มข้อมูลจดหมายสำเร็จ!')
            resp.status_code = 200
            return resp
        else:
            return not_found()
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

        
# @app.route('/update_letter', methods=['PUT'])
# def update_letter():
#     try:
#         _json = request.json
#         _id = _json['id']
#         _userfname = _json['user_id']
#         _exportfname = _json['exportName']
#         _category = _json['category_id']
#         _statusname = _json['status_id']
#         # validate the received values
#         if _userfname and  _exportfname  and _category and _statusname and _id and  request.method == 'PUT':
#             sql = "UPDATE letter SET user_id=%s, exportName=%s, category_id=%s, status_id=%s WHERE id=%s"
#             data = ( _userfname, _exportfname, _category, _statusname, _id)
#             conn = mysql.connect()
#             cursor = conn.cursor()
#             cursor.execute(sql, data)
#             conn.commit()
#             resp = jsonify('อัพเดทข้อมูลจดหมายสำเร็จ!')
#             resp.status_code = 200
#             return resp
#         else:
#             return not_found()
#     except Exception as e:
#         print(e)
#     finally:
#         cursor.close()
#         conn.close()

@app.route('/update_status', methods=['PUT'])
def update_status():
    try:
        _json = request.json
        _id = _json['id']
       
        _statusname = _json['status_id']
        # validate the received values
        if   _statusname and _id and  request.method == 'PUT':
            sql = "UPDATE letter SET   status_id=%s WHERE id=%s"
            data = ( _statusname, _id)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            resp = jsonify('อัพเดทข้อมูลจดหมายสำเร็จ!')
            resp.status_code = 200
            return resp
        else:
            return not_found()
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


# ลบข้อมูลจดหมาย
@app.route('/delete_letter/<string:id>', methods=['DELETE'])
def delete_letter(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM letter WHERE id=%s", (id,))
        conn.commit()
        resp = jsonify('ลบข้อมูลจดหมายสำเร็จ!')
        resp.status_code = 200
        return resp
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        
#######################################################################################
        
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            # key = request.form["key"]
            text = pytesseract.image_to_string(
                Image.open(image), lang="tha+eng")
        try:
            conn = mysql.connect()
            name = text.strip()
            # name = "ปฏิภาณ  วงศ์จันทร์"
            # lname = name.split(' ')
            fullname = list(name.split())
            # print(">>>>>")
            print(fullname)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # print(fullname[0])
            print(">>>>>")
            # print(fullname[1])
            print(len(fullname))
            
            if len(fullname) >1:
                cursor.execute("SELECT * FROM USER WHERE user.user_fname LIKE %s or user.user_lname LIKE %s ",
                           ("%" + fullname[0] + "%", "%" + fullname[1] + "%"))     
            else:
                cursor.execute("SELECT * FROM USER WHERE user.user_fname LIKE %s ",
                           ("%" + fullname[0] + "%"))   
            if cursor.rowcount == 0:
                return "ไม่พบข้อมูลผู้ใช้"
                # sql = "INSERT INTO `user` (`user_id`, `user_fname`, `department_id`, `user_lname`, `prefix_id`, `usertype_id`, `position_id`) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                # data = ('60175591481',  fullname[0],
                #         '1733', fullname[1], '6', '1', '13')
                # cursor.execute(sql, data)
                # conn.commit()
            rows = cursor.fetchall()
            resp = jsonify(rows)
            resp.status_code = 200
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()

            
            
###############################################################################################


@app.route('/upload1', methods=['POST'])
def upload_file1():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            # key = request.form["key"]

            text = pytesseract.image_to_string(
                Image.open(image), lang="tha+eng")
        try:
            conn = mysql.connect()
            name = text.strip()
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM USER WHERE user.user_fname LIKE %s ",
                           ("%" + name + "%"))
            
            if cursor.rowcount == 0:
                fullname = list(name.split())     
                sql = ("SELECT * FROM USER WHERE user.user_fname LIKE %s or user.user_lname LIKE %s ",
                           ("%" + fullname[0] + "%", "%" + fullname[1] + "%"))
             
                cursor.execute(sql)
                conn.commit()
            rows = cursor.fetchall()
            resp = jsonify(rows)
            resp.status_code = 200
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()

@app.route('/adduser', methods=['POST'])
def add_user():
    try:
        _json = request.json
        _member = _json['member_id']
        _prefix = _json['prefix_id']
        _userfname = _json['user_fname']
        _userlname = _json['user_lname']
        _department = _json['department_id']
        _faculty = _json['faculty_id']
        _usertype = _json['usertype_id']
        _position = _json['position_id']
        # validate the received values
        if _member and _prefix and _userfname and _userlname and _department and _faculty and _usertype and _position and request.method == 'POST':
            # save edits
            sql = "INSERT INTO user(member_id, prefix_id, user_fname, user_lname, department_id, faculty_id, usertype_id, position_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
            data = (_member, _prefix, _userfname, _userlname,
                    _department, _faculty, _usertype, _position)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            resp = jsonify('เพิ่มข้อมูลผู้ใช้งานสำเร็จ!')
            resp.status_code = 200
            return resp
        else:
            return not_found()
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/delete_user/<string:id>', methods=['DELETE'])
def delete_user(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE user_id=%s", (id,))
        conn.commit()
        resp = jsonify('ลบข้อมูลสำเร็จ!')
        resp.status_code = 200
        return resp
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
        _faculty = _json['faculty_id']
        _usertype = _json['usertype_id']
        _position = _json['position_id']
        # validate the received values
        if  _member and _prefix and _userfname and _userlname and _department and _faculty and _usertype and _position and _userid and request.method == 'PUT':
            # save edits
            sql = "UPDATE user SET member_id=%s, prefix_id=%s, user_fname=%s, user_lname=%s, department_id=%s, faculty_id=%s, usertype_id=%s, position_id=%s WHERE user_id=%s"
            data = (_member, _prefix, _userfname, _userlname,
                    _department, _faculty, _usertype, _position, _userid)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            resp = jsonify('อัพเดทข้อมูลผู้ใช้งานสำเร็จ!')
            resp.status_code = 200
            return resp
        else:
            return not_found()
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


def res(status,data):
    message = {
        'mgs': status,
        'data': data,
    }
    resp = jsonify(message)
    resp.status_code = 200
    return resp


if __name__ == '__main__':
    app.run()
