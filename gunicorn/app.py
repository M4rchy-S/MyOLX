from flask import Flask, redirect, url_for, render_template, request, session, jsonify
from psycopg2 import pool
from vaildation import InputValidation
from hashlib import pbkdf2_hmac
import os
from time import sleep
from math import ceil

app = Flask(__name__)

sleep(10)


# app.secret_key = "MySuper_secret_Key"
app.config['SECRET_KEY'] = "MySuper_secret_Key"
main_salt = b'SuperSecretSalt'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = '/static/images'
app.config['UPLOAD_FOLDER'] = app.root_path + UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

MAX_PAGES_PER_SEARCH = 5

# try:
#     app.config['DB_POOL'] = pool.SimpleConnectionPool(
#         1, 
#         10, 
#         user='postgres', 
#         # host='localhost', 
#         host='postgres', 
#         port='5432', 
#         database='webserver',
#         password='testpassword'
#     )
# except Exception as e:
#     @app.route('/', defaults={'path': ''})
#     @app.route('/<path:path>')
#     def catch_all(path):
#         return "<h2>Server Database is offline. Restart Server manually</h2>"
    
#     app.run()

app.config['DB_POOL'] = pool.SimpleConnectionPool(
        1, 
        10, 
        user='postgres', 
        # host='localhost', 
        host='postgres', 
        port='5432', 
        database='webserver',
        password='testpassword'
    )
    


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
        conn.rollback()
        return ""
    finally:
        if conn:
            app.config['DB_POOL'].putconn(conn)

def get_hash_password(input_password: str) -> str:
    return pbkdf2_hmac('sha256', input_password.encode('utf-8'), main_salt, 500).hex()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(Exception)
def handle_error(e):
    return f"<h3>Error 500 on server Side</h3><\br>{e}"

@app.route("/")
@app.route("/index")
def main():
    return render_template("index.html", username=session.get('name', "Your profile"))

@app.route("/search")
def search():
    #   Page
    cur_page = request.args.get('page', '1')
    try:
        cur_page = int(cur_page)
        if cur_page <= 0:
            cur_page = 1
    except Exception as e:
        redirect(url_for('main'))
    
    #   Category
    category = request.args.get('category_select', 'None')
    category_list =  ["None" ,"Electronics" ,"Pets" ,"Home_Furniture" ,"Clothing" ,"Hobbies" ,"Vehicles"]
    if category not in category_list:
        category_list = "None"

    # Location
    location = request.args.get('city_select', '') 
    city_list = [
        "All Country","Kyiv","Kharkiv","Odesa","Dnipro","Lviv","Zaporizhzhia","Kryvyi Rih",
        "Mykolaiv","Mariupol","Vinnytsia","Kherson","Poltava","Chernihiv","Cherkasy",
        "Sumy","Zhytomyr","Chernivtsi","Ivano-Frankivsk","Ternopil","Rivne","Lutsk",
        "Uzhhorod","Kropyvnytskyi" ]
        
    if location not in city_list:
        location = "All Country"
    

    #   Search text
    search_text = request.args.get('search_text', '') 

    #   Sql text

    #   Get total size
    sq_list = ["SELECT COUNT(*) FROM posts"]
    parameters = []
    if len(search_text) > 0:
        parameters.append(f"document @@ to_tsquery('{search_text}')")
    if category != "None":
        parameters.append( f"category = '{category}' " )
    if location != "All Country":
        parameters.append( f"location = '{location}' " )

    if len(parameters) > 0:
        sq_list.append( " WHERE " + " AND ".join(parameters) )

    sql_query_search = " ".join(sq_list)

    res = db_query(sql_query_search)
    if res == '':
        return redirect(url_for('handle_error'))
    
    max_pages = max(ceil(res[0][0] / MAX_PAGES_PER_SEARCH), 1)

    if cur_page > max_pages:
        cur_page = 1

    #   Get data
    sq_list = ["SELECT id,title,price,location,images  FROM posts"]
    if len(parameters) > 0:
        sq_list.append( " WHERE " + " AND ".join(parameters) )
    sq_list.append(f"ORDER BY time DESC LIMIT {MAX_PAGES_PER_SEARCH} OFFSET {(cur_page-1) * MAX_PAGES_PER_SEARCH};")
    sql_query_search = " ".join(sq_list)

    post_cards_data = db_query(sql_query_search)
    if post_cards_data == '':
        return redirect(url_for('handle_error'))
    
    post_cards_data = [list(data_line) for data_line in post_cards_data]
    for i in range(len(post_cards_data)):
        if post_cards_data[i][4] != '':
            post_cards_data[i][4] = post_cards_data[i][4].split()[0]
    
    return render_template("search.html", username=session.get('name', "Your profile"), page=cur_page, all_pages=max_pages, search_text=search_text, category_select=category, city_select=location, data_cards=post_cards_data)

@app.route("/post/<int:post_id>")
def postpage(post_id):
    results = db_query(f'SELECT posts.images, posts.description, posts.title, posts.price, posts."location", users."name", users.phone FROM posts INNER JOIN users ON posts.user_id = users.id WHERE posts.id = {post_id}')
    if results == '':
        return redirect(url_for('handle_error'))    
    elif not results:
        return redirect(url_for('error_page'))
    
    images_str = str(results[0][0]).split(" ")
    if images_str[0] == '':
        images_str.clear()

    return render_template("postpage.html", username=session.get('name', "Your profile"),images=images_str, description=results[0][1], title=results[0][2], price=results[0][3],location=results[0][4], user=results[0][5], phone=results[0][6])

@app.route("/error")
def error_page():
    return "<h2>Error 404 - Page not found</h2>"

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
        message =request.args.get('message', '')
        return render_template("create-ann.html", error_message=message,  token=session.get('csrf_token', ''))
    else:
        return redirect(url_for('sign_in'))

@app.route("/settings")
def settings():
    if session:
        message = request.args.get('message', '')
        return render_template("settings.html", error_message=message, token=session.get('csrf_token', ''))
    else:
        return redirect(url_for('sign_in'))

@app.route("/mylist")
def ann_list():
    if session:
        res = db_query(f"SELECT posts.title, posts.price, posts.id FROM posts INNER JOIN users ON posts.user_id = users.id WHERE users.email = '{session['email']}'")
        if res == '':
            return redirect(url_for('handle_error'))

        return render_template("ann-list.html", lines_data=res, token=session.get('csrf_token', ''))
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
            return redirect(url_for('sign_up', message="Phone number or Email are already busy"))
        
        session['name'] = user_name 
        session['email'] = mail
        session['password'] = password
        session['phone'] = phone
        session['csrf_token'] = os.urandom(16).hex()
        return redirect(url_for('ann_list')) 
    else:
        return redirect(url_for('main'))

@app.route("/login", methods=['POST'])
def enter_account():
    if request.method == 'POST':

        email = request.form['email']
        password = get_hash_password(request.form['password'])
        
        res = db_query(f"SELECT users.\"name\", users.email, users.\"password\", users.phone FROM users WHERE users.email = '{email}' AND users.\"password\" = '{password}'")
        if res:
            session['name'] = res[0][0]
            session['email'] = res[0][1]
            session['password'] = res[0][2]
            session['phone'] = res[0][3]
            session['csrf_token'] = os.urandom(16).hex()
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

@app.route("/change-password", methods=['POST'])
def change_password():
    if session and request.method == 'POST' and request.form.get('csrf_token', '') == session['csrf_token']:
        if get_hash_password(request.form['old_password']) == session['password']:
            iv = InputValidation()
            iv.validate_password(request.form['new_password'])
            if iv.count() == 0:
                new_password = get_hash_password(request.form['new_password'])
                res = db_query(f"UPDATE users SET password = '{new_password}' WHERE users.email = '{session['email']}'")
                if res:
                    session['password'] = new_password
                    return redirect(url_for('settings'))
                elif res == '':
                    return redirect(url_for('handle_error'))      
                else:
                    return redirect(url_for('settings', message="Error"))
            else:
                return redirect(url_for('settings', message="Wrong new password requirements"))
        else:
            return redirect(url_for('settings', message="Wrong old password"))
        
    else:
        return redirect(url_for('main'))

@app.route("/change-phone", methods=['POST'])
def change_phone():
    if session and request.method == 'POST' and request.form.get('csrf_token', '') == session['csrf_token']:
        new_phone_number = request.form['new_phone']
        iv = InputValidation()
        phone_number = iv.validate_phone(new_phone_number)
        if iv.count() > 0:
            return redirect(url_for('settings', message=iv.getfirst()))
        else:
            res = db_query(f"SELECT users.phone FROM users WHERE users.phone = '+{phone_number}'")
            if len(res) == 0:
                #   UPDATE users SET phone = '+36' WHERE users.email = 'testsubject@mail2.com'
                res = db_query(f"UPDATE users SET phone = '+{phone_number}' WHERE users.email = '{session['email']}'")
                if res == '':
                    return redirect(url_for('handle_error'))
                else:  
                    return redirect(url_for('settings'))
            elif len(res) > 0:
                return redirect(url_for('settings', message="This phone number is already busy"))
            elif res == '':
                return redirect(url_for('handle_error'))  
            else:
                return redirect(url_for('settings', message="Error"))
    else:
        return redirect(url_for('main'))

@app.route("/delete-account", methods=['POST'])
def delete_account():
    if session and request.method == 'POST' and request.form.get('csrf_token', '') == session['csrf_token']:
        res = db_query(f"SELECT id FROM users WHERE email = '{session['email']}'")
        if res == '':
            return redirect(url_for('handle_error')) 
        
        user_id = res[0][0]

        res = db_query(f"DELETE FROM posts WHERE user_id = {user_id}")
        if res == '':
            return redirect(url_for('handle_error'))

        res = db_query(f"DELETE FROM users WHERE email = '{session['email']}'")
        if res == '':
            return redirect(url_for('handle_error')) 
        else:
            return redirect(url_for('log_out'))
    else:
        return redirect(url_for('main'))

@app.route("/create-new-ann", methods=['POST'])    
def create_new_ann():
    if request.method == 'POST' and session and request.form.get('csrf_token', '') == session['csrf_token']:
        #   form data validation
        res = db_query(f"SELECT COUNT(*) FROM posts INNER JOIN users ON posts.user_id = users.id WHERE users.email = '{session['email']}'")
        if res == '':
            return redirect(url_for('handle_error'))  
        
        if(res[0][0] >= 5):
            return redirect(url_for('create_ann', message="Your already have 5 posts"))
        
        #   title
        if len( request.form.get('title', '') ) <= 3:
            return redirect(url_for('create_ann', message="Small title"))
        
        #   number
        try:
            price = float( request.form.get('price', '') )
            if price <= 0:
                raise Exception
        except Exception as e:
            return redirect(url_for('create_ann', message="Bad Price"))
        
        #   Location (city)
        city_list = [
            "All Country","Kyiv","Kharkiv","Odesa","Dnipro","Lviv","Zaporizhzhia","Kryvyi Rih",
            "Mykolaiv","Mariupol","Vinnytsia","Kherson","Poltava","Chernihiv","Cherkasy",
            "Sumy","Zhytomyr","Chernivtsi","Ivano-Frankivsk","Ternopil","Rivne","Lutsk",
            "Uzhhorod","Kropyvnytskyi" ]
        
        location = request.form.get('city-select', '')
        if location not in city_list:
            location = "All Country"

        #   Category
        category_list =  ["None" ,"Electronics" ,"Pets" ,"Home_Furniture" ,"Clothing" ,"Hobbies" ,"Vehicles"]
        category = request.form.get('category-select', '')
        if category not in category_list:
            category_list = "None"

        #   Desc
        description = request.form.get('description', "")
        if len( description ) <= 10 or len( description ) >= 50000:
            return redirect(url_for('create_ann', message="Bad description"))

        #   Files data validation
        file_lists = []
        if 'images[]' in request.files:
            for file in request.files.getlist("images[]"):
                if file.filename == '':
                    continue
                
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)

                if file_size >= 56623104:
                    return redirect(url_for('create_ann', message="File Size is too big (54 Mb is max)"))

                if file and allowed_file(file.filename):
                    file.filename = os.urandom(12).hex() + '.' + file.filename.rsplit('.', 1)[1].lower()
                    file.save( os.path.join(app.config['UPLOAD_FOLDER'], file.filename) )
                    file_lists.append( file.filename )
        
        res = db_query(f"SELECT id FROM users WHERE email = '{session['email']}'")
        if res == '':
            return redirect(url_for('handle_error')) 
        
        user_id = res[0][0]
        file_lists = " ".join(file_lists)


        #   INSERT INTO posts (user_id, title, price, images, description, location, category, document) VALUES (4, 'Test title', 777, 'cat1.jpg', 'Description about houses', 'All Country', 'None', to_tsvector('Test title' || ' ' || 'Description about houses'));

        res = db_query(f"INSERT INTO posts (user_id, title, price, images, description, location, category, document) VALUES ({user_id}, '{request.form.get('title', 'title_sample')}', {price}, '{file_lists}', '{description}', '{location}', '{category}', to_tsvector('{request.form.get('title', 'title_sample')}' || ' ' || '{description}'))")
        if res == '':
            return redirect(url_for('handle_error')) 
        
        return redirect(url_for('ann_list'))
    else:
        return redirect(url_for('main'))
    
@app.route("/delete-ann", methods=['GET'])
def delete_ann():
    if request.method == 'GET' and session and request.args.get('csrf_token', '') == session['csrf_token']:
        post_id = request.args.get('post_id', '')
        if post_id == '':
            return redirect(url_for('ann_list'))
        
        res = db_query(f"SELECT users.email FROM posts INNER JOIN users ON posts.user_id = users.id WHERE posts.id = {post_id};")
        if res == '':
            return redirect(url_for('handle_error'))
        
        user_email = res[0][0]

        if user_email == session['email']:
            res = db_query(f"DELETE FROM posts WHERE id = {post_id};")
            if res == '':
                return redirect(url_for('handle_error'))

            return redirect(url_for('ann_list'))
        else:
            redirect(url_for('main'))


    else:
        redirect(url_for('main'))

@app.route("/api/search")
def api_search():
    #   Page
    cur_page = request.args.get('page', '1')
    try:
        cur_page = int(cur_page)
        if cur_page <= 0:
            cur_page = 1
    except Exception as e:
        redirect(url_for('main'))
    
    #   Category
    category = request.args.get('category_select', 'None')
    category_list =  ["None" ,"Electronics" ,"Pets" ,"Home_Furniture" ,"Clothing" ,"Hobbies" ,"Vehicles"]
    if category not in category_list:
        category_list = "None"

    # Location
    location = request.args.get('city_select', '') 
    city_list = [
        "All Country","Kyiv","Kharkiv","Odesa","Dnipro","Lviv","Zaporizhzhia","Kryvyi Rih",
        "Mykolaiv","Mariupol","Vinnytsia","Kherson","Poltava","Chernihiv","Cherkasy",
        "Sumy","Zhytomyr","Chernivtsi","Ivano-Frankivsk","Ternopil","Rivne","Lutsk",
        "Uzhhorod","Kropyvnytskyi" ]
        
    if location not in city_list:
        location = "All Country"
    

    #   Search text
    search_text = request.args.get('search_text', '') 

    #   Sql text

    #   Get total size
    sq_list = ["SELECT COUNT(*) FROM posts"]
    parameters = []
    if len(search_text) > 0:
        parameters.append(f"document @@ to_tsquery('{search_text}')")
    if category != "None":
        parameters.append( f"category = '{category}' " )
    if location != "All Country":
        parameters.append( f"location = '{location}' " )

    if len(parameters) > 0:
        sq_list.append( " WHERE " + " AND ".join(parameters) )

    sql_query_search = " ".join(sq_list)

    res = db_query(sql_query_search)
    if res == '':
        return redirect(url_for('handle_error'))
    
    max_pages = max(ceil(res[0][0] / MAX_PAGES_PER_SEARCH), 1)

    if cur_page > max_pages:
        cur_page = 1

    #   Get data
    sq_list = ["SELECT id,title,price,location,images  FROM posts"]
    if len(parameters) > 0:
        sq_list.append( " WHERE " + " AND ".join(parameters) )
    sq_list.append(f"ORDER BY time DESC LIMIT {MAX_PAGES_PER_SEARCH} OFFSET {(cur_page-1) * MAX_PAGES_PER_SEARCH};")
    sql_query_search = " ".join(sq_list)

    post_cards_data = db_query(sql_query_search)
    if post_cards_data == '':
        return redirect(url_for('handle_error'))
    
    post_cards_data = [list(data_line) for data_line in post_cards_data]
    for i in range(len(post_cards_data)):
        if post_cards_data[i][4] != '':
            post_cards_data[i][4] = post_cards_data[i][4].split()[0]
    
    # return render_template("search.html", username=session.get('name', "Your profile"), page=cur_page, all_pages=max_pages, search_text=search_text, category_select=category, city_select=location, data_cards=post_cards_data)
    return jsonify({
        'page': cur_page,
        'all_pages':max_pages,
        'search_text':search_text,
        'category_select':category,
        'city_select': location,
        'data_cards': post_cards_data
    })

if __name__ == "__main__":
    session.clear()
    app.run(host='0.0.0.0', port=8000)