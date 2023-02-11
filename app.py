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

    # data = requests.get('url', headers=headers)
    # soup = BeautifulSoup(data.text, 'html.parser')
    #
    # title = soup.select('head > title')

    doc = {
        'star': star_receive,
        'comment': comment_receive,
        'url': url_receive,
        # 'title' : title
    }
    db.list.insert_one(doc)

    return jsonify({'msg':'저장 완료!'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=False)