from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri_here'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Task(db.Model):
    __tablename__ = 'tasks'

    task_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.Date)
    status_id = db.Column(db.Integer, db.ForeignKey('task_statuses.status_id'))
    status = db.relationship('TaskStatus', back_populates='tasks', lazy=True)
    user_tasks = db.relationship('UserTask', back_populates='task', cascade='all, delete-orphan')


class TaskStatus(db.Model):
    __tablename__ = 'task_statuses'
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), nullable=False)
    tasks = db.relationship('Task', back_populates='status', cascade='all, delete-orphan')


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    tasks = db.relationship('UserTask', back_populates='user', cascade='all, delete-orphan')


class UserTask(db.Model):
    __tablename__ = 'user_tasks'

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), primary_key=True)
    user = db.relationship('User', back_populates='tasks')
    task = db.relationship('Task', back_populates='user_tasks')


@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)


@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        description = request.form.get('description')
        deadline = request.form.get('deadline')
        status_id = request.form.get('status')

        # Создание новой задачи
        new_task = Task(description=description, deadline=deadline, status_id=status_id)

        # Добавление задачи в бд
        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for('index'))

    # Получение списка статусов задач из бд
    task_statuses = TaskStatus.query.all()
    return render_template('add_task.html', task_statuses=task_statuses)


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    task_statuses = TaskStatus.query.all()

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
    if task:
        # Удаление связанных записей в таблице user_tasks
        for user_task in task.user_tasks:
            db.session.delete(user_task)

        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    else:
        return jsonify({'message': 'Task not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
