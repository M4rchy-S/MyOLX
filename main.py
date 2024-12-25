from flask import Flask, redirect, url_for, render_template, request, session
from psycopg2 import pool
from vaildation import InputValidation
from hashlib import pbkdf2_hmac

app = Flask(__name__)

app.secret_key = "MySuper_secret_Key"
main_salt = b'SuperSecretSalt'

try:
    app.config['DB_POOL'] = pool.SimpleConnectionPool(
        1, 
        10, 
        user='postgres', 
        host='localhost', 
        port='5432', 
        database='webserver'
    )
except Exception as e:
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return "<h2>Server Database is offline. Restart Server manually</h2>"
    
    app.run()
    


def db_query(query: str) -> str:
    conn = None
    try:
        conn = app.config['DB_POOL'].getconn()
        cur = conn.cursor()
        cur.execute(query)
        if query.split()[0] == 'SELECT':
            rows = cur.fetchall()
        else:
            rows = "+"
        # try:
        #     rows = cur.fetchall()
        # except Exception as e:
        #     rows = " "
        conn.commit()
        return rows
    except Exception as e:
        print("[ERROR] Query database error acquired")
        return ""
    finally:
        if conn:
            app.config['DB_POOL'].putconn(conn)

def get_hash_password(input_password: str) -> str:
    return pbkdf2_hmac('sha256', input_password.encode('utf-8'), main_salt, 500).hex()

@app.errorhandler(Exception)
def handle_error(e):
    return "<h3>Error 500 on server Side</h3>"

@app.route("/")
@app.route("/index")
def main():
    return render_template("index.html", username=session.get('name', "Your profile"))

@app.route("/search")
def search():
    return render_template("search.html", username=session.get('name', "Your profile"))

@app.route("/<int:post_id>")
def postpage(post_id):
    results = db_query(f'SELECT posts.images, posts.description, posts.title, posts.price, posts."location", users."name", users.phone FROM posts INNER JOIN users ON posts.user_id = users.id WHERE posts.id = {post_id}')
    print(f"[DEBUG] {results=}")
    if results == '':
        return redirect(url_for('handle_error'))    
    elif not results:
        return redirect(url_for('error_page'))

    return render_template("postpage.html", username=session.get('name', "Your profile"),images=str(results[0][0]).split(" "), description=results[0][1], title=results[0][2], price=results[0][3],location=results[0][4], user=results[0][5], phone=results[0][6])

@app.route("/error")
def error_page():
    return "<h2>Error 404</h2>"

@app.route("/sign-in")
def sign_in():
    if not session:
        message = request.args.get('message', '')
        return render_template("sign-in.html", error_message=message)
    else:
        return redirect(url_for('main'))
    

@app.route("/sign-up")
def sign_up():
    if not session:
        message = request.args.get('message', '')
        return render_template("sign-up.html", error_message=message)
    else:
        return redirect(url_for('main'))

@app.route("/create-ann")
def create_ann():
    if session:
        return render_template("create-ann.html")
    else:
        return redirect(url_for('sign_in'))

@app.route("/settings")
def settings():
    if session:
        return render_template("settings.html")
    else:
        return redirect(url_for('sign_in'))

@app.route("/mylist")
def ann_list():
    if session:
        return render_template("ann-list.html")
    else:
        return redirect(url_for('sign_in'))

#       Main Utility URL Requests
@app.route("/create_account", methods=['POST'])
def create_account():
    if request.method == 'POST':
        iv = InputValidation()
        mail = iv.validate_mail( request.form['mail'] )
        password = get_hash_password( iv.validate_password( request.form['password'] ) )
        user_name = iv.validate_name( request.form['user_name'] )
        phone = iv.validate_phone( request.form['phone'] )

        if iv.count() > 0:
            return redirect( url_for('sign_up', message=iv.getfirst()) )
        
        res = db_query(f"INSERT INTO users (name, phone, email, password) VALUES ('{user_name}', '+{phone}', '{mail}', '{password}')")
        if res == '':
            return redirect(url_for('handle_error'))
        
        session['name'] = user_name 
        return redirect(url_for('ann_list')) 
    else:
        return redirect(url_for('main'))

@app.route("/login", methods=['POST'])
def enter_account():
    if request.method == 'POST':

        email = request.form['email']
        # password = pbkdf2_hmac('sha256', request.form['password'].encode('utf-8'), b'SuperSecretSalt', 500).hex()
        password = get_hash_password(request.form['password'])
        
        res = db_query(f"SELECT users.\"name\" FROM users WHERE users.email = '{email}' AND users.\"password\" = '{password}'")
        if res:
            session['name'] = res[0][0]
            return redirect(url_for('ann_list'))  
        elif res == '':
            return redirect(url_for('handle_error'))      
        else:
            return redirect(url_for('sign_in', message="Incorrect data") )
    
    else:
        return redirect(url_for('main'))
    
@app.route("/log-out")
def log_out():
    session.clear()
    return redirect(url_for('main'))
    


if __name__ == "__main__":
    app.run(debug=True)