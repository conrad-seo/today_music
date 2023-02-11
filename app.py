from flask import Flask, render_template, request, jsonify, url_for, redirect
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

import certifi

ca = certifi.where()

import pymongo

client = pymongo.MongoClient("mongodb+srv://test:sparta@cluster0.sk4ckqt.mongodb.net/?retryWrites=true&w=majority",tlsCAFile=ca)
db = client.today_music

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'STORE_MANAGE'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib

# re.함수를 사용하기 위해 추가하였습니다.
import re

# json 내장 모듈을 사용하기 위함
import json


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        return render_template('index.html', nickname=user_info["nick"])
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


# /회원가입페이지
@app.route('/register')
def join():
    return render_template('register.html')


#################################
##  회원가입을 위한 API            ##
#################################
# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    password_receive = request.form['pw_give']
    pwcf_receive = request.form['pwcf_give']
    nickname_receive = request.form['nickname_give']
    email_receive = request.form['email_give']

    res = db.users.find({}, {'_id': False})

    # 최초 DB가 없을때도 실행하기 위해 추가함
    if id_receive == '' or email_receive == '' or password_receive == '' or pwcf_receive == '':
        return jsonify({'ans': 'fail', 'msg': '공백이 있습니다'})
    elif '@' not in email_receive or '.' not in email_receive:
        return jsonify({'ans': 'fail', 'msg': '이메일 형식이 아닙니다.'})
    elif pwcf_receive != password_receive:
        return jsonify({'ans': 'fail', 'msg': '비밀번호가 다릅니다'})

    for list in res:
        # 공백 처리, 해당 부분에서 약간의 오류를 발생시키면 html 스크립트 공백체크가 작동한다..
        if id_receive == '' or email_receive == '' or password_receive == '' or pwcf_receive == '':
            return jsonify({'ans': 'fail', 'msg': '공백이 있습니다'})
        # 이메일 형식 체크 @, '.' 포함 여부 확인
        elif '@' not in email_receive or '.' not in email_receive:
            return jsonify({'ans': 'fail', 'msg': '이메일 형식이 아닙니다.'})
        # 회원가입 시 중복 ID, Email 처리
        elif list['name'] == id_receive or list['email'] == email_receive:
            return jsonify({'ans': 'fail', 'msg': '이름 또는 이메일 중복!'})
        # 2차 비밀번호 체크
        elif pwcf_receive != password_receive:
            return jsonify({'ans': 'fail', 'msg': '비밀번호가 다릅니다'})
    PW = hashlib.sha256(password_receive.encode()).hexdigest()
    PW2 = hashlib.sha256(pwcf_receive.encode()).hexdigest()
    print(PW)
    print(PW2)

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    db.user.insert_one(
        {'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive, 'email': email_receive})
    return jsonify({'result': 'success'})


#################################
##  ID, 닉네임 중복학인           ##
#################################
@app.route("/register/check_id", methods=["POST"])
def check_id():
    id_receive = request.form['id_give']
    user = db.user.find_one({'id': id_receive})
    if (user == None):
        return jsonify({'msg': '사용가능한 ID입니다.'})
    else:
        return jsonify({'msg': 'ID가 존재합니다.'})


@app.route("/register/check_nick", methods=["POST"])
def check_nick():
    nick_receive = request.form['nick_give']
    user = db.user.find_one({'nick': nick_receive})
    if (user == None):
        return jsonify({'msg': '사용가능한 닉네임입니다.'})
    else:
        return jsonify({'msg': '닉네임이 존재합니다.'})


@app.route("/register/check_email", methods=["POST"])
def check_email():
    email_receive = request.form['email_give']
    user = db.user.find_one({'email': email_receive})
    if (user == None):
        return jsonify({'msg': '사용가능한 이메일입니다.'})
    else:
        return jsonify({'msg': '이메일이 존재합니다.'})


#################################
##  로그인을 위한 API            ##
#################################
# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    # 최초 DB가 없을때도 실행하기 위해 추가함
    if id_receive == '' or pw_receive == '':
        return jsonify({'ans': 'fail', 'msg': '공백이 있습니다'})

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# [유저 정보 확인 API]
# 로그인된 유저만 call 할 수 있는 API입니다.
# 유효한 토큰을 줘야 올바른 결과를 얻어갈 수 있습니다.
# (그렇지 않으면 남의 장바구니라든가, 정보를 누구나 볼 수 있겠죠?)
@app.route('/api/nick', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')

    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        return jsonify({'result': 'success', 'nickname': userinfo['nick']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})


@app.route('/listget', methods=["GET"])
def list_get_num():
    token_receive = request.cookies.get('mytoken')
    num = request.args.get('num')
    print(num)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        list = db.list.find_one({'num': int(num)})
        print(list)
        return render_template('detail.html', nickname=user_info["nick"], list=list)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route("/show_list", methods=["POST"])
def list_get():
    pl_list = list(db.list.find({}, {'_id': False}).sort([{'num', -1}]))
    # print(pl_list)
    return jsonify(pl_list)


@app.route("/make_list", methods=["POST"])
def list_post():
    nick_receive = request.form['nick_give']
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    url_receive = request.form['url_give']

    con_url = url_receive.replace('watch?v=', 'embed/')

    if url_receive == '' or 'https' not in url_receive or url_receive.upper() == url_receive.lower():
        return jsonify({'msg': '유효한 주소가 아닙니다.'})

    if star_receive == '':
        return jsonify({'msg': '별점을 선택해주세요!'})

    if comment_receive == '':
        return jsonify({'msg': '코멘트를 작성해주세요!'})

    if len(list(db.list.find({}, {'_id': False}))) == 0:
        count = 1
    else:
        addlist_num = list(db.list.find({}, {}).sort([{'num', -1}]))
        # print(addlist_num)
        dbcount = addlist_num[0]['num']
        count = dbcount + 1

    data = requests.get(url_receive, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')

    title = soup.select_one('meta[property="og:title"]')['content']
    image = soup.select_one('meta[property="og:image"]')['content']

    doc = {
        'num': count,
        'name': nick_receive,
        'star': star_receive,
        'comment': comment_receive,
        'url': con_url,
        'title': title,
        'image': image
    }
    db.list.insert_one(doc)
    return jsonify({'msg': '등록완료'})


@app.route('/in_comment', methods=["POST"])
def input_comment():
    num_receive = request.form['num_give']
    nick_name_receive = request.form['nick_give']
    comment_receive = request.form['comment_give']

    doc = {
        'num': num_receive,
        'nick': nick_name_receive,
        'comment': comment_receive
    }

    db.comment.insert_one(doc)
    return jsonify({'msg': '댓글 등록 완료'})


@app.route('/show_comment', methods=["POST"])
def show_comment():
    num_receive = request.form['num_give']
    semi_list = list(db.comment.find({'num': num_receive}, {'_id': False}))
    print(semi_list)
    return jsonify({'smn_list': semi_list})

@app.route("/list/modify", methods=["POST"])
def list_modify():
    num_receive = request.form['num_give']
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    print(num_receive, star_receive, comment_receive)
    print(type(num_receive))
    print(type(star_receive))
    print(type(comment_receive))
    db.list.update_one({'num': int(num_receive)}, {'$set': {'star': star_receive}})
    db.list.update_one({'num': int(num_receive)}, {'$set': {'comment': comment_receive}})
    return jsonify({'msg': '코멘트 수정 완료!'})

@app.route("/list/delete", methods=["POST"])
def list_delete():
    num_receive = request.form['num_give']
    db.list.delete_one({'num': int(num_receive)})
    return jsonify({'msg': '삭제 완료'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
