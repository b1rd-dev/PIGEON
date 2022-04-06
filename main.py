from flask_login import UserMixin, LoginManager, login_user, user_logged_in
from flask_login import login_required, current_user, logout_user
from flask import Flask, redirect, render_template, request, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
import os, hashlib



app = Flask(__name__)
app.config['SECRET_KEY'] = 'J0DEvTJCxr3uXOZm0jYSjlqfPaD7fJV4NFuAM6RBqyQNtcGtkO'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///server.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class SharedFolder(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(100), nullable=False, unique=True)
    users = db.Column(db.String(100), nullable=False)

login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(1000), nullable=False, unique=True)
    password = db.Column(db.String(1000))
    isAdmin = db.Column(db.Boolean, nullable=False)


@app.route('/signup', methods=["GET", 'POST'])
@login_required
def signup():
    if current_user.isAdmin:
        if request.method == "POST":
            username = request.form.get('name')
            password = request.form.get('password')
            isAdmin = True if request.form.get('isAdmin') == 'on' else False

            user = User.query.filter_by(username=username).first()
            if  '' or " " in username:
                flash('Set correct username!')
                return redirect('/signup')
            if user:
                flash('Username already exists. Go to <a href="/login">login page</a>.')
                return redirect('/signup')
            new_user = User(username=username, password=hashlib.sha256(password.encode('UTF-8')).hexdigest(), isAdmin=isAdmin)
            db.session.add(new_user)
            db.session.commit()

            return redirect('/login')
        else:
            return render_template('signup.html')
    else:
        return redirect("/")




@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or user.password != hashlib.sha256(password.encode('UTF-8')).hexdigest():
            flash('Please check your login details and try again.')
            return redirect('/login')
        login_user(user, remember=False)
        return redirect('/')
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route('/upload', methods=["POST"])
@login_required
def upload():
    if request.method == "POST":
        try:
            web_path = request.form['web_path']   

            if 'file' not in request.files:
                flash("Error!")
                return redirect(web_path)

            file = request.files['file']  

            if file.filename == '':
                flash("Invalid filename!")
                return redirect(web_path)

            path = request.form['path']        
                      
            if file.filename == '':
                return redirect(web_path)

            if file:
                full_path = os.path.join(path, file.filename)
                file.save(full_path)
            return redirect(web_path)

        except:
            flash("Error!")
            return redirect("/share")
    else:
        return redirect("/share")

@app.route('/share/<int:id>/')
@login_required
def redirect_to_back(id):
    return redirect("/share")

@app.route('/download/<int:id>/<path:path>')
@login_required
def download(id, path):
    if current_user.username in SharedFolder.query.get(id).users and SharedFolder.query.get(id).path.lower() in path.replace("//", "/").lower():
        return send_file(path, as_attachment=True)
    else:
        flash("Access is denied!")
        return redirect("/share")

@app.route('/share/<int:id>/<path:path>')
@login_required
def share_p(id, path):
    try:
        if current_user.username in SharedFolder.query.get(id).users:
            root_path = SharedFolder.query.get_or_404(id).path
            path_to_folder = f"{os.path.split(root_path)[0]}/{path}"
            shared_folders = os.listdir(path_to_folder)
            back_path = f"share/{id}/{'/'.join(path.split('/')[:-1])}"
            current_path = f"share/{id}/{path}"
            subdir = True if path else False
            files = []
            for file in shared_folders:
                files.append({
                    'id': id,
                    'path': root_path,
                    'full_path': path_to_folder + "/" + file,
                    'is_dir': os.path.isdir(path_to_folder + "/" + file),
                    'name': file,
                    'web_path': f"share/{id}/{path}/{file}"
                })   
            return render_template("share.html", files=files, subdir=subdir, wam=path, back=back_path, full_path=path_to_folder, web_path=current_path)
        else:
            flash("Access is denied!")
            return redirect("/share")
    except:
        flash("Can`t find file or directory.")
        return redirect("/share")

@app.route('/share')
@login_required
def share():
    try:
        shared_folders = SharedFolder.query.filter(SharedFolder.users.contains(current_user.username)).all() 
        files = []
        for file in shared_folders:
            print(file.path)
            files.append({
                'id': file.id,
                'path': file.path,
                'is_dir': os.path.isdir(file.path),
                'name': os.path.split(file.path)[-1],
                'web_path': f"share/{file.id}/{os.path.split(file.path)[-1]}"
            })    
        return render_template("share.html", files=files)
    except:
        flash("Error!")
        return redirect("/share")



@app.route('/users')
@login_required
def users():    
    if current_user.isAdmin:
        users = User.query.all()
        return render_template("users.html", users=users)
    else:
        return redirect("/")

@app.route('/users/update/<int:id>', methods=['POST'])
@login_required
def user_upd(id):    
    if current_user.isAdmin:
        user = User.query.get_or_404(id)
        user.username = request.form['name']
        user.password = hashlib.sha256(request.form['password'].encode('UTF-8')).hexdigest()
        user.isAdmin = True if request.form.get('isAdmin') == "on" else False
        try:
            db.session.commit()
            flash("User Updated !")
            return redirect('/users')
        except:
            return redirect('/users')
    else:
        return redirect("/")

@app.route('/users/delete/<int:id>')
@login_required
def user_del(id):    
    if current_user.isAdmin:
        user = User.query.get_or_404(id)
        try:
            db.session.delete(user)
            db.session.commit()
            flash("User deleted!")
            return redirect('/users')
        except:
            return redirect('/users')
    else:
        return redirect("/")

@app.route('/admin')
@login_required
def admin():    
    if current_user.isAdmin:
        shared_folders = SharedFolder.query.all()
        return render_template("admin.html", shared_folders=shared_folders)
    else:
        return redirect("/")

@app.route('/profile', methods=["GET", 'POST'])
@login_required
def profile():
    if current_user.isAdmin:
        user = User.query.get(current_user.id)
        if request.method == "POST":
            user.password = request.form.get('password')
            try:
                db.session.commit()
                flash("Successfuly updated!")
                return redirect('/profile')
            except:
                return redirect("profile")
        else:        
            return render_template("profile.html")
    else:
        return redirect("/")


@app.route('/unshare/<int:id>')
@login_required
def unshare(id):
    if current_user.isAdmin:
        share = SharedFolder.query.get_or_404(id)
        try:
            db.session.delete(share)
            db.session.commit()
            return redirect('/admin')
        except:
            return "Error"
    else:
        return redirect("/")

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    if current_user.isAdmin:
        share = SharedFolder.query.get(id)


        path_check = SharedFolder.query.filter_by(path=request.form['path']).first()
        if not os.path.isdir(request.form['path']):
            flash(f"Path {request.form['path']} doesn`t exist")
            return redirect('/admin')
        if path_check and path_check.id != id:
            flash("Path already registered")
            return redirect('/admin')
        for user in request.form['users'].split(","):
            if not User.query.filter_by(username=user).first():
                flash(f"User {user} doesn`t exist")
                return redirect('/admin')

        share.path = request.form['path'].replace("\\", "/")
        share.users = request.form['users']
        try:
            db.session.commit()
            return redirect('/admin')
        except:
            return "Error"
    else:
        return redirect("/")

@app.route('/ns', methods=['POST'])
@login_required
def new_share():
    if current_user.isAdmin:
        path = request.form['path'].replace("\\", "/")
        users = request.form['users']

        new_share = SharedFolder(path=path, users=users)
        path_check = SharedFolder.query.filter_by(path=path).first()

        if not os.path.isdir(path):
            flash(f"Path {path} doesn`t exist")
            return redirect('/admin')
        for user in users.split(","):
            if not User.query.filter_by(username=user).first():
                flash(f"User {user} doesn`t exist")
                return redirect('/admin')
        if path_check:
            flash("Path already registered")
            return redirect('/admin')
        try:
            db.session.add(new_share)
            db.session.commit()
            return redirect('/admin')
        except:
            return "Error"
    else:
        return redirect("/")


if __name__ == "__main__":

    app.run(debug=False, host="0.0.0.0", port=80)
