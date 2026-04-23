from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#0d6efd')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship('Task', backref='category', lazy=True)
    notes = db.relationship('Note', backref='category', lazy=True)
    recurring_tasks = db.relationship('RecurringTask', backref='category', lazy=True)

class AnnualGoal(db.Model):
    __tablename__ = 'annual_goals'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    progress = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    monthly_goals = db.relationship('MonthlyGoal', backref='annual_goal', lazy=True, cascade='all, delete-orphan')

    def update_progress(self):
        total = len(self.monthly_goals)
        if total == 0:
            self.progress = 0.0
        else:
            completed = sum(1 for mg in self.monthly_goals if mg.is_achieved)
            self.progress = (completed / total) * 100
        db.session.commit()

    def update(self, title, description, start_date, end_date):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        db.session.commit()

class MonthlyGoal(db.Model):
    __tablename__ = 'monthly_goals'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_achieved = db.Column(db.Boolean, default=False)
    progress = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    annual_goal_id = db.Column(db.Integer, db.ForeignKey('annual_goals.id'), nullable=False)
    weekly_goals = db.relationship('WeeklyGoal', backref='monthly_goal', lazy=True, cascade='all, delete-orphan')

    def update_progress(self):
        total = len(self.weekly_goals)
        if total == 0:
            self.progress = 0.0
            self.is_achieved = False
        else:
            completed = sum(1 for wg in self.weekly_goals if wg.is_achieved)
            self.progress = (completed / total) * 100
            self.is_achieved = (self.progress >= 100)
        db.session.commit()
        if self.annual_goal:
            self.annual_goal.update_progress()

    def update(self, title, description, start_date, end_date, annual_goal_id):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.annual_goal_id = annual_goal_id
        db.session.commit()
        self.update_progress()

class WeeklyGoal(db.Model):
    __tablename__ = 'weekly_goals'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_achieved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    monthly_goal_id = db.Column(db.Integer, db.ForeignKey('monthly_goals.id'), nullable=False)

    def achieve(self):
        if not self.is_achieved:
            self.is_achieved = True
            db.session.commit()
            if self.monthly_goal:
                self.monthly_goal.update_progress()

    def update(self, title, description, start_date, end_date, monthly_goal_id):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.monthly_goal_id = monthly_goal_id
        db.session.commit()
        if self.monthly_goal:
            self.monthly_goal.update_progress()

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default='عادي')
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    def update(self, title, description, due_date, priority):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        db.session.commit()

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    def update(self, title, content):
        self.title = title
        self.content = content
        self.updated_at = datetime.utcnow()
        db.session.commit()

class RecurringTask(db.Model):
    __tablename__ = 'recurring_tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    frequency_type = db.Column(db.String(20), nullable=False)  # daily, weekly, custom_days
    frequency_days = db.Column(db.Integer, nullable=True)
    weekday = db.Column(db.Integer, nullable=True)  # 0-6 Monday=0, Sunday=6
    last_completed = db.Column(db.Date, nullable=True)
    next_due = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_next_due(self):
        today = date.today()
        if self.frequency_type == 'daily':
            return today + timedelta(days=1)
        elif self.frequency_type == 'weekly' and self.weekday is not None:
            days_ahead = self.weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)
        elif self.frequency_type == 'custom_days' and self.frequency_days:
            return today + timedelta(days=self.frequency_days)
        return today

    def complete(self):
        self.last_completed = date.today()
        self.next_due = self.calculate_next_due()
        db.session.commit()

    def update(self, title, description, frequency_type, frequency_days, category_id, is_active, weekday=None):
        self.title = title
        self.description = description
        self.frequency_type = frequency_type
        self.frequency_days = frequency_days
        self.category_id = category_id
        self.is_active = is_active
        self.weekday = weekday if frequency_type == 'weekly' else None
        self.next_due = date.today()  # إعادة تعيين التاريخ القادم إلى اليوم
        db.session.commit()
