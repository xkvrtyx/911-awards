import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///awards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # lead, senior, part_time, regular
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    votes = db.relationship('Vote', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    nominees = db.relationship('Nominee', backref='category', lazy=True, cascade='all, delete-orphan')

class Nominee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))  # optional
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    votes = db.relationship('Vote', backref='nominee', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    nominee_id = db.Column(db.Integer, db.ForeignKey('nominee.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'category_id', name='unique_user_category_vote'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Event config
EVENT_NAME = "911 Dispatcher Awards"
EVENT_TAGLINE = "Honoring the voices that save lives. Cast your vote — one per category."

# Full roster with roles
ROSTER = {
    "Abby Holliman": "lead",
    "Kady Elgen": "lead",
    "Karrissa Hood": "senior",
    "Alex Skasick": "senior",
    "Jennifer Smith": "senior",
    "Emma Thompson": "part_time",
    "Corrie Eads": "part_time",
    "Hannah Hensley": "regular",
    "Taylor Williams": "regular",
    "Keri Atkinson": "regular",
    "Madison Gray": "regular",
}

# Categories that are restricted by role
RESTRICTED_CATEGORIES = {
    "The Lead of the Year Award": "lead",
    "The Senior of the Year Award": "senior",
    "Part-Time Telecommunicator of the Year": "part_time",
}

def init_db():
    with app.app_context():
        db.create_all()
        # Only seed categories if none exist yet (keeps votes and accounts permanent)
        if Category.query.count() == 0:
            # Shared nominee lists
            all_dispatchers = [
                {"name": "Abby Holliman", "description": "Abby's Shift"},
                {"name": "Alex Skasick", "description": "Abby's Shift"},
                {"name": "Hannah Hensley", "description": "Abby's Shift"},
                {"name": "Karrissa Hood", "description": "Abby's Shift"},
                {"name": "Taylor Williams", "description": "Abby's Shift"},
                {"name": "Jennifer Smith", "description": "Kady's Shift"},
                {"name": "Kady Elgen", "description": "Kady's Shift"},
                {"name": "Keri Atkinson", "description": "Kady's Shift"},
                {"name": "Madison Gray", "description": "Kady's Shift"},
            ]
            
            senior_nominees = [
                {"name": "Alex Skasick", "description": "Abby's Shift"},
                {"name": "Jennifer Smith", "description": "Kady's Shift"},
                {"name": "Karrissa Hood", "description": "Abby's Shift"},
            ]
            
            lead_nominees = [
                {"name": "Abby Holliman", "description": "Abby's Shift"},
                {"name": "Kady Elgen", "description": "Kady's Shift"},
            ]

            categories_data = [
                {
                    "name": "The Human Google Award",
                    "description": "Recognizes a telecommunicator who demonstrates exceptional knowledge of geography, procedures, resources, and local information, enabling quick and accurate responses.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Reliability Award",
                    "description": "Recognizes a telecommunicator who consistently demonstrates dependability through strong attendance, willingness to cover shifts, and reliable performance.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Plot Twist Professional Award",
                    "description": "Recognizes a telecommunicator who adapts quickly and effectively when a routine call or incident unexpectedly escalates into a complex or high-priority emergency.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Calmest Voice in the Chaos Award",
                    "description": "Recognizes a telecommunicator who maintains a steady, professional demeanor and clear communication during high-stress or rapidly evolving incidents.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Headset Hero Award",
                    "description": "Recognizes a telecommunicator who consistently performs at a high level while managing multiple simultaneous tasks, including calls, radio traffic, and system updates.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Above & Beyond Award",
                    "description": "Recognizes a telecommunicator whose actions or initiative significantly exceeded standard expectations in support of the public, field units, or coworkers.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Keyboard Warrior Award",
                    "description": "Recognizes a telecommunicator who maintains high accuracy and speed while documenting calls and updating systems in real time.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Comic Relief Award",
                    "description": "Recognizes a telecommunicator who positively contributes to the work environment by providing appropriate humor while still meeting performance standards.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Overtime Legend Award",
                    "description": "Recognizes a telecommunicator who demonstrates exceptional reliability by covering additional shifts and supporting staffing needs.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Peer Support Pro Award",
                    "description": "Recognizes a telecommunicator who offers practical assistance and encouragement to coworkers while maintaining their own performance standards.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The “Seen It, Handled It” Award",
                    "description": "Recognizes a telecommunicator who applies experience and sound judgment to effectively manage unusual or challenging calls.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Needs Autocorrect Award",
                    "description": "Recognizes a telecommunicator known for frequent spelling errors in CAD entries or for regularly asking how to spell words before typing.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Unbothered Legend Award",
                    "description": "Recognizes a telecommunicator who remains composed and effective regardless of call volume, radio traffic, staffing levels, or unexpected situations.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Certified Napper Award",
                    "description": "Recognizes a telecommunicator who maximizes rest opportunities during lower-activity periods while remaining available for operational needs.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The \"What?\" Award",
                    "description": "Recognizes a telecommunicator who frequently requests repetition or clarification, even in quiet conditions.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Caffeine Addict Award",
                    "description": "Recognizes a telecommunicator who relies heavily on caffeine to maintain alertness and performance throughout their shift.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Morning Escape Artist Award",
                    "description": "Recognizes a telecommunicator who efficiently completes end-of-shift duties and departs promptly at the conclusion of their tour.",
                    "nominees": all_dispatchers
                },
                {
                    "name": "The Senior of the Year Award",
                    "description": "Recognizes a senior telecommunicator who consistently demonstrates advanced skill, sound judgment, and leadership by supporting less-experienced staff while maintaining high performance standards.",
                    "nominees": senior_nominees
                },
                {
                    "name": "Part-Time Telecommunicator of the Year",
                    "description": "Recognizes a part-time telecommunicator who consistently demonstrates strong performance, reliability, and professionalism while supporting center operations.",
                    "nominees": [
                        {"name": "Corrie Eads", "description": "Part-Time"},
                        {"name": "Emma Thompson", "description": "Part-Time"}
                    ]
                },
                {
                    "name": "The Lead of the Year Award",
                    "description": "Recognizes a lead dispatcher or acting supervisor who effectively guides shift operations, assists with decision-making, and supports both staff and center objectives.",
                    "nominees": lead_nominees
                },
                {
                    "name": "Dispatcher of the Year Award",
                    "description": "Recognizes a telecommunicator who consistently delivers exceptional performance, professionalism, and composure while handling emergency and non-emergency calls.",
                    "nominees": all_dispatchers
                }
            ]
            for cat_data in categories_data:
                cat = Category(name=cat_data["name"], description=cat_data["description"])
                db.session.add(cat)
                db.session.flush()
                for nom_data in cat_data["nominees"]:
                    nom = Nominee(name=nom_data["name"], description=nom_data["description"], category_id=cat.id)
                    db.session.add(nom)
            db.session.commit()

init_db()

@app.route('/')
def index():
    categories = Category.query.all()
    return render_template('index.html', event_name=EVENT_NAME, tagline=EVENT_TAGLINE, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('vote'))
    
    # Get names that haven't registered yet
    registered_names = {u.name for u in User.query.all()}
    available_names = sorted([name for name in ROSTER.keys() if name not in registered_names])
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not name or name not in ROSTER:
            flash('Please select a valid name from the list.', 'error')
            return redirect(url_for('register'))
        if name in registered_names:
            flash('That person has already registered.', 'error')
            return redirect(url_for('register'))
        if not email or not password or len(password) < 6:
            flash('Valid email and password (min 6 chars) required.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        user = User(name=name, email=email, role=ROSTER[name])
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {name}! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', event_name=EVENT_NAME, available_names=available_names)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('vote'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('vote'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html', event_name=EVENT_NAME)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/vote')
@login_required
def vote():
    categories = Category.query.all()
    # Get user's existing votes as category_id -> nominee object
    user_votes = {}
    for v in current_user.votes:
        user_votes[v.category_id] = Nominee.query.get(v.nominee_id)
    
    return render_template('vote.html', 
                         event_name=EVENT_NAME, 
                         categories=categories, 
                         user_votes=user_votes, 
                         user_name=current_user.name,
                         user_role=current_user.role)

@app.route('/cast_vote', methods=['POST'])
@login_required
def cast_vote():
    category_id = request.form.get('category_id', type=int)
    nominee_id = request.form.get('nominee_id', type=int)
    if not category_id or not nominee_id:
        flash('Invalid vote.', 'error')
        return redirect(url_for('vote'))
    
    category = Category.query.get(category_id)
    if not category:
        flash('Invalid category.', 'error')
        return redirect(url_for('vote'))
    
    # Check role restriction
    restricted_role = RESTRICTED_CATEGORIES.get(category.name)
    if restricted_role and current_user.role == restricted_role:
        flash('You are not eligible to vote in this category.', 'error')
        return redirect(url_for('vote'))
    
    # Check if already voted in this category
    existing = Vote.query.filter_by(user_id=current_user.id, category_id=category_id).first()
    if existing:
        flash('You have already voted in this category.', 'error')
        return redirect(url_for('vote'))
    
    # Validate nominee belongs to category
    nominee = Nominee.query.filter_by(id=nominee_id, category_id=category_id).first()
    if not nominee:
        flash('Invalid nominee for this category.', 'error')
        return redirect(url_for('vote'))
    
    # Prevent voting for yourself
    if nominee.name == current_user.name:
        flash('You cannot vote for yourself.', 'error')
        return redirect(url_for('vote'))
    
    vote = Vote(user_id=current_user.id, category_id=category_id, nominee_id=nominee_id)
    db.session.add(vote)
    db.session.commit()
    flash(f'Vote cast for {nominee.name}!', 'success')
    return redirect(url_for('vote') + f'#category-{category_id}')

@app.route('/results')
def results():
    if not current_user.is_authenticated or current_user.name != "Karrissa Hood":
        flash('Results are only available to authorized users.', 'error')
        return redirect(url_for('index'))
    categories = Category.query.all()
    results_data = []
    for cat in categories:
        nominees_with_counts = []
        for nom in cat.nominees:
            count = Vote.query.filter_by(nominee_id=nom.id).count()
            nominees_with_counts.append({'nominee': nom, 'votes': count})
        nominees_with_counts.sort(key=lambda x: x['votes'], reverse=True)
        results_data.append({'category': cat, 'nominees': nominees_with_counts})
    return render_template('results.html', event_name=EVENT_NAME, results=results_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
