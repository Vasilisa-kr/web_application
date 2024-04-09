from flask import Flask, url_for, redirect, render_template, request, abort
from forms.form import LoginForm, RegisterForm, QuestionsForm, AnswersForm
from data import db_session
from data.questions import Questions
from data.users import User
from data.answer import Answers
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        questions = db_sess.query(Questions).filter(
            (Questions.user == current_user) | (Questions.is_private != True))
    else:
        questions = db_sess.query(Questions).filter(Questions.is_private != True)
    return render_template("index.html", questions=questions)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', form=form)


@app.route('/questions', methods=['GET', 'POST'])
@login_required
def add_questions():
    form = QuestionsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        questions = Questions()
        questions.title = form.title.data
        questions.content = form.content.data
        questions.is_private = form.is_private.data
        current_user.questions.append(questions)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('questions.html',
                           form=form)


@app.route('/questions/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = QuestionsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        questions = db_sess.query(Questions).filter(Questions.id == id,
                                                    Questions.user == current_user
                                                    ).first()
        if questions:
            form.title.data = questions.title
            form.content.data = questions.content
            form.is_private.data = questions.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        questions = db_sess.query(Questions).filter(Questions.id == id,
                                                    Questions.user == current_user
                                                    ).first()
        if questions:
            questions.title = form.title.data
            questions.content = form.content.data
            questions.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('questions.html',
                           form=form
                           )


@app.route('/add_answer/<int:num>', methods=['GET', 'POST'])
@login_required
def add_answer(num):
    form = AnswersForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        answers = Answers()
        answers.content = form.content.data
        answers.user_id = current_user.id
        answers.questions_id = num
        current_user.answers.append(answers)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect(f'/solutions/{num}')
    return render_template('answers.html',
                           form=form)


@app.route('/profile')
def profile():
    if current_user.is_authenticated:
        answers = len(current_user.answers)
        return render_template("profile.html", answers=answers)
    else:
        return redirect('/login')


@app.route('/solutions/<int:num>')
def solutions(num):
    db_sess = db_session.create_session()
    questions = db_sess.query(Questions).filter(Questions.id == num).first()
    return render_template("solutions.html", questions=questions)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    db_session.global_init("db/forms.db")
    app.run(port=8080, host='127.0.0.1')
