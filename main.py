from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests

endpoint = "https://api.themoviedb.org/3/search/movie"
api_key = ""

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)


class AddForm(FlaskForm):
    title = StringField(label="Title", validators=[DataRequired()])
    submit = SubmitField("Submit")


class UpdateForm(FlaskForm):
    rating = FloatField(label="New Rating", validators=[DataRequired()])
    review = StringField(label="New Review", validators=[DataRequired()])
    submit = SubmitField("Submit")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, unique=True, nullable=False)
    review = db.Column(db.String(80), unique=True, nullable=False)
    img_url = db.Column(db.String(200), unique=True, nullable=False)


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<int:idv>", methods=["GET", "POST"])
def edit(idv):
    update_form = UpdateForm()
    if update_form.validate_on_submit():
        rating = update_form.rating.data
        review = update_form.review.data
        print(rating, review)
        movie_to_update = Movie.query.get(idv)
        movie_to_update.rating = rating
        movie_to_update.review = review
        db.session.commit()
        all_movies = Movie.query.order_by(Movie.rating).all()
        for i in range(len(all_movies)):
            all_movies[i].ranking = len(all_movies) - i
        db.session.commit()
        return render_template("index.html", movies=Movie.query.order_by(Movie.rating).all())
    return render_template("edit.html", form=update_form, title=Movie.query.get(idv).title)


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        movies = requests.get(url=endpoint, params={
            "api_key": api_key,
            "query": add_form.title.data
        }).json()['results']
        return render_template("select.html", options=movies)
    return render_template("add.html", form=add_form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    ep = "https://api.themoviedb.org/3/movie/" + movie_id
    data = requests.get(url=ep, params={
        "api_key": api_key
    }).json()
    new_movie = Movie(
        title=data["original_title"],
        year=int(data['release_date'][0:4]),
        description=data['overview'],
        rating=float(data['vote_average']),
        ranking=1,
        review="lorem ipsum2",
        img_url="https://image.tmdb.org/t/p/w500/" + data['backdrop_path']
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', idv=Movie.query.filter_by(title=data['original_title']).first().id))


@app.route('/delete/<int:idv>')
def delete(idv):
    db.session.delete(Movie.query.get(idv))
    db.session.commit()
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=Movie.query.order_by(Movie.rating).all())


if __name__ == '__main__':
    app.run(debug=True)
