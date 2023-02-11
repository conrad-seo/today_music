import requests as requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

import jwt

from pymongo import MongoClient
client = MongoClient('mongodb+srv://test:sparta@cluster0.sk4ckqt.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.today_music

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'STORE_MANAGE'

headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
data = requests.get('https://www.youtube.com/watch?v=xgvckGs6xhU',headers=headers)

soup = BeautifulSoup(data.text, 'html.parser')
#유뷰브 제목입력
textytb = soup.select_one('title').text

@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        return render_template('detail.html', nickname=user_info["nick"])
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route("/inf", methods=["GET"])
def ytb_get():
    music_infs = list(db.list.find({}, {'_id': False}))
    return jsonify({'music_inf': music_infs})

@app.route("/detail", methods=["POST"])
def comment_post():

    comment_receive = request.form['comment_give']

    doc = {
        'comment':comment_receive
    }
    db.comment.insert_one(doc)

    return jsonify({'msg': '댓글 등록 완료'})

@app.route("/detail", methods=["GET"])
def comment_get():
    comment_inputs = list(db.comment.find({}, {'_id': False}))
    return jsonify({'comment_input': comment_inputs})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)