from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv()

app = Flask(__name__)

app.permanent_session_lifetime = timedelta(days=365)

# =========================
# CONFIG
# =========================
app.config['SECRET_KEY'] = 'tinda-secret-key'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
}

db = SQLAlchemy(app)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

ADMIN_EMAILS = [
    "johnnsale54@gmail.com",
    "contact@gustaveshumbusho.com",
    "tindaexpress.cd@gmail.com"
]

ADMIN_PHONES = [
    "+243977492678",
    "+254710603313",
    "+243822385696"
]


# =========================
# MODELS
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(200), nullable=True)
    password = db.Column(db.String(300), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Parcel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref="parcels")

    # CATEGORY
    category = db.Column(db.String(100))

    # PICKUP
    pickup_ville = db.Column(db.String(200))
    pickup_commune = db.Column(db.String(200))
    pickup_avenue = db.Column(db.String(200))
    pickup_numero = db.Column(db.String(200))
    pickup_reference = db.Column(db.String(300))

    # DELIVERY
    delivery_ville = db.Column(db.String(200))
    delivery_commune = db.Column(db.String(200))
    delivery_avenue = db.Column(db.String(200))
    delivery_numero = db.Column(db.String(200))
    delivery_reference = db.Column(db.String(300))

    # RECEIVER
    receiver_name = db.Column(db.String(200))
    receiver_phone = db.Column(db.String(100))
    receiver_email = db.Column(db.String(200))

    # PARCEL
    parcel_name = db.Column(db.String(200))
    parcel_description = db.Column(db.Text)
    parcel_image = db.Column(db.Text)
    delivery_proof_image = db.Column(db.Text)

    # STATUS
    status = db.Column(db.String(100), default="En attente")


def create_admins():

    admins = [
        {
            "fullname": "Gustave",
            "phone": "+254710603313",
            "email": "contact@gustaveshumbusho.com",
            "password": "Tinda@2020"
        },
        {
            "fullname": "Petero Nsale",
            "phone": "+243977492678",
            "email": "johnnsale54@gmail.com",
            "password": "Tinda@2020"
        },
        {
            "fullname": "Tinda Express",
            "phone": "+243822385696",
            "email": "tindaexpress.cd@gmail.com",
            "password": "Tinda@2020"
        }
    ]

    for admin in admins:

        existing = User.query.filter_by(phone=admin["phone"]).first()

        if not existing:

            user = User(
                fullname=admin["fullname"],
                phone=admin["phone"],
                email=admin["email"],
                password=generate_password_hash(admin["password"]),
                is_admin=True
            )

            db.session.add(user)

    db.session.commit()


def normalize_phone(phone):

    phone = phone.replace(" ", "").replace("-", "")

    if phone.startswith("0"):
        phone = "+243" + phone[1:]
    elif phone.startswith("243"):
        phone = "+" + phone

    return phone


# =========================
# EMAIL CONTENT HELPERS
# =========================
def parcel_card_html(parcel, index, total):

    title = parcel.parcel_name or f"Colis {index}"

    if total > 1:
        title = f"Colis {index}/{total} • {title}"

    image_html = f'''
    <div style="margin-top:20px;">
        <img
            src="{parcel.parcel_image}"
            style="width:100%;border-radius:20px;object-fit:cover;"
        >
    </div>
    ''' if parcel.parcel_image else ''

    return f"""
    <div style="background:#fff7ed;border-radius:25px;padding:30px;margin-top:25px;">

        <h3 style="margin-top:0;color:#ff8a00;font-size:24px;">{title}</h3>

        <p style="color:#444;font-size:17px;line-height:1.8;">
            <strong>Catégorie :</strong> {parcel.category}
        </p>

        <p style="color:#444;font-size:17px;line-height:1.8;">
            <strong>Destinataire :</strong> {parcel.receiver_name} ({parcel.receiver_phone})
        </p>

        <p style="color:#444;font-size:17px;line-height:1.8;">
            <strong>Ramassage :</strong>
            {parcel.pickup_ville or ''}, {parcel.pickup_commune or ''}, {parcel.pickup_avenue or ''},
            N° {parcel.pickup_numero or ''}, {parcel.pickup_reference or ''}
        </p>

        <p style="color:#444;font-size:17px;line-height:1.8;">
            <strong>Livraison :</strong>
            {parcel.delivery_ville or ''}, {parcel.delivery_commune or ''}, {parcel.delivery_avenue or ''},
            N° {parcel.delivery_numero or ''}, {parcel.delivery_reference or ''}
        </p>

        {image_html}

    </div>
    """


def email_shell(header_badge, title, body_html, max_width=600):

    return f"""
    <div style="background:#f4f4f4;padding:30px 15px;font-family:Arial,sans-serif;">
        <div style="max-width:{max_width}px;margin:auto;background:white;border-radius:30px;overflow:hidden;box-shadow:0 5px 20px rgba(0,0,0,0.08);">

            <div style="background:#0b1220;padding:45px 30px;text-align:center;">
                <img
                    src="https://tinda-express-app.onrender.com/static/images/logo.png"
                    style="width:90px;height:90px;border-radius:50%;object-fit:cover;border:4px solid #ff8a00;margin-bottom:15px;background:white;"
                >
                <h1 style="color:white;margin:0;font-size:38px;">Tinda Express</h1>
                <div style="display:inline-block;margin-top:18px;background:#1b2435;color:#ffffff;padding:12px 22px;border-radius:30px;font-size:15px;font-weight:bold;">
                    {header_badge}
                </div>
            </div>

            <div style="padding:45px 30px;">
                <h2 style="font-size:34px;color:#111827;margin-top:0;line-height:1.3;">{title}</h2>
                <div style="width:90px;height:6px;background:#ff8a00;border-radius:10px;margin:25px 0;"></div>

                {body_html}

                <div style="margin-top:45px;text-align:center;">
                    <p style="color:#888;font-size:16px;line-height:1.8;">
                        Merci d’utiliser <strong>Tinda Express</strong>
                    </p>
                    <p style="color:#aaa;font-size:14px;margin-top:25px;">
                        Livraison rapide • Sécurisée • Intelligente
                    </p>
                </div>
            </div>
        </div>
    </div>
    """


# =========================
# SEND STATUS EMAIL (single parcel, admin updates status)
# =========================
def send_status_email(parcel):

    user = User.query.get(parcel.user_id)

    if not user or not user.email:
        return

    body = f"""
    <p style="font-size:18px;color:#555;line-height:1.7;">
        Bonjour <strong>{user.fullname}</strong>,
    </p>

    <p style="font-size:18px;color:#555;line-height:1.7;">
        Votre colis <strong>{parcel.parcel_name}</strong> a été mis à jour avec succès.
    </p>

    <div style="background:#f9fafb;border-radius:25px;padding:30px;margin-top:35px;text-align:center;">
        <p style="color:#777;font-size:15px;margin-bottom:18px;letter-spacing:1px;">STATUT DU COLIS</p>
        <div style="display:inline-block;background:#fff3df;color:#ff8a00;padding:14px 28px;border-radius:30px;font-size:20px;font-weight:bold;">
            {parcel.status}
        </div>
    </div>

    {f'''
    <div style="margin-top:35px;">
        <img src="{parcel.parcel_image}" style="width:100%;border-radius:25px;object-fit:cover;">
    </div>
    ''' if parcel.parcel_image else ''}

    {f'''
    <div style="margin-top:40px;background:#ecfdf3;border-radius:25px;padding:25px;">
        <h3 style="color:#16a34a;margin-top:0;font-size:24px;">Colis livré avec succès</h3>
        <p style="color:#444;line-height:1.7;">Votre colis a bien été remis au destinataire.</p>
        <img src="{parcel.delivery_proof_image}" style="width:100%;border-radius:20px;margin-top:20px;">
    </div>
    ''' if parcel.delivery_proof_image else ''}
    """

    msg = Message(
        subject=f"Tinda Express • {parcel.status}",
        sender=("Tinda Express", app.config['MAIL_USERNAME']),
        recipients=[user.email]
    )

    msg.html = email_shell("Notification de livraison", "Mise à jour de votre colis", body)
    mail.send(msg)


# =========================
# SEND ORDER CONFIRMATION (client, one or many parcels)
# =========================
def send_order_confirmation(user, parcels):

    if not user.email:
        return

    total = len(parcels)

    intro = "Nous avons bien reçu votre demande d’envoi pour :" if total == 1 \
        else f"Nous avons bien reçu vos {total} demandes d’envoi :"

    cards = "".join(
        parcel_card_html(p, i + 1, total) for i, p in enumerate(parcels)
    )

    body = f"""
    <p style="font-size:18px;color:#555;line-height:1.8;">
        Bonjour <strong>{user.fullname}</strong>,
    </p>

    <p style="font-size:18px;color:#555;line-height:1.8;">
        {intro}
    </p>

    {cards}

    <div style="margin-top:40px;background:#f9fafb;padding:25px;border-radius:20px;">
        <p style="color:#444;font-size:17px;line-height:1.8;margin:0;">
            Un agent <strong>Tinda Express</strong> vous contactera bientôt pour confirmer et prendre en charge
            {"vos colis" if total > 1 else "votre colis"}.
        </p>
    </div>
    """

    msg = Message(
        subject="Tinda Express • Demande reçue",
        sender=("Tinda Express", app.config['MAIL_USERNAME']),
        recipients=[user.email]
    )

    msg.html = email_shell("Demande reçue avec succès", "Merci d’avoir choisi Tinda Express \U0001f69a", body, max_width=600)
    mail.send(msg)


# =========================
# SEND ADMIN NEW ORDER EMAIL (one or many parcels)
# =========================
def send_admin_order_email(user, parcels):

    total = len(parcels)

    cards = "".join(
        parcel_card_html(p, i + 1, total) for i, p in enumerate(parcels)
    )

    body = f"""
    <div style="background:#f9fafb;border-radius:25px;padding:30px;margin-top:10px;">
        <h3 style="margin-top:0;color:#111827;font-size:24px;">Expéditeur</h3>
        <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Nom :</strong> {user.fullname}</p>
        <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Téléphone :</strong> {user.phone}</p>
        <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Email :</strong> {user.email or "-"}</p>
    </div>

    {cards}
    """

    title = "Nouvelle demande d’envoi \U0001f69a" if total == 1 else f"{total} nouvelles demandes d’envoi \U0001f69a"

    msg = Message(
        subject="Tinda Express • Nouvelle demande d’envoi",
        sender=("Tinda Express", app.config['MAIL_USERNAME']),
        recipients=ADMIN_EMAILS
    )

    msg.html = email_shell("Nouvelle demande reçue", title, body, max_width=700)
    mail.send(msg)


# =========================
# ROUTES
# =========================
@app.route("/")
def index():

    if "user_id" in session:

        user = User.query.get(session["user_id"])

        if user:

            if user.is_admin:
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        session.clear()

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form.get("fullname")
        phone = request.form.get("phone")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")

        clean_phone = normalize_phone(phone)

        users = User.query.all()

        for u in users:
            if normalize_phone(u.phone) == clean_phone:
                return render_template("register.html", error="Ce numéro existe déjà")

        new_user = User(
            fullname=fullname,
            phone=phone,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        session.permanent = True
        session["user_id"] = new_user.id

        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        phone = request.form.get("phone")
        password = request.form.get("password")

        clean_phone = normalize_phone(phone)

        users = User.query.all()
        user = next((u for u in users if normalize_phone(u.phone) == clean_phone), None)

        if not user or not check_password_hash(user.password, password):
            return render_template("login.html", error="Téléphone ou mot de passe incorrect")

        session.permanent = True
        session["user_id"] = user.id

        if user.is_admin:
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


@app.route("/create_parcel", methods=["POST"])
def create_parcel():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    categories = request.form.getlist("category[]")
    pickup_villes = request.form.getlist("pickup_ville[]")
    pickup_communes = request.form.getlist("pickup_commune[]")
    pickup_avenues = request.form.getlist("pickup_avenue[]")
    pickup_numeros = request.form.getlist("pickup_numero[]")
    pickup_references = request.form.getlist("pickup_reference[]")

    delivery_villes = request.form.getlist("delivery_ville[]")
    delivery_communes = request.form.getlist("delivery_commune[]")
    delivery_avenues = request.form.getlist("delivery_avenue[]")
    delivery_numeros = request.form.getlist("delivery_numero[]")
    delivery_references = request.form.getlist("delivery_reference[]")

    receiver_names = request.form.getlist("receiver_name[]")
    receiver_phones = request.form.getlist("receiver_phone[]")
    receiver_emails = request.form.getlist("receiver_email[]")

    parcel_names = request.form.getlist("parcel_name[]")
    parcel_descriptions = request.form.getlist("parcel_description[]")

    images = request.files.getlist("parcel_image[]")

    new_parcels = []

    for i in range(len(categories)):

        parcel_image_url = None

        image = images[i] if i < len(images) else None

        if image and image.filename != "":
            upload_result = cloudinary.uploader.upload(image)
            parcel_image_url = upload_result["secure_url"]

        new_parcel = Parcel(
            user_id=user.id,

            category=categories[i],

            pickup_ville=pickup_villes[i],
            pickup_commune=pickup_communes[i],
            pickup_avenue=pickup_avenues[i],
            pickup_numero=pickup_numeros[i],
            pickup_reference=pickup_references[i],

            delivery_ville=delivery_villes[i],
            delivery_commune=delivery_communes[i],
            delivery_avenue=delivery_avenues[i],
            delivery_numero=delivery_numeros[i],
            delivery_reference=delivery_references[i],

            receiver_name=receiver_names[i],
            receiver_phone=receiver_phones[i],
            receiver_email=receiver_emails[i] if i < len(receiver_emails) else None,

            parcel_name=parcel_names[i],
            parcel_description=parcel_descriptions[i] if i < len(parcel_descriptions) else None,

            parcel_image=parcel_image_url,

            status="En attente"
        )

        db.session.add(new_parcel)
        new_parcels.append(new_parcel)

    db.session.commit()

    send_order_confirmation(user, new_parcels)
    send_admin_order_email(user, new_parcels)

    return redirect(url_for("mes_envois"))


@app.route("/mes-envois")
def mes_envois():

    if "user_id" not in session:
        return redirect(url_for("login"))

    parcels = Parcel.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Parcel.id.desc()).all()

    return render_template("mes-envois.html", parcels=parcels)


@app.route("/profil")
def profil():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    return render_template("profil.html", user=user)


@app.route("/parcel/<int:parcel_id>")
def parcel_details(parcel_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    parcel = Parcel.query.filter_by(
        id=parcel_id,
        user_id=session["user_id"]
    ).first()

    if not parcel:
        return redirect(url_for("mes_envois"))

    return render_template("parcel-details.html", parcel=parcel)


@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user.is_admin:
        return "Accès refusé"

    parcels = Parcel.query.order_by(Parcel.id.desc()).all()

    return render_template("admin/dashboard.html", parcels=parcels)


@app.route("/admin/parcel/<int:parcel_id>", methods=["GET", "POST"])
def admin_parcel(parcel_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if user.email not in ADMIN_EMAILS and user.phone not in ADMIN_PHONES:
        return "Accès refusé"

    parcel = Parcel.query.get_or_404(parcel_id)

    if request.method == "POST":

        new_status = request.form.get("status")
        parcel.status = new_status

        proof_image = request.files.get("delivery_proof_image")

        if proof_image and proof_image.filename != "":
            upload_result = cloudinary.uploader.upload(proof_image)
            parcel.delivery_proof_image = upload_result["secure_url"]

        db.session.commit()

        send_status_email(parcel)

        return redirect(url_for("admin_parcel", parcel_id=parcel.id))

    return render_template("admin/parcel.html", parcel=parcel)


# =========================
# RUN
# =========================

with app.app_context():
    db.create_all()
    create_admins()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
