
import yt_dlp
from urllib.parse import urlparse
##################################################################################
from flask import (                                                              #       
        Flask, request, render_template, session,                                #
        redirect, url_for, abort                                                 #
    )                                                                            #
from flask_sqlalchemy import SQLAlchemy                                          #
from sqlalchemy import or_                                                       #
from werkzeug.security import (                                                  #
        generate_password_hash, check_password_hash                              #
    )                                                                            #
##################################################################################
app = Flask(__name__)                                                           ##
app.secret_key = "my-secret-key"                                                ##
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"                    ##
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False                            ##
db = SQLAlchemy(app)                                                            ##
##################################################################################

card_set_cards = db.Table (
    "card_set_cards",
    db.Column("card_id", db.Integer, db.ForeignKey("cards.id"), primary_key=True),
    db.Column("set_id", db.Integer, db.ForeignKey("card_sets.id"), primary_key=True)
)

class User(db.Model):
    __tablename__ = "pot_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    cards = db.relationship("Card", backref="owner")
    card_sets = db.relationship("CardSet", backref="owner")

class Card(db.Model):
    __tablename__ = "cards"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200))
    answer = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("pot_users.id"), nullable=False)

class CardSet(db.Model):
    __tablename__ = "card_sets"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
    db.Integer,
    db.ForeignKey("pot_users.id"),
    nullable=False
    )
    # NEW: A set can optionally belong to another set.
    parent_id = db.Column(
    db.Integer,
    db.ForeignKey("card_sets.id"),
    nullable=True
    )
    # Existing relationship: cards can belong to multiple sets.
    cards = db.relationship(
    "Card",
    secondary=card_set_cards,
    backref=db.backref("sets", lazy="select")
    )
    # NEW: Access this set's parent.
    parent = db.relationship(
    "CardSet",
    remote_side=[id],
    back_populates="children"
    )
    # NEW: Access this set's immediate children.
    children = db.relationship(
    "CardSet",
    back_populates="parent"
    )
###################################################################################
with app.app_context():
    db.create_all()
###################################################################################
###################################################################################

def get_youtube_title(link):
    # Parse and validate the URL
    parsed_url = urlparse(link)
    domain = parsed_url.netloc.lower().split(":")[0]

    valid_domains = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }

    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme.")

    if domain not in valid_domains:
        raise ValueError("This is not a YouTube URL.")

    # Extract video information without downloading it
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(link, download=False)

        if not info or not info.get("title"):
            raise ValueError("Could not retrieve the video title.")

        return info["title"]

    except yt_dlp.utils.DownloadError as error:
        raise ValueError(
            "The YouTube video is invalid, unavailable, "
            "or could not be accessed."
        ) from error

@app.route("/data", methods=["GET","POST"])
def collect_data(): 
    if "user_id" not in session:
        return redirect(url_for("login"))
    title = None
    error = None
    if request.method=="POST":
        link = request.form.get("q", "").strip()
        try:
            title = get_youtube_title(link)
        except ValueError as e:
            error = str(e)
    
    return render_template(
            "home.html",
            query=title,
            error=error
        )
@app.route("/profile")
def user_info(): 
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("user_prof.html")
@app.route("/cards/mine")
def all_my_cards():
    if "user_id" not in session:
        return redirect(url_for("login")) 
    return render_template("home.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u_name = request.form.get("username", "").strip()
        p_word = request.form.get("password", "")
        the_user = User.query.filter_by(username=u_name).first()
        if ( the_user and check_password_hash(the_user.password_hash, p_word)):
            session.clear()
            session["user"] = the_user.username
            session["user_id"] = the_user.id
            return redirect(url_for("all_my_cards"))
        else:
            return render_template("login.html", error="Invalid username or password")
    else:
        return redirect(url_for("home"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        _name = request.form.get("username", "").strip()
        _word = request.form.get("password", "")
        if not _word or not _name:
            return render_template(
                    "register.html",
                    error="Please enter both a username and password."
                )
        existing_user = User.query.filter_by(username=_name).first()
        if existing_user:
            return render_template(
                    "register.html",
                    error="That username is already taken."
                    )
        _word_hash = generate_password_hash(_word)
        pappi = User(username=_name, password_hash=_word_hash)
        db.session.add(pappi)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")
@app.route("/")
def home():
    if "user_id" not in session:
        return render_template("login.html")
    else:
        session.clear()
        return render_template("login.html")
if __name__ == '__main__':
    app.run(debug=True)
###################################################################################
###################################################################################

