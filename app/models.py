import typing
import datetime
from os import environ

import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from transliterate import slugify

from app import db, login_manager

user_submission = db.Table(
    'user_submission',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('submission_id', db.Integer, db.ForeignKey('submissions.id'))
)


class BaseModel(db.Model):
    __abstract__ = True

    def __repr__(self) -> str:
        return self._repr(id=self.id)

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class User(BaseModel, UserMixin):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True)
    verified = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    role_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("roles.id"))
    role = relationship('Role')

    grade_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("grades.id"))
    grade = relationship('Grade')
    grade_letter = sqlalchemy.Column(sqlalchemy.String)

    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    registration_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.utcnow)

    submissions = relationship('Submission', secondary=user_submission, backref='users')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return self._repr(
            id=self.id,
            name=f'{self.name} {self.surname}',
            grade=f'{self.grade}{self.grade_letter}',
            email=self.email,
            role=self.role,
        )


class Grade(BaseModel):
    __tablename__ = "grades"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    topics = relationship('Topic', backref='grade')

    def __repr__(self):
        return self._repr(number=self.number)


class Role(BaseModel):
    __tablename__ = "roles"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def __repr__(self):
        return self._repr(name=self.name)


class Topic(BaseModel):
    __tablename__ = "topics"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    grade_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("grades.id"))

    name = sqlalchemy.Column(sqlalchemy.String)
    translit_name = sqlalchemy.Column(sqlalchemy.String)

    tasks = relationship('Task', backref='topic')

    def set_translit_name(self):
        self.translit_name = slugify(self.name)

    def __repr__(self):
        return self._repr(
            id=self.id,
            name=f'{self.name} ({self.translit_name})',
            grade=self.grade,
        )


class Task(BaseModel):
    __tablename__ = "tasks"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    topic_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("topics.id"))

    name = sqlalchemy.Column(sqlalchemy.String)
    translit_name = sqlalchemy.Column(sqlalchemy.String)
    text = sqlalchemy.Column(sqlalchemy.Text)

    example = relationship('Example', uselist=False, backref='task')
    tests = relationship('Test', backref='task', lazy='subquery')

    submissions = relationship('Submission', backref='task')

    def set_translit_name(self):
        self.translit_name = slugify(self.name)

    def __repr__(self):
        return self._repr(
            id=self.id,
            name=f'{self.name} ({self.translit_name})',
            topic=self.topic.name,
            grade=self.topic.grade.number
        )


class Example(BaseModel):
    __tablename__ = "examples"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"))

    example_input = sqlalchemy.Column(sqlalchemy.Text)
    example_output = sqlalchemy.Column(sqlalchemy.Text)


class Test(BaseModel):
    __tablename__ = "tests"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"))

    test_input = sqlalchemy.Column(sqlalchemy.Text)
    test_output = sqlalchemy.Column(sqlalchemy.Text)
    is_hidden = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    def __repr__(self):
        return self._repr(
            id=self.id,
            task=self.task,
            data={
                'input': self.test_input,
                'output': self.test_output,
                'hidden': self.is_hidden
            }
        )


class Submission(BaseModel):
    __tablename__ = "submissions"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"))

    language = sqlalchemy.Column(sqlalchemy.String)
    passed_tests = sqlalchemy.Column(sqlalchemy.Integer)
    source_code = sqlalchemy.Column(sqlalchemy.Text)
    submission_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.utcnow)

    test_results = relationship('TestResult', backref="submission", lazy='subquery')

    @hybrid_property
    def processed_code(self):
        # Dictionary with symbols that can break CodeMirror
        replacements = {
            '"': r'\"',  # double quote
            "'": r"\'",  # singe quote
            "`": r"\`"  # backtick
        }

        code = repr(self.source_code)[1:-1]
        for character in replacements.keys():
            code = code.replace(character, replacements[character])

        return code

    def get_result(self) -> dict:
        failed_tests = [result for result in self.test_results if not result.success]
        if any(failed_tests):
            failed_test = failed_tests[0]
            return {'success': False, 'message': failed_test.message}

        return {'success': True, 'message': 'Success'}

    def __repr__(self):
        return self._repr(
            id=self.id,
            user=self.user,
            task=self.task,
            result=self.get_result()['message']
        )


class TestResult(BaseModel):
    __tablename__ = "test_result"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    test_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tests.id"))
    test = relationship('Test')

    submission_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("submissions.id"))

    success = sqlalchemy.Column(sqlalchemy.Boolean)
    message = sqlalchemy.Column(sqlalchemy.String)
    user_output = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return self._repr(
            id=self.id,
            test=self.test,
            submission=self.submission,
            message=self.message
        )


class Report(BaseModel):
    __tablename__ = "reports"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = relationship('User')

    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"))
    task = relationship('Task')

    text = sqlalchemy.Column(sqlalchemy.Text)

    def __repr__(self):
        return self._repr(
            user=self.user,
            task=self.task,
            text=self.text
        )


def init_db_data():
    # Creating grades
    if db.session.query(User).count() == 0:
        for grade in range(5, 12):
            db.session.add(Grade(number=grade))

        # Creating roles
        user_role = Role(name='user')
        db.session.add(user_role)
        admin_role = Role(name='admin')
        db.session.add(admin_role)

        # Creating admin
        admin = User(
            name='Админ',
            surname='Админович',
            email='contester@mail.ru',
            verified=True,
            role_id=db.session.query(Role).filter(Role.name == 'admin').first().id,
            grade_id=None,
            grade_letter=None
        )
        admin.set_password(environ.get('ADMIN_PASSWORD'))
        db.session.add(admin)

        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)
