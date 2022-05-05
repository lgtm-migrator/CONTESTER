from flask import render_template, redirect, url_for, request, session
from flask_login import current_user, login_required
from flask_breadcrumbs import register_breadcrumb

from app import app, db, login_manager
from app.blueprints.admin.admin import admin
from app.blueprints.auth.auth import auth
from app.blueprints.api.api import api
from app.blueprints.errors.handler import errors

from app.models import Grade, Topic, Task, Example, Test
from app.contester.languages import languages_dict
from app.utils.routes import next_url
import app.breadcrumbs as bc

app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(errors, url_prefix='/error')


# Unauthorized handler
@login_manager.unauthorized_handler
def unauthorized_callback():
    session['next_url'] = request.path
    return redirect(url_for('auth.login_page'))


@app.route('/', methods=['GET'])
@register_breadcrumb(app, '.', 'Главная')
@next_url
def home_page():
    return render_template('home.html', title='Главная')


@app.route('/<int:grade_number>', methods=['GET'])
@register_breadcrumb(app, '.grade', '', dynamic_list_constructor=bc.view_grade_dlc)
@next_url
def grade_page(grade_number):
    grade = db.session.query(Grade).filter(Grade.number == grade_number).first_or_404()
    topics = grade.get_topics()

    return render_template('grade.html', title=f'{grade.number} класс',
                           grade=grade, topics=topics)


@app.route('/<int:grade_number>/<string:topic_translit_name>', methods=['GET'])
@register_breadcrumb(app, '.grade.topic', '', dynamic_list_constructor=bc.view_topic_dlc)
@next_url
def topic_page(grade_number, topic_translit_name):
    grade = db.session.query(Grade).filter(Grade.number == grade_number).first_or_404()
    topic = db.session.query(Topic).filter(Topic.translit_name == topic_translit_name).first_or_404()
    tasks = topic.get_tasks()

    return render_template('topic.html', title=topic.name, grade=grade, topic=topic, tasks=tasks)


@app.route('/<int:grade_number>/<string:topic_translit_name>/<string:task_translit_name>', methods=['GET'])
@register_breadcrumb(app, '.grade.topic.task', '', dynamic_list_constructor=bc.view_task_dlc)
@next_url
def task_page(grade_number, topic_translit_name, task_translit_name):
    grade = db.session.query(Grade).filter(Grade.number == grade_number).first_or_404()
    topic = db.session.query(Topic).filter(Topic.translit_name == topic_translit_name).first_or_404()
    task = db.session.query(Task).filter(Task.translit_name == task_translit_name).first_or_404()

    return render_template('task.html', title=task.name, grade=grade, topic=topic, task=task, languages=languages_dict)


@app.route('/profile', methods=['GET', 'POST'])
@register_breadcrumb(app, '.profile', 'Профиль')
@login_required
def profile_page():
    return render_template('profile.html', title='Профиль')
