# Task Management System

Task Management System is a web-based task management application. Allows users to create, edit and delete tasks, as well as view a list of tasks with the ability to filter and sort.

## Installation

1. First clone the repository:
```
git clone https://github.com/ValerieeSt/TaskManagementSystem.git
```
3. Install dependencies:
 ```
pip install -r requirements.txt
```

## Database Configuration

1. Open the `app.py` file.
2. Locate the following section:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri_here'
```
  Update the database URI with your database credentials and connection details.

3. Then run migrations to create the required tables in the database:
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```
## Run
1. Navigate to the project directory: `cd TaskManagementSystem`
2. Launch the application: `python app.py`
3. Open a web browser and go to http://localhost:5000

## Usage

- Adding a new task: Go to the "Add Task" page and fill in the required fields.
- Editing a task: On the task list page, click "Edit" next to the task you want to edit.
- Deleting a task: On the task list page, click "Delete" next to the task you want to delete.
