
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


@app.route("/cards/all")
def all_cards():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    sort = request.args.get("sort", "newest")
    if sort not in ("newest","oldest"):
        sort = "newest"
    #validate the page size
    allowed_size = (10, 25, 50)
    try:
        per_page = int(request.args.get("per_page", 10))
    except (TypeError, ValueError):
        per_page = 10
    if per_page not in allowed_size:
        per_page = 10
    query = Card.query.filter_by(user_id=user_id)
    #use card IDs as a temporary proxy
    if sort == "oldest":
        query = query.order_by(Card.id.asc())
    else:
        query = query.order_by(Card.id.desc())
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    cards_page = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    card_sets = CardSet.query.filter_by(
         user_id=session["user_id"]
    ).all()
    return render_template(
        "home.html",
        cards=cards_page.items,
        cards_page=cards_page,
        card_sets=card_sets,
        sort=sort,
        per_page=per_page   
    )
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        _name = request.form.get("username", "").strip()
        _word = request.form.get("password", "")
        _user = User.query.filter_by(username=_name).first()
        if ( _user and check_password_hash(_user.password_hash, _word)):
            session.clear()
            session["user"] = _user.username
            session["user_id"] = _user.id
            return redirect(url_for("all_cards"))
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

