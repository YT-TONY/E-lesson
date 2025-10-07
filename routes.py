from flask import render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from app import app
from models import db, User, Note

# -------------------------------
# Home route
# -------------------------------
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# -------------------------------
# Register route
# -------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role,
            is_approved=False
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Wait for admin approval before logging in.', 'info')
        return redirect(url_for('login'))

    return render_template('register.html')


# -------------------------------
# Login route
# -------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

        if not user.is_approved:
            flash('Your account is awaiting admin approval.', 'warning')
            return redirect(url_for('login'))

        login_user(user)
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


# -------------------------------
# Logout
# -------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# -------------------------------
# Dashboard routing by role
# -------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))


# -------------------------------
# Admin Dashboard
# -------------------------------
@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    pending_users = User.query.filter_by(is_approved=False).all()
    pending_notes = Note.query.filter_by(status='pending').all()
    approved_notes = Note.query.filter_by(status='approved').all()

    return render_template(
        'admin_dashboard.html',
        pending_users=pending_users,
        pending_notes=pending_notes,
        approved_notes=approved_notes
    )


# -------------------------------
# Approve/Delete User
# -------------------------------
@app.route('/approve_user/<int:user_id>')
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'{user.username} has been approved!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'{user.username} has been removed.', 'info')
    return redirect(url_for('admin_dashboard'))


# -------------------------------
# Approve/Delete Notes
# -------------------------------
@app.route('/approve_note/<int:note_id>')
@login_required
def approve_note(note_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    note = Note.query.get_or_404(note_id)
    note.status = 'approved'
    db.session.commit()
    flash(f'Note "{note.title}" has been approved!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_note/<int:note_id>')
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)

    if current_user.role != 'admin' and note.uploader != current_user:
        flash('You do not have permission to delete this note.', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(note)
    db.session.commit()
    flash(f'Note "{note.title}" has been deleted.', 'info')
    return redirect(url_for('dashboard'))


# -------------------------------
# Teacher Dashboard & Upload
# -------------------------------
@app.route('/dashboard/teacher')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('teacher_dashboard.html', notes=notes)


@app.route('/upload_note', methods=['GET', 'POST'])
@login_required
def upload_note():
    if current_user.role != 'teacher':
        flash('Only teachers can upload notes.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        course = request.form['course']
        file = request.files['file']

        if not file:
            flash('Please select a file.', 'danger')
            return redirect(url_for('upload_note'))

        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        new_note = Note(
            title=title,
            description=description,
            course=course,
            file_path=filename,
            user_id=current_user.id
        )
        db.session.add(new_note)
        db.session.commit()

        flash('Note uploaded successfully! Waiting for admin approval.', 'info')
        return redirect(url_for('teacher_dashboard'))

    return render_template('upload_note.html')


# -------------------------------
# Student Dashboard
# -------------------------------
@app.route('/dashboard/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    notes = Note.query.filter_by(status='approved').all()
    return render_template('student_dashboard.html', notes=notes)


# -------------------------------
# View note (inline)
# -------------------------------
@app.route('/view/<path:filename>')
@login_required
def view_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash("File not found.", "danger")
        return redirect(url_for('dashboard'))

    # Automatically detect MIME type for inline view
    mimetype = None
    if filename.endswith('.pdf'):
        mimetype = 'application/pdf'
    elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        mimetype = 'image/jpeg'
    else:
        mimetype = 'application/octet-stream'

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False, mimetype=mimetype)
