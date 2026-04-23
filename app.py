from flask import Flask, render_template, request, redirect, url_for
from models import db, AnnualGoal, MonthlyGoal, WeeklyGoal, Task, Note, Category, RecurringTask
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///planner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

# ------------------ الأهداف السنوية ------------------
@app.route('/annual')
def annual_goals():
    goals = AnnualGoal.query.all()
    return render_template('annual_goals.html', goals=goals)

@app.route('/annual/add', methods=['POST'])
def add_annual_goal():
    title = request.form['title']
    description = request.form.get('description', '')
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    if start_date <= end_date:
        goal = AnnualGoal(title=title, description=description, start_date=start_date, end_date=end_date)
        db.session.add(goal)
        db.session.commit()
    return redirect(url_for('annual_goals'))

@app.route('/annual/delete/<int:goal_id>')
def delete_annual_goal(goal_id):
    goal = AnnualGoal.query.get_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    return redirect(url_for('annual_goals'))
@app.route('/annual/edit/<int:goal_id>', methods=['GET', 'POST'])
def edit_annual_goal(goal_id):
    goal = AnnualGoal.query.get_or_404(goal_id)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        if start_date <= end_date:
            goal.update(title, description, start_date, end_date)
        return redirect(url_for('annual_goals'))
    return render_template('edit_annual_goal.html', goal=goal)

# ------------------ الأهداف الشهرية ------------------
@app.route('/monthly')
def monthly_goals():
    monthly = MonthlyGoal.query.all()
    annuals = AnnualGoal.query.all()
    return render_template('monthly_goals.html', monthly_goals=monthly, annual_goals=annuals)

@app.route('/monthly/add', methods=['POST'])
def add_monthly_goal():
    title = request.form['title']
    description = request.form.get('description', '')
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    annual_goal_id = int(request.form['annual_goal_id'])
    annual = AnnualGoal.query.get(annual_goal_id)
    if annual and start_date >= annual.start_date and end_date <= annual.end_date and start_date <= end_date:
        goal = MonthlyGoal(title=title, description=description, start_date=start_date, end_date=end_date, annual_goal_id=annual_goal_id)
        db.session.add(goal)
        db.session.commit()
        annual.update_progress()
    return redirect(url_for('monthly_goals'))

@app.route('/monthly/delete/<int:goal_id>')
def delete_monthly_goal(goal_id):
    goal = MonthlyGoal.query.get_or_404(goal_id)
    annual_id = goal.annual_goal_id
    db.session.delete(goal)
    db.session.commit()
    annual = AnnualGoal.query.get(annual_id)
    if annual:
        annual.update_progress()
    return redirect(url_for('monthly_goals'))

@app.route('/monthly/edit/<int:goal_id>', methods=['GET', 'POST'])
def edit_monthly_goal(goal_id):
    goal = MonthlyGoal.query.get_or_404(goal_id)
    annuals = AnnualGoal.query.all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        annual_goal_id = int(request.form['annual_goal_id'])
        # تحقق من أن التواريخ تقع ضمن الهدف السنوي
        annual = AnnualGoal.query.get(annual_goal_id)
        if annual and start_date >= annual.start_date and end_date <= annual.end_date and start_date <= end_date:
            goal.update(title, description, start_date, end_date, annual_goal_id)
        return redirect(url_for('monthly_goals'))
    return render_template('edit_monthly_goal.html', goal=goal, annual_goals=annuals)

# ------------------ الأهداف الأسبوعية ------------------
@app.route('/weekly')
def weekly_goals():
    weekly = WeeklyGoal.query.all()
    monthly = MonthlyGoal.query.all()
    return render_template('weekly_goals.html', weekly_goals=weekly, monthly_goals=monthly)

@app.route('/weekly/add', methods=['POST'])
def add_weekly_goal():
    title = request.form['title']
    description = request.form.get('description', '')
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    monthly_goal_id = int(request.form['monthly_goal_id'])
    monthly = MonthlyGoal.query.get(monthly_goal_id)
    if monthly and start_date >= monthly.start_date and end_date <= monthly.end_date and start_date <= end_date:
        goal = WeeklyGoal(title=title, description=description, start_date=start_date, end_date=end_date, monthly_goal_id=monthly_goal_id)
        db.session.add(goal)
        db.session.commit()
        monthly.update_progress()
    return redirect(url_for('weekly_goals'))

@app.route('/weekly/achieve/<int:goal_id>')
def achieve_weekly_goal(goal_id):
    goal = WeeklyGoal.query.get_or_404(goal_id)
    goal.achieve()
    return redirect(url_for('weekly_goals'))

@app.route('/weekly/delete/<int:goal_id>')
def delete_weekly_goal(goal_id):
    goal = WeeklyGoal.query.get_or_404(goal_id)
    monthly_id = goal.monthly_goal_id
    db.session.delete(goal)
    db.session.commit()
    monthly = MonthlyGoal.query.get(monthly_id)
    if monthly:
        monthly.update_progress()
    return redirect(url_for('weekly_goals'))

@app.route('/weekly/edit/<int:goal_id>', methods=['GET', 'POST'])
def edit_weekly_goal(goal_id):
    goal = WeeklyGoal.query.get_or_404(goal_id)
    monthlys = MonthlyGoal.query.all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        monthly_goal_id = int(request.form['monthly_goal_id'])
        monthly = MonthlyGoal.query.get(monthly_goal_id)
        if monthly and start_date >= monthly.start_date and end_date <= monthly.end_date and start_date <= end_date:
            goal.update(title, description, start_date, end_date, monthly_goal_id)
        return redirect(url_for('weekly_goals'))
    return render_template('edit_weekly_goal.html', goal=goal, monthly_goals=monthlys)
# ------------------ المهام (Tasks) ------------------
@app.route('/tasks')
def tasks():
    all_tasks = Task.query.all()
    all_categories = Category.query.all()
    return render_template('tasks.html', tasks=all_tasks, categories=all_categories)

@app.route('/tasks/add', methods=['POST'])
def add_task():
    title = request.form.get('title')
    description = request.form.get('description', '')
    due_date_str = request.form.get('due_date')
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
    priority = request.form.get('priority', 'عادي')
    category_id = request.form.get('category_id')  # <-- هذا السطر مهم
    if title:
        task = Task(title=title, description=description, due_date=due_date, priority=priority)
        if category_id and category_id != '':
            task.category_id = int(category_id)
        db.session.add(task)
        db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/tasks/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_completed = True
    db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/tasks/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        priority = request.form.get('priority')
        category_id = request.form.get('category_id')
        task.update(title, description, due_date, priority)
        if category_id and category_id != '':
            task.category_id = int(category_id)
        else:
            task.category_id = None
        db.session.commit()
        return redirect(url_for('tasks'))
    return render_template('edit_task.html', task=task, categories=categories)

# ------------------ الملاحظات (Notes) ------------------
@app.route('/notes')
def notes():
    all_notes = Note.query.all()
    all_categories = Category.query.all()
    return render_template('notes.html', notes=all_notes, categories=all_categories)

@app.route('/notes/add', methods=['POST'])
def add_note():
    title = request.form.get('title')
    content = request.form.get('content')
    category_id = request.form.get('category_id')
    if title and content:
        note = Note(title=title, content=content)
        if category_id and category_id != '':
            note.category_id = int(category_id)
        db.session.add(note)
        db.session.commit()
    return redirect(url_for('notes'))

@app.route('/notes/delete/<int:note_id>')
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('notes'))
@app.route('/notes/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form.get('category_id')
        note.update(title, content)
        if category_id and category_id != '':
            note.category_id = int(category_id)
        else:
            note.category_id = None
        db.session.commit()
        return redirect(url_for('notes'))
    return render_template('edit_note.html', note=note, categories=categories)
# ------------------ التصنيفات (Categories) ------------------
@app.route('/categories')
def categories():
    all_cats = Category.query.all()
    return render_template('categories.html', categories=all_cats)

@app.route('/categories/add', methods=['POST'])
def add_category():
    name = request.form.get('name')
    color = request.form.get('color', '#0d6efd')
    if name:
        # تحقق من عدم وجود تصنيف بنفس الاسم
        existing = Category.query.filter_by(name=name).first()
        if not existing:
            cat = Category(name=name, color=color)
            db.session.add(cat)
            db.session.commit()
    return redirect(url_for('categories'))

@app.route('/categories/delete/<int:cat_id>')
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    # تعيين category_id = NULL للمهام والملاحظات المرتبطة بهذا التصنيف
    for task in cat.tasks:
        task.category_id = None
    for note in cat.notes:
        note.category_id = None
    db.session.delete(cat)
    db.session.commit()
    return redirect(url_for('categories'))

@app.route('/categories/filter/<int:cat_id>')
def filter_by_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    tasks = Task.query.filter_by(category_id=cat_id).all()
    notes = Note.query.filter_by(category_id=cat_id).all()
    recurring_tasks = RecurringTask.query.filter_by(category_id=cat_id, is_active=True).all()
    return render_template('filtered_content.html', category=cat, tasks=tasks, notes=notes)




# ------------------ المهام الروتينية (Recurring Tasks) ------------------
@app.route('/recurring')
def recurring_tasks():
    tasks = RecurringTask.query.filter_by(is_active=True).all()
    today = date.today()
    due_today = [t for t in tasks if t.next_due <= today]
    categories = Category.query.all()
    return render_template('recurring_tasks.html', tasks=tasks, due_today=due_today, categories=categories)

@app.route('/recurring/add', methods=['POST'])
def add_recurring_task():
    title = request.form['title']
    description = request.form.get('description', '')
    freq_type = request.form['frequency_type']
    freq_days = request.form.get('frequency_days')
    weekday = request.form.get('weekday')
    category_id = request.form.get('category_id')
    task = RecurringTask(
        title=title,
        description=description,
        frequency_type=freq_type,
        frequency_days=int(freq_days) if freq_days and freq_days.isdigit() else None,
        weekday=int(weekday) if weekday and weekday.isdigit() and freq_type == 'weekly' else None,
        next_due=date.today(),
        category_id=int(category_id) if category_id and category_id != '' else None
    )
    db.session.add(task)
    db.session.commit()
    return redirect(url_for('recurring_tasks'))

@app.route('/recurring/complete/<int:task_id>')
def complete_recurring_task(task_id):
    task = RecurringTask.query.get_or_404(task_id)
    task.complete()
    return redirect(url_for('recurring_tasks'))

@app.route('/recurring/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_recurring_task(task_id):
    task = RecurringTask.query.get_or_404(task_id)
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        freq_type = request.form['frequency_type']
        freq_days = request.form.get('frequency_days')
        weekday = request.form.get('weekday')
        category_id = request.form.get('category_id')
        is_active = request.form.get('is_active') == 'on'
        task.update(
            title=title,
            description=description,
            frequency_type=freq_type,
            frequency_days=int(freq_days) if freq_days and freq_days.isdigit() else None,
            category_id=int(category_id) if category_id and category_id != '' else None,
            is_active=is_active,
            weekday=int(weekday) if weekday and weekday.isdigit() and freq_type == 'weekly' else None
        )
        return redirect(url_for('recurring_tasks'))
    return render_template('edit_recurring_task.html', task=task, categories=categories)

@app.route('/recurring/delete/<int:task_id>')
def delete_recurring_task(task_id):
    task = RecurringTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('recurring_tasks'))





if __name__ == '__main__':
    app.run(debug=True)
