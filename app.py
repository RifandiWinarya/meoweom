import json
from bson import SON, ObjectId
from pymongo import MongoClient
from bson import json_util
from functools import wraps
from datetime import datetime, timedelta
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from werkzeug.utils import secure_filename
import os
import secrets

client = MongoClient(
    "mongodb+srv://kelompok3grup7:mbkm_2023@mbkm.3kge4dh.mongodb.net/?retryWrites=true&w=majority"
)

db = client.MBKM2023

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/gambar"

app.secret_key = "MBKM2023"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@login_required
def home():
    username = session.get('username', None)
    user_info = db.users.find_one({"username": username}, {"_id": False})

    users = db.users

    posts = db.posts.find().sort("date", -1)
    username_login = session.get("username")
    return render_template("index.html",username_login=username_login, user_info=user_info, posts=posts, users=users)


@app.route("/artikel")
@login_required
def artikel():
    role = session.get("role")
    username_login = session.get("username")
    # print(role)
    return render_template("artikel.html", role=role, username_login=username_login)


@app.route("/artikel/<judul>")
@login_required
def artikel_isi(judul):
    judul = judul
    username_login = session.get("username")
    return render_template("artikel_isi.html", judul=judul,username_login=username_login)


@app.route('/profil/<username>')
@login_required
def profil(username):
    user_login = session.get('username', None)
    user_info = db.users.find_one({"username": username}, {"_id": False})

    users = db.users

    posts = db.posts.find().sort("date", -1)
    return render_template("profil.html", user_info=user_info, posts=posts, users=users, user_login=user_login)


@app.route("/profillain")
@login_required
def profiluserlain():
    return render_template("profiluserlain.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/registrasi")
def registrasi():
    return render_template("sign_up.html")


@app.route("/catshop")
@login_required
def catshop():
    username_login = session.get("username")
    role = session.get("role")
    return render_template("catshop.html",role=role, username_login=username_login)


@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    username = session.get('username', None)
    user_info = db.users.find_one({"username": username}, {"_id": False})
    if request.method == 'POST':
        username = session.get("username")
        kategori = request.form['kategori']
        isi = request.form['isi']
        gambar = request.files['gambar']
        date = datetime.now()

        if gambar:
            random_string = secrets.token_hex(8)
            _, extension = os.path.splitext(gambar.filename)
            filename = f"{random_string}{extension}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            gambar.save(filepath)

        else:
            filepath = '/'
            
        db.posts.insert_one({
            'username': username,
            'kategori': kategori,
            'isi': isi,
            'gambar': filepath,
            'date': date,
        })
        return redirect(url_for('home'))

    return render_template("post.html", user_info=user_info)


@app.route("/post/<post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    username = session.get('username', None)
    if username:
        comment_content = request.form.get('comment_content')
        timestamp = datetime.utcnow()

        comment = {
            'username': username,
            'content': comment_content,
            'timestamp': timestamp
        }

        # Update the post in the database to add the new comment
        db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$push': {'comments': comment}}
        )

        return redirect(url_for('home'))

    return jsonify({"msg": "User not logged in"}), 401


@app.template_filter('time_ago')
def time_ago_filter(timestamp):
    current_time = datetime.utcnow()
    if isinstance(timestamp, datetime):
        comment_time = timestamp
    else:
        comment_time = datetime.utcfromtimestamp(timestamp)

    time_difference = current_time - comment_time
    seconds = time_difference.total_seconds()
    minutes = divmod(seconds, 60)[0]
    hours = divmod(minutes, 60)[0]
    days = divmod(hours, 24)[0]

    if seconds < 60:
        return f"{int(seconds)} {'second' if int(seconds) == 1 else 'seconds'} ago"
    elif minutes < 60:
        return f"{int(minutes)} {'minute' if int(minutes) == 1 else 'minutes'} ago"
    elif hours < 24:
        return f"{int(hours)} {'hour' if int(hours) == 1 else 'hours'} ago"
    else:
        return f"{int(days)} {'day' if int(days) == 1 else 'days'} ago"


@app.route("/coba1")
@login_required
def coba1():
    username = session.get("username")
    role = session.get("role")
    return render_template("coba1.html", username=username, role=role)


@app.route("/coba2")
@login_required
def coba2():
    username = session.get("username")
    role = session.get("role")
    return render_template("coba2.html", username=username, role=role)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/sign_up/check_dup", methods=["POST"])
def check_dup():
    username_receive = request.form["username_give"]
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({"result": "success", "exists": exists})


@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    name_receive = request.form["name_give"]
    tanggal_receive = request.form["tanggal_give"]
    gender_receive = request.form.get("gender_give")
    password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
        "profile_name": name_receive,
        "tanggal_name": tanggal_receive,
        "gender_name": gender_receive,
        "profile_pic_real": "profile_pics/profile_placeholder.png",
        "role": "user",
    }
    db.users.insert_one(doc)
    return jsonify({"result": "success"})


@app.route("/sign_in", methods=["POST"])
def sign_in():
    # Sign in
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )
    if result:
        random_hex = str(secrets.token_hex(8))
        session["logged_in"] = True
        session["_id"] = random_hex
        session["id_user_login"] = str(result["_id"])
        session["username"] = result["username"]
        session["role"] = result["role"]
        session["profile_pic_real"] = result["profile_pic_real"]
        return jsonify(
            {
                "result": "success",
            }
        )
    else:
        return jsonify(
            {
                "msg": "salah",
            }
        )


@app.route("/get_posts")
def get_posts():
    # data = db.artikel.find({}).sort("tanggal", -1).limit(20)
    data = db.artikel.aggregate(
        [
            {"$sample": {"size": 20}},
        ]
    )
    posts = json_util.dumps(data)
    return jsonify(
        {
            "result": "success",
            "msg": "Successful fetched all posts",
            "posts": json.loads(posts),
        }
    )


@app.route("/get_posts_side")
def get_posts_side():
    data = db.artikel.find({}).sort("tanggal", -1).limit(5)
    posts = json_util.dumps(data)
    return jsonify(
        {
            "result": "success",
            "msg": "Successful fetched all posts",
            "posts": json.loads(posts),
        }
    )


@app.route("/get_posts_isi")
def get_posts_isi():
    judul_receive = request.args.get("judul_give")
    data = db.artikel.find_one({"judul": judul_receive}, {"_id": False})
    post = json_util.dumps(data)
    return jsonify(
        {
            "result": "success",
            "msg": "Successful fetched all posts",
            "post": json.loads(post),
        }
    )

@app.route("/get_posts_shop")
def get_posts_shop():
    # data = db.artikel.find({}).sort("tanggal", -1).limit(20)
    data = db.shop.find({})
    posts = json_util.dumps(data)
    return jsonify(
        {
            "result": "success",
            "msg": "Successful fetched all posts",
            "posts": json.loads(posts),
        }
    )

@app.route('/hapus_postingan_shop', methods=['POST'])
def hapus_postingan_shop():
    id_user_receive = request.form.get("id_give")
    post_data = db.shop.find_one({'_id': ObjectId(id_user_receive)})
    if post_data:
        if 'gambar' in post_data:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'artikel', post_data['gambar'])
            if os.path.exists(file_path):
                os.remove(file_path)
    # print(id_user_receive)
    result = db.shop.delete_one({'_id': ObjectId(id_user_receive)})
    return jsonify({"result": "result"})

@app.route("/postingshop", methods=["POST"])
def postingshop():
    judul_receive = request.form.get("judul_give")
    harga_receive = request.form.get("harga_give")
    _id = session.get("_id")
    
    doc = {
        "judul": judul_receive,
        "harga": harga_receive,
    }

    if "file_give" in request.files:
        file = request.files["file_give"]
        if file.filename == '':
            return jsonify({"result": "error", "msg": "No selected file"})

        filename = secure_filename(file.filename)
        file_path = f"./static/shop/{'a'+_id+filename}"
        file_path_server = f"{filename}"
        
        file.save(file_path)
        doc["gambar"] = 'a'+_id+file_path_server
    # print(judul_receive, harga_receive, doc.get("gambar", "No image"))
    db.shop.insert_one(doc)
    return jsonify({"result": "success", "msg": "Article posted!"})



@app.route("/postingb", methods=["POST"])
def postingb():
    judul_receive = request.form.get("judul_give")
    isi_receive = request.form.get("isi_give")
    tanggal_receive = request.form.get("tanggal_give")
    _id = session.get("_id")
    
    doc = {
        "judul": judul_receive,
        "isi": isi_receive,
        "tanggal": tanggal_receive,
    }

    if "file_give" in request.files:
        file = request.files["file_give"]
        if file.filename == '':
            return jsonify({"result": "error", "msg": "No selected file"})

        filename = secure_filename(file.filename)
        file_path = f"./static/artikel/{'a'+_id+filename}"
        file_path_server = f"{filename}"
        
        file.save(file_path)
        doc["gambar"] = 'a'+_id+file_path_server

    db.artikel.insert_one(doc)

    # print(judul_receive, isi_receive, tanggal_receive, doc.get("gambar", "No image"))
    return jsonify({"result": "success", "msg": "Article posted!"})

@app.route('/hapus_postingan_artikel', methods=['POST'])
def hapus_postingan_artikel():
    id_user_receive = request.form.get("id_give")
    post_data = db.artikel.find_one({'_id': ObjectId(id_user_receive)})
    if post_data:
        if 'gambar' in post_data:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'artikel', post_data['gambar'])
            if os.path.exists(file_path):
                os.remove(file_path)
    # print(id_user_receive)
    result = db.artikel.delete_one({'_id': ObjectId(id_user_receive)})
    return jsonify({"result": "result"})

@app.route("/editprofile", methods=["POST"])
def editprofile():
    username_receive = request.form.get("username_give")
    tanggal_receive = request.form.get("tanggal_give")
    username = session.get("username")
    _id = session.get("_id")
    # print(username_receive, username, tanggal_receive)
   
    post_data = db.users.find_one({'username': username_receive})
    if post_data:
        if 'profile_pic_real' in post_data:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics', post_data['profile_pic_real'])
            if os.path.exists(file_path):
                os.remove(file_path)

    doc = {
        "username": username_receive,
        "tanggal": tanggal_receive,
    }

    if "file_give" in request.files:
        file = request.files["file_give"]
        if file.filename == '':
            return jsonify({"result": "error", "msg": "No selected file"})

        filename = secure_filename(file.filename)
        file_path = f"./static/profile_pics/{'a'+_id+filename}"
        file_path_server = f"profile_pics/{'a'+_id+filename}"
        
        file.save(file_path)
        doc["profile_pic_real"] = file_path_server
    # print(username_receive, username, tanggal_receive, doc.get("profile_pic_real", "No image"))
    db.users.update_one({'username': username}, {
        '$set': doc
    })
    return jsonify({"result": "success", "msg": "Profile updated successfully"})

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
