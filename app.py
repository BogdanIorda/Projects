import csv
import re
import time

from flask import Flask, render_template, request, send_file, redirect
from flask_sqlalchemy import SQLAlchemy

data_time = time.strftime("%y_%m_%d---%H_%M_%S")
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:Celmaitare1995@localhost/testdatabase"
db = SQLAlchemy(app)


def calculate_password_strength(password):
    """
    Calculeaza strength-ul parolei si returneaza unul din urmatoarele: "Missing Password", "Very Weak",
    "Weak", "Moderate" sau "Strong".
    """
    if password is None or not password:
        return "Missing Password"
    length = len(password)
    strength = 0

    if length < 8:
        return "Very Weak"
    else:
        strength += 1
    if any(char.isupper() for char in password):
        strength += 1
    if any(char.islower() for char in password):
        strength += 1
    if any(char.isdigit() for char in password):
        strength += 1
    if any(char.isascii() and not char.isalnum() for char in password):
        strength += 1
    if strength <= 3:
        return "Weak"
    elif strength == 4:
        return "Moderate"
    else:
        return "Strong"


class PasswordManager(db.Model):
    """
    Clasa reprezinta modelul pentru gestionarea datelor de parole stocate in baza de date.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(999), nullable=False)
    site_url = db.Column(db.String(999), nullable=False)
    site_password = db.Column(db.String(999), nullable=False)
    password_strength = db.Column(db.Integer, nullable=False)


# Routes
@app.route("/")
def index():
    """
    Ruta pentru afisarea paginii principale cu inregistrarile stocate ale parolelor.
    """
    password_list = PasswordManager.query.all()
    return render_template("index.html", password_list=password_list)


@app.route("/add", methods=["GET", "POST"])
def add_details():
    """
    Ruta pentru adaugarea de inregistrari noi ale parolelor în baza de date.
    """
    password_strength = 0
    error_message = None
    if request.method == "POST":
        email = request.form["email"]
        site_url = request.form["site_url"]
        site_password = request.form["site_password"]
        email_pattern = re.compile(r'\.(com|org|net)$')
        if not re.search(email_pattern, email.lower()):
            error_message = "Invalid email domain"
            password_list = PasswordManager.query.all()
            return render_template("index.html", password_list=password_list, password_strength=password_strength,
                                   error_message=error_message)
        website_pattern = re.compile(r'\.(com|org|net)$')
        if not re.search(website_pattern, site_url.lower()):
            error_message = "Invalid website domain"
            password_list = PasswordManager.query.all()
            return render_template("index.html", password_list=password_list, password_strength=password_strength,
                                   error_message=error_message)

        existing_entry = PasswordManager.query.filter(
            (PasswordManager.email == email) & (PasswordManager.site_url == site_url)
        ).first()

        if existing_entry:
            error_message = "An entry with the same email and site URL already exists in the database."
        else:
            password_strength = calculate_password_strength(site_password)

            new_password_details = PasswordManager(
                email=email, site_url=site_url, site_password=site_password, password_strength=password_strength
            )
            db.session.add(new_password_details)
            db.session.commit()

    password_list = PasswordManager.query.all()
    return render_template("index.html", password_list=password_list, password_strength=password_strength,
                           error_message=error_message)


@app.route("/update/<int:id>", methods=["GET", "POST"])
def update_details(id):
    """
    Ruta pentru actualizarea inregistrarilor existente ale parolelor in baza de date.
    """
    update_details = PasswordManager.query.get_or_404(id)
    password_strength = 0
    conflict_warning = False

    if request.method == "POST":
        new_email = request.form["email"]
        new_site_url = request.form["site_url"]
        new_site_password = request.form["site_password"]

        existing_entry = PasswordManager.query.filter(
            (PasswordManager.email == new_email) & (PasswordManager.site_url == new_site_url) & (
                    PasswordManager.id != id)
        ).first()

        if existing_entry:
            conflict_warning = "An entry with the same email and site URL already exists in the database."
        else:
            password_strength = calculate_password_strength(new_site_password)
            update_details.email = new_email
            update_details.site_url = new_site_url
            update_details.site_password = new_site_password
            update_details.password_strength = password_strength

            try:
                db.session.commit()
                return redirect("/")
            except:
                return "There was an error updating Password Details"

    return render_template("update.html", update_details=update_details, password_strength=password_strength,
                           conflict_warning=conflict_warning)


@app.route("/delete/<int:id>")
def delete_details(id):
    """
    Ruta pentru stergerea inregistrărilor de parole din baza de date.
    """
    new_details_to_delete = PasswordManager.query.get_or_404(id)
    try:
        db.session.delete(new_details_to_delete)
        db.session.commit()
        return redirect("/")
    except:
        return "There was an error deleting details"


@app.route('/export')
def export_data():
    """
    Ruta pentru exportul inregistrărilor din baza de date intr-un fisier CSV pentru backup.
    """
    with open('backup.csv', 'w') as f:
        out = csv.writer(f)
        out.writerow(['id', 'email', 'site_url', 'site_password'])
        for item in PasswordManager.query.all():
            out.writerow([item.id, item.email, item.site_url, item.site_password])
    return send_file('backup.csv',
                     mimetype='text/csv',
                     download_name=f"Export_Password_{data_time}.csv",
                     as_attachment=True)


if __name__ == "__main__":
    """
    Ruleaza aplicația Flask in modul de debug.
    """
    app.run(debug=True)
