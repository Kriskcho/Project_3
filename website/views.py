from flask import Blueprint, app, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from website import db
from .models import Like
import json

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    from .models import User
    return render_template('home.html', user=current_user)

@views.route('/exercises', methods=['GET', 'POST'])
def exercises():
    from .models import ExerciseLibrary
    
    difficulty = request.args.get('difficulty', '')
    exercise_type = request.args.get('type', '')
    equipment = request.args.get('equipment', '')

    query = ExerciseLibrary.query

    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if exercise_type:
        query = query.filter_by(exercise_type=exercise_type)
    if equipment == 'no':
        query = query.filter_by(requires_equipment=False)
    elif equipment == 'yes':
        query = query.filter_by(requires_equipment=True)

    exercises = query.all()

    if ExerciseLibrary.query.count() == 0:
        populate_sample_exercises()
        exercises = query.all()

    return render_template('exercises.html', user=current_user, exercises=exercises)

@views.route('/exercise/<int:exercise_id>')
def exercise_detail(exercise_id):
    from .models import ExerciseLibrary
    exercise = ExerciseLibrary.query.get_or_404(exercise_id)
    return render_template('exercise_detail.html', user=current_user, exercise=exercise)

@views.route('/log-exercise/<int:exercise_id>', methods=['POST'])
@login_required
def log_completed_exercise(exercise_id):
    from .models import ExerciseLibrary, Exercise
    
    exercise_lib = ExerciseLibrary.query.get_or_404(exercise_id)
    
    new_exercise = Exercise(
        user_id=current_user.id,
        title=exercise_lib.name,
        exercise_type=exercise_lib.exercise_type,
        duration_minutes=exercise_lib.duration_minutes,
        calories_burned=exercise_lib.calories_burned
    )
    db.session.add(new_exercise)
    db.session.commit()
    
    flash(f'Successfully logged {exercise_lib.name}!', category='success')
    return redirect(url_for('views.exercises', exercise_id=exercise_id))

@views.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    stats = {}
    recent = []
    if current_user.is_authenticated:
        from .models import Exercise
        exercises = Exercise.query.filter_by(user_id=current_user.id).order_by(Exercise.date_completed.desc()).all()
        total_sessions = len(exercises)
        total_minutes = sum(e.duration_minutes or 0 for e in exercises)
        calories_burned = sum(e.calories_burned or 0 for e in exercises)
        recent = exercises[:5]
        stats = {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "calories_burned": calories_burned
        }
    return render_template('dashboard.html', user=current_user, stats=stats, recent=recent)

@views.route('/delete-exercise/<int:exercise_id>', methods=['POST'])
@login_required
def delete_exercise(exercise_id):
    from .models import Exercise
    ex = Exercise.query.get_or_404(exercise_id)
    if ex.user_id != current_user.id:
        flash('Not authorized.', category='error')
        return redirect(url_for('views.dashboard'))
    db.session.delete(ex)
    db.session.commit()
    flash('Exercise entry deleted.', category='success')
    return redirect(url_for('views.dashboard'))

@views.route('/community', methods=['GET', 'POST'])
def community():
    from .models import Post, ChatMessage
    posts = Post.query.order_by(Post.date.desc()).all()
    chat_messages = ChatMessage.query.order_by(ChatMessage.date.asc()).limit(50).all()
    return render_template('community.html', user=current_user, posts=posts, chat_messages=chat_messages)

@views.route('/create-post', methods=['POST'])
@login_required
def create_post():
    from .models import Post
    content = request.form.get('content')
    if content and len(content) <= 500:
        new_post = Post(user_id=current_user.id, content=content)
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', category='success')
    else:
        flash('Post content is invalid.', category='error')
    return redirect(url_for('views.community'))

@views.route('/like-post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    from .models import Post
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        flash('Post unliked.', category='success')
    else:
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
        flash('Post liked!', category='success')
    return redirect(url_for('views.community'))

@views.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    from .models import Post
    post = Post.query.get_or_404(post_id)
    if post.user_id == current_user.id:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')
    return redirect(url_for('views.community'))

@views.route('/add-comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    from .models import Comment
    content = request.form.get('content')
    if content and len(content) <= 300:
        new_comment = Comment(user_id=current_user.id, post_id=post_id, content=content)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added!', category='success')
    return redirect(url_for('views.community'))

@views.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    from .models import Comment
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id == current_user.id:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted.', category='success')
    return redirect(url_for('views.community'))

@views.route('/send-message', methods=['POST'])
@login_required
def send_message():
    from .models import ChatMessage
    from .ai_agent import ask_ai

    user_message = request.form.get('message')

    if user_message and len(user_message) <= 500:
        new_user_msg = ChatMessage(
            user_id=current_user.id,
            message=user_message,
            sender='user'
        )
        db.session.add(new_user_msg)
        db.session.commit()

        chat_history = ChatMessage.query.filter_by(
            user_id=current_user.id
        ).order_by(ChatMessage.date.asc()).all()

        ai_reply = ask_ai(user_message, chat_history)

        new_bot_msg = ChatMessage(
            user_id=current_user.id,
            message=ai_reply,
            sender='bot'
        )
        db.session.add(new_bot_msg)
        db.session.commit()

    return redirect(url_for('views.community'))


@views.route('/myaccount', methods=['GET', 'POST'])
def myaccount():
    return render_template('myaccount.html', user=current_user)

def populate_sample_exercises():
    from .models import ExerciseLibrary
    
    sample_exercises = [
        ExerciseLibrary(
            name="Push-Ups",
            description="A classic upper body exercise that strengthens chest, shoulders, and triceps.",
            difficulty="Beginner",
            duration_minutes=10,
            calories_burned=50,
            requires_equipment=False,
            exercise_type="Strength",
            instructions="Start in plank position. Lower body until chest nearly touches floor. Push back up.",
            benefits="Builds upper body strength, improves core stability",
            image_url="pushups.jpg"
        ),
        ExerciseLibrary(
            name="Squats 111",
            description="Lower body exercise targeting quads, hamstrings, and glutes.",
            difficulty="Beginner",
            duration_minutes=15,
            calories_burned=80,
            requires_equipment=False,
            exercise_type="Strength",
            instructions="Stand with feet shoulder-width apart. Lower down as if sitting in a chair. Return to standing.",
            benefits="Strengthens legs and core, improves mobility",
            image_url="squats.jpg"
        ),
        ExerciseLibrary(
            name="Running",
            description="Cardiovascular exercise for endurance and stamina.",
            difficulty="Intermediate",
            duration_minutes=30,
            calories_burned=300,
            requires_equipment=False,
            exercise_type="Cardio",
            instructions="Maintain steady pace. Keep breathing rhythmic.",
            benefits="Improves cardiovascular health, burns calories",
            image_url="running.jpg"
        )
    ]

    for exercise in sample_exercises:
        db.session.add(exercise)
    
    db.session.commit()
    print("Sample exercises added to database!")