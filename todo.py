from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps 

app = Flask(__name__) 

#Kullanıcı Giriş Kontrolü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfaya Erişmek İçin Giriş Yapmalısınız")
            return redirect(url_for("login"))
    return decorated_function

#Register Form
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.DataRequired()])
    username = StringField("Kullanıcı Adı",validators=[validators.DataRequired()])
    email = StringField("Mail",validators=[validators.Email(message="Doğru e-posta giriniz"),validators.DataRequired()])
    password = PasswordField("Şifre",validators=[
        validators.EqualTo(fieldname="confirm",message="Parola uyuşmuyor")
    ])
    confirm = PasswordField("Şifrenizi Tekrar Girin")

#Login Form
class LoginForm(Form):
    username = StringField("Kullanıcı Adı",validators=[validators.data_required()])
    password = PasswordField("Şifre",validators=[validators.data_required()])

app.secret_key="blog" # flash mesaj için

# Veritabanı
app.config["MYSQL_HOST"] ="localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "todo"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)


@app.route("/")
def index():
    return redirect(url_for("todo"))
@app.route("/todo")
def todo():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM todo WHERE author = %s"
    cursor.execute(sorgu,(session["username"],))
    todos = cursor.fetchall()
    return render_template("todo.html",todos=todos)

@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        cursor = mysql.connection.cursor()
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        k_sorgu = "Select * FROM users WHERE username = %s " #Kullanıcı Adı Sorgusu
        kontrol =cursor.execute(k_sorgu,(username,))
        m_sorgu = "Select * FROM users WHERE email = %s " #Mail Sorgusu
        if kontrol > 0:
            flash("Kullanıcı adı kullanılıyor","danger")
            return redirect(url_for("register"))
        kontrol = cursor.execute(m_sorgu,(email,))
        if kontrol > 0:
            flash("Mail Kullanılıyor","danger")
            return redirect(url_for("register"))
        sorgu = "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt Olundu")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)

@app.route("/login",methods=["GET","POST"])
def login():
    cursor = mysql.connection.cursor()
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password = form.password.data
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password,real_password):
                 flash("Başarıyla Giriş Yaptınız","success")
                 session["logged_in"] = True
                 session["username"] = username
                 return redirect(url_for("todo"))
            else:
                flash("Şifrenizi Yanlış Girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Kullanıcı Adını Yanlış Girdiniz","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form=form)

#Çıkış İşlemi
@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış Yaptınız","success")
    return redirect(url_for("index"))

#Todo Ekleme
@app.route("/add",methods=["POST"])
def add():
    title = request.form.get("title")
    sorgu = "INSERT INTO todo(title, complete, author)VALUES (%s,%s,%s)"
    cursor = mysql.connection.cursor()
    cursor.execute(sorgu,(title,False,session["username"]))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("index"))

#Durum Güncelleme
@app.route("/update/<string:id>")
def update(id):
    sorgu = "Select * FROM todo WHERE id = %s"
    cursor = mysql.connection.cursor()
    cursor.execute(sorgu,(id,))
    data = cursor.fetchone()
    if data["complete"] == False:
        sorgu2 = "UPDATE todo SET complete = %s WHERE id = %s"
        cursor.execute(sorgu2,(True,id))
        mysql.connection.commit()
        return redirect(url_for("todo"))
    else:
        sorgu3 = "UPDATE todo SET complete = %s WHERE id = %s"
        cursor.execute(sorgu3,(False,id))
        mysql.connection.commit()
        return redirect(url_for("todo"))

#todo silme
@app.route("/delete/<string:id>")
def delete(id):
    sorgu = "DELETE FROM todo WHERE id = %s"
    cursor = mysql.connection.cursor()
    cursor.execute(sorgu,(id,))
    mysql.connection.commit()
    return redirect(url_for("todo"))

if __name__ == "__main__":
    app.run(debug=True) 