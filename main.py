from flask import Flask, redirect, url_for, render_template, make_response, request, session
from psycopg2 import pool
import form_validation

app = Flask(__name__)

# app.config['SECRET_KEY'] = "MySuper_secret_Key"
app.secret_key = "MySuper_secret_Key"

app.config['DB_POOL'] = pool.SimpleConnectionPool(
    1, 
    10, 
    user='postgres', 
    host='localhost', 
    port='5432', 
    database='webserver'
)

def db_query(query: str) -> str:
    conn = None
    try:
        conn = app.config['DB_POOL'].getconn()
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print("[ERROR] Query database error acquired")
        return ""
    finally:
        if conn:
            app.config['DB_POOL'].putconn(conn)


@app.route("/")
@app.route("/index")
def main():
    return render_template("index.html")

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/<int:post_id>")
def postpage(post_id):
    results = db_query(f'SELECT posts.images, posts.description, posts.title, posts.price, posts."location", users."name", users.phone FROM posts INNER JOIN users ON posts.user_id = users.id WHERE posts.id = {post_id}')
    print(f"[DEBUG] {results=}")
    if not results:
        return redirect(url_for('error_page'))

    return render_template("postpage.html", images=str(results[0][0]).split(" "), description=results[0][1], title=results[0][2], price=results[0][3],location=results[0][4], user=results[0][5], phone=results[0][6])

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
        return render_template("sign-up.html")
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
    print(f'{request=}')
    return "created"

@app.route("/login", methods=['POST'])
def enter_account():
    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']
        
        res = db_query(f"SELECT users.id FROM users WHERE users.email = '{email}' AND users.\"password\" = '{password}'")
        if res:
            session['email'] = email
            return redirect(url_for('ann_list'))        
        else:
            return redirect(url_for('sign_in', message="Incorrect data") )
    
    else:
        return redirect(url_for('main'))
    
@app.route("/log-out")
def log_out():
    session.clear()
    return redirect(url_for('main'))
    


if __name__ == "__main__":
    app.run(debug=False)