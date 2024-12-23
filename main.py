from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def main():
    return render_template("index.html")

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/postpage")
def postpage():
    return render_template("postpage.html")

@app.route("/sign-in")
def sign_in():
    return render_template("sign-in.html")

@app.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")

@app.route("/create-ann")
def create_ann():
    return render_template("create-ann.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/mylist")
def ann_list():
    return render_template("ann-list.html")

@app.route("/create_account", methods=['POST'])
def create_account():
    return "created"

@app.route("/login", methods=['POST'])
def enter_account():
    return "entered"


if __name__ == "__main__":
    app.run(debug=True)