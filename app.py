from flask import Flask, render_template, request, redirect, url_for
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
    status = db.relationship('TaskStatus', backref='tasks', lazy=True)
class TaskStatus(db.Model):
    __tablename__ = 'task_statuses'
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), nullable=False)

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

        # Добавление задачи в базу данных
        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for('index'))

    # Получение списка статусов задач из базы данных
    task_statuses = TaskStatus.query.all()
    return render_template('add_task.html', task_statuses=task_statuses)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        task.description = request.form.get('description')
        task.deadline = request.form.get('deadline')
        task.status_id = request.form.get('status')

        # Обновление задачи в базе данных
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('edit_task.html', task=task)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)


