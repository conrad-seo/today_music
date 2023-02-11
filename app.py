import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)
from pymongo import MongoClient
import certifi
ca = certifi.where()
client = MongoClient('mongodb+srv://test:sparta@cluster0.sk4ckqt.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.today_music
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}


@app.route('/')
def home():
    return render_template('index.html')

@app.route("/show_list", methods=["GET"])
def list_get():
    pl_list = list(db.list.find({}, {'_id': False}))

    return jsonify({'pl_list': pl_list})

@app.route("/make_list", methods=["POST"])
def list_post():
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    url_receive = request.form['url_give']
    url = url_receive

    if url == '' or 'https' not in url or url.upper() == url.lower():
        return jsonify({'msg': '유효한 주소가 아닙니다.'})

    if star_receive =='':
        return jsonify({'msg': '별점을 선택해주세요!'})

    if comment_receive == '':
        return jsonify({'msg': '코멘트를 작성해주세요!'})


    data = requests.get(url, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')

    title = soup.select_one('meta[property="og:title"]')['content']
    image = soup.select_one('meta[property="og:image"]')['content']

    doc = {
        'star': star_receive,
        'comment': comment_receive,
        'url': url_receive,
        'title' : title,
        'image' : image
    }
    db.list.insert_one(doc)
    return jsonify ({'msg':'등록 완료!'})


    # if url == '' or 'https' not in url or url.upper() == url.lower():

    #
    #
    # if id_receive == '' or email_receive == '' or password_receive == '' or pwcf_receive == '':
    #     return jsonify({'ans': 'fail', 'msg': '공백이 있습니다'})
    # elif '@' not in email_receive or '.' not in email_receive:
    #     return jsonify({'ans': 'fail', 'msg': '이메일 형식이 아닙니다.'})
    # elif pwcf_receive != password_receive:
    #     return jsonify({'ans': 'fail', 'msg': '비밀번호가 다릅니다'})


    # return jsonify({'msg': '등록 완료!','title': title})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)