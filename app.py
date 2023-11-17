from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder=os.path.abspath('templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri_here'
app.secret_key = 'your_secret_key_here'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class Task(db.Model):
    __tablename__ = 'tasks'

    task_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.Date)
    status_id = db.Column(db.Integer, db.ForeignKey('task_statuses.status_id'))
    status = db.relationship('TaskStatus', back_populates='tasks', lazy=True)
    user_tasks = db.relationship('UserTask', back_populates='task', cascade='all, delete-orphan')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def serialize(self):
        return {
            'task_id': self.task_id,
            'description': self.description,
            'deadline': self.deadline.strftime('%Y-%m-%d') if self.deadline else None,
            'status': self.status.serialize() if self.status else None
        }


class TaskStatus(db.Model):
    __tablename__ = 'task_statuses'
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), nullable=False)
    tasks = db.relationship('Task', back_populates='status', cascade='all, delete-orphan')

    def serialize(self):
        return {
            'status_id': self.status_id,
            'status_name': self.status_name
        }


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    tasks = db.relationship('UserTask', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.user_id)


class UserTask(db.Model):
    __tablename__ = 'user_tasks'

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), primary_key=True)
    user = db.relationship('User', back_populates='tasks')
    task = db.relationship('Task', back_populates='user_tasks')


@app.route('/')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.user_id).all()
    task_statuses = TaskStatus.query.all()
    return render_template('index.html', tasks=tasks, task_statuses=task_statuses)


@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        description = request.form.get('description')
        deadline = request.form.get('deadline')
        status_id = request.form.get('status')
        new_task = Task(
            description=description,
            deadline=deadline,
            status_id=status_id,
            user_id=current_user.user_id  # Установите user_id при создании задачи
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))

    task_statuses = TaskStatus.query.all()
    return render_template('add_task.html', task_statuses=task_statuses)


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    task_statuses = TaskStatus.query.all()

    print(f"Task owner ID: {task.user_id}, Current user ID: {current_user.user_id}")

    # Добавим дополнительные проверки
    if not task.user_id:
        print("Permission denied: Task owner ID is None.")
        abort(403)  # Запрет доступа, если task.user_id не установлен

    if task.user_id != current_user.user_id:
        print("Permission denied: User is not the owner of the task.")
        abort(403)  # Запрет доступа, если пользователь не владелец задачи

    if request.method == 'POST':
        task.description = request.form.get('description')
        task.deadline = request.form.get('deadline')
        task.status_id = request.form.get('status')
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_task.html', task=task, task_statuses=task_statuses)


@app.route('/delete/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.user_id:
        for user_task in task.user_tasks:
            db.session.delete(user_task)
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    else:
        return jsonify({'message': 'Task not found or not authorized to delete'}), 404


@app.route('/filter/<status_id>')
def filter_tasks(status_id):
    if status_id != 'all':
        tasks = Task.query.filter_by(status_id=status_id, user_id=current_user.user_id).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.user_id).all()

    return jsonify(tasks=[task.serialize() for task in tasks])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Вход успешен!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Выход успешен!', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'error')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Регистрация успешна. Теперь вы можете войти', 'success')
            app.logger.info(f"User registered: {username}")  # Добавляем эту строку
            return redirect(url_for('login'))

    return render_template('register.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

if __name__ == '__main__':
    app.run(debug=True)

print(app.url_map)