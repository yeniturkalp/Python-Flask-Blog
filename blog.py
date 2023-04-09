from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from functools import wraps
from passlib.handlers.sha2_crypt import sha256_crypt
# import mysql.connector

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))

    return decorated_function

# user login WTF formatında yazılmıştır
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)]) # min 4 max 25 karakterli bir isim soy isim ister
    username = StringField("Kullanıcı Adı",validators=[validators.length(min=3,max=25)]) # min 3 max 25 karakterli bir isim kullanıcı adı ister
    email = StringField("E-mail Adresiniz",validators=[validators.Email(message="e-postanız uygun formatta deği!!")])
     # girilen değerin e posta formatına uygun olup olmadığını kontrol eder eğer formata uygun değilse uyarı mesajı yollar
    # İki parola ister. EqualTo girilen iki şifreyi karşılaştırır eğer benzerlik yok ise hata mesajı verir
    password = PasswordField("Parola:", validators=[validators.DataRequired(message="LÜtfen bir parola belirleyin"), 
    validators.EqualTo(fieldname="confirm", message="Parolanız uyuşmuyor!!")])
    confirm = PasswordField("Parolayı Doğrulayın") # ikinci şifre alanı bu alan ile karşılaştırma yapılır.

class LoginForm(Form):
    username = StringField("Kullanıcı adı")
    password = PasswordField("Şifre")
app = Flask(__name__)
app.secret_key = "myblog"

#flask ile mysql config
app.config["MYSQL_HOST"] = "localhost"
 #veri tabanının nerede çalıştığını belirtir yani bilgisayarımızda çalıştığını belirtiyoruz.
app.config["MYSQL_NAME"] = "root" #mysql kullanıcı adı yazılır.(kurulurken root ismi ile default olarak kuruludu)
app.config["MYSQL_PASSWORD"] = "" #default olarak şifresiz kurulduğu için boş bırakıyoruz
app.config["MYSQL_DB"] = "myblog" #veri tabanına projemizi kurduğumuz ismi yazıyoruz
app.config["MYSQL_CURSORCLASS"] = "DictCursor" # veri tabanında bulunan verileri sözlük yapısı formatında çekmemizi sağlar.
app.config['DEBUG'] = True
mysql = MySQL(app) #nesne oluşturuyoruz. Flask ile mysql arasında bağ tamamen kurulmuş oluyor.


@app.route("/") # ana dizine yönlendirme yapar
def index():
    return render_template("index.html")


#about page
@app.route("/about")
def about():
    return render_template("about.html")
#dashboard page
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author= %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    return render_template("dashboard.html")
#register / kayıt olma 
@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate(): #kullanıcı kayıt olursa çalışır
        name =form.name.data
        username = form.username.data
        email = form.email.data
        password =sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        #aynı mail adresi ile kayıt olmayı engelleyen
        sorgu2 = "Select * from users where email = %s"
        result = cursor.execute(sorgu2,(email,))
        #aynı username ile kayıt olamyı engelleyen sorgu
        sorgu3 = "Select * from users where username = %s"
        result2 = cursor.execute(sorgu3,(username,))

        if result >0:
            flash("Mail adresi boşta değil. Lütfen farklı bir mail adresi yazın...","danger")
            return redirect(url_for("register"))
        elif result2 == 1:
            flash("Bu kullanıcı adı dolu. Lütfen farklı bir kullanıcı adı girin...","danger")
            return redirect(url_for("register"))   
        else:
            sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
            cursor.execute(sorgu,(name,email,username,password))
            mysql.connection.commit()
            cursor.close()
            flash("Başarılı şekilde kayıt oldunuz..","success")
            return redirect(url_for("login"))
    else:
         return render_template("register.html",form = form) #kayıt olmak için sayfayı çağırırsa veya o alana giriş yaparsa çalışır

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("eror.html")
    

#login page
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,)) 
        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Hoş geldin {} ".format(username),"success")
                session["logged_in"] = True
                session["username"]= username

                return redirect(url_for("index"))
            else:
                flash("Yanlış bir parola girdiniz..","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","warning")
    return render_template("login.html", form=form)


#article detail

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

#logout 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


#add article
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate(): #kullanıcı kayıt olursa çalışır
        title =form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Başarılı şekilde makaleyi kaydettiniz..","success")
        return redirect(url_for("dashboard"))    
    return render_template("addarticle.html",form=form)

#delete user
# @app.route("/userdelete/<int:id>",methods=["POST"])
# @login_required
# def userdelete(id):
#     if request.method == "POST":
#         cursor = mysql.connection.cursor()
#         sorgu2 = "DELETE FROM `users` WHERE `users`.`%s`"
#         cursor.execute(sorgu2,(id,))
#         mysql.connection.commit()
#         cursor.close()
#         flash("Kaydınız başarılı şekilde silinmiştir.. Elveda güzel insan..","warning")
#         return redirect(url_for("index"))
#     else:
#         flash("Böyle bir şeye yetkiniz yok!","danger")
#         return render_template("login.html")
    
# @app.route('/userdelete/<string:id>', methods=['POST'])
# def delete_user(id):
#     # Veritabanına bağlanma
#     cursor = mysql.connection.cursor()

#     # Kullanıcı silme sorgusu
#     sql = "DELETE FROM users WHERE id = %s"

#     # Sorguyu çalıştırma
#     cursor.execute(sql, (id,))

#     # Veritabanındaki değişiklikleri kaydetme
#     mysql.connection.commit()

#     # Kullanıcıya bir mesaj gönderme
#     flash("Silindiniz","success")
# article delete                             
@app.route("/delete/<string:id>")
@login_required #giriş yapmayan kullanıcı silme işlemi yapamaz
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))
    
    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        # cursor.execute('SET @newid=0')
        # cursor.execute('UPDATE articles SET id = (@newid:=@newid+1) ORDER BY id;')
        # cursor.execute('ALTER TABLE articles AUTO_INCRMENT = id')
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Bu yazı için böyle bir yetkiniz yok veya zaten yazı yok", "danger")
        return redirect(url_for("index"))

# article update
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where author = %s and id =%s"
        result = cursor.execute(sorgu,(session["username"],id))
        if result == 0:
            flash("Yazınız bulunmamaktadır..","warning")
            return redirect(url_for("index"))
        else:
           article = cursor.fetchone()
           form = ArticleForm()
           form.title.data = article["title"]
           form.content.data = article["content"]
           return render_template("update.html",form=form)
    else:
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s, content =%s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Yazınız başalarılı şekilde güncellendi..","success")
        return redirect(url_for("dashboard"))
        
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.length(min=5,max=40)])
    content = TextAreaField("Makale İçeriği", validators=[validators.length(min=10,)])
# Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for("index"))
   else:
       keyword = request.form.get("keyword")

       cursor = mysql.connection.cursor()

       sorgu = "Select * from articles where title like '%" + keyword +"%'"

       result = cursor.execute(sorgu)

       if result == 0:
           flash("Aranan kelimeye uygun yazı bulunamadı...","danger")
           return redirect(url_for("articles"))
       else:
           articles = cursor.fetchall()

           return render_template("articles.html",articles = articles)
       

if __name__ == "__main__": #terminalden çalıştırıp çalıştırılmadığını kontrol eder  
    app.run(debug=True)


