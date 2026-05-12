from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import timedelta
import json

from pywebpush import (
    webpush,
    WebPushException
)




load_dotenv()

app = Flask(__name__)

app.permanent_session_lifetime = timedelta(
    days=365
)

app.permanent_session_lifetime = timedelta(days=365)


app.config["VAPID_PUBLIC_KEY"] = os.getenv(
    "VAPID_PUBLIC_KEY"
)

app.config["VAPID_PRIVATE_KEY"] = os.getenv(
    "VAPID_PRIVATE_KEY"
)

# =========================
# CONFIG
# =========================
app.config['SECRET_KEY'] = 'tinda-secret-key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL") 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app.secret_key = "tinda-secret-key"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

# =========================
# USER MODEL
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    fullname = db.Column(db.String(200), nullable=False)

    phone = db.Column(db.String(50), unique=True, nullable=False)

    email = db.Column(db.String(200), nullable=True)

    password = db.Column(db.String(300), nullable=False)

    is_admin = db.Column(
    db.Boolean,
    default=False
    )


# =========================
# PARCEL MODEL
# =========================
class Parcel(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

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
    user = db.relationship(
    "User",
    backref="parcels"
    )
    # PARCEL
    parcel_name = db.Column(db.String(200))

    parcel_description = db.Column(db.Text)

    parcel_image = db.Column(db.Text)

    delivery_proof_image = db.Column(db.Text)

    # STATUS
    status = db.Column(
        db.String(100),
        default="En attente"
    )

class PushSubscription(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    subscription = db.Column(
        db.Text
    )    

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

        existing = User.query.filter_by(
            phone=admin["phone"]
        ).first()

        if not existing:

            user = User(

                fullname=admin["fullname"],

                phone=admin["phone"],

                email=admin["email"],

                password=generate_password_hash(
                    admin["password"]
                ),

                is_admin=True

            )

            db.session.add(user)

    db.session.commit()
# =========================
# SEND STATUS EMAIL
# =========================
def send_status_email(parcel):

    # =========================
    # GET ACCOUNT OWNER
    # =========================
    user = User.query.get(parcel.user_id)

    # NO USER EMAIL
    if not user or not user.email:
        return

    subject = f"Tinda Express • {parcel.status}"

    html = f"""

    <div style="
        background:#f4f4f4;
        padding:30px 15px;
        font-family:Arial,sans-serif;
    ">

        <div style="
            max-width:600px;
            margin:auto;
            background:white;
            border-radius:30px;
            overflow:hidden;
            box-shadow:0 5px 20px rgba(0,0,0,0.08);
        ">

            <!-- HEADER -->
            <div style="
                background:#0b1220;
                padding:40px 30px;
                text-align:center;
            ">

                <img
                    src='https://tinda-express-app.onrender.com/static/images/logo.png'
                    style='
                        width:90px;
                        height:90px;
                        border-radius:50%;
                        object-fit:cover;
                        border:4px solid #ff8a00;
                        margin-bottom:15px;
                        background:white;
                    '
                >

                <h1 style="
                    color:white;
                    margin:0;
                    font-size:38px;
                ">
                    Tinda Express
                </h1>

                <div style="
                    display:inline-block;
                    margin-top:18px;
                    background:#1b2435;
                    color:#ffffff;
                    padding:12px 22px;
                    border-radius:30px;
                    font-size:15px;
                    font-weight:bold;
                ">
                    Notification de livraison
                </div>

            </div>

            <!-- CONTENT -->
            <div style="
                padding:40px 30px;
            ">

                <h2 style="
                    font-size:38px;
                    line-height:1.3;
                    margin-top:0;
                    color:#111827;
                ">
                    Mise à jour de votre colis
                </h2>

                <div style="
                    width:90px;
                    height:6px;
                    background:#ff8a00;
                    border-radius:10px;
                    margin:25px 0;
                "></div>

                <p style="
                    font-size:18px;
                    color:#555;
                    line-height:1.7;
                ">
                    Bonjour
                    <strong>{user.fullname}</strong>,
                </p>

                <p style="
                    font-size:18px;
                    color:#555;
                    line-height:1.7;
                ">
                    Votre colis :
                </p>

                <h3 style="
                    font-size:30px;
                    color:#111827;
                    margin-top:10px;
                ">
                    {parcel.parcel_name}
                </h3>

                <p style="
                    font-size:18px;
                    color:#555;
                    line-height:1.7;
                ">
                    a été mis à jour avec succès.
                </p>

                <!-- STATUS -->
                <div style="
                    background:#f9fafb;
                    border-radius:25px;
                    padding:30px;
                    margin-top:35px;
                    text-align:center;
                ">

                    <p style="
                        color:#777;
                        font-size:15px;
                        margin-bottom:18px;
                        letter-spacing:1px;
                    ">
                        STATUT DU COLIS
                    </p>

                    <div style="
                        display:inline-block;
                        background:#fff3df;
                        color:#ff8a00;
                        padding:14px 28px;
                        border-radius:30px;
                        font-size:20px;
                        font-weight:bold;
                    ">
                        {parcel.status}
                    </div>

                </div>

                <!-- PARCEL IMAGE -->
                {f'''
                <div style="margin-top:35px;">

                    <img
                        src="{parcel.parcel_image}"
                        style="
                            width:100%;
                            border-radius:25px;
                            object-fit:cover;
                        "
                    >

                </div>
                ''' if parcel.parcel_image else ''}

                <!-- DELIVERY PROOF -->
                {f'''
                <div style="
                    margin-top:40px;
                    background:#ecfdf3;
                    border-radius:25px;
                    padding:25px;
                ">

                    <h3 style="
                        color:#16a34a;
                        margin-top:0;
                        font-size:24px;
                    ">
                        Colis livré avec succès
                    </h3>

                    <p style="
                        color:#444;
                        line-height:1.7;
                    ">
                        Votre colis a bien été remis au destinataire.
                    </p>

                    <img
                        src="{parcel.delivery_proof_image}"
                        style="
                            width:100%;
                            border-radius:20px;
                            margin-top:20px;
                        "
                    >

                </div>
                ''' if hasattr(parcel, 'delivery_proof_image') and parcel.delivery_proof_image else ''}

                <!-- FOOTER -->
                <div style="
                    margin-top:45px;
                    text-align:center;
                ">

                    <p style="
                        color:#888;
                        font-size:16px;
                        line-height:1.8;
                    ">
                        Merci d’utiliser
                        <strong>Tinda Express</strong>
                    </p>

                    <p style="
                        color:#aaa;
                        font-size:14px;
                        margin-top:25px;
                    ">
                        Livraison rapide • Sécurisée • Intelligente
                    </p>

                </div>

            </div>

        </div>

    </div>

    """

    msg = Message(

        subject=subject,

        sender=(
            "Tinda Express",
            app.config['MAIL_USERNAME']
        ),

        recipients=[user.email]

    )

    msg.html = html

    mail.send(msg)  

# =========================
# SEND ORDER CONFIRMATION
# =========================
def send_order_confirmation(parcel):

    # =========================
    # GET ACCOUNT OWNER
    # =========================
    user = User.query.get(parcel.user_id)

    # NO USER OR EMAIL
    if not user or not user.email:
        return

    subject = "Tinda Express • Demande reçue"

    html = f"""

    <div style="
        background:#f4f4f4;
        padding:30px 15px;
        font-family:Arial,sans-serif;
    ">

        <div style="
            max-width:600px;
            margin:auto;
            background:white;
            border-radius:30px;
            overflow:hidden;
            box-shadow:0 5px 20px rgba(0,0,0,0.08);
        ">

            <!-- HEADER -->
            <div style="
                background:#0b1220;
                padding:45px 30px;
                text-align:center;
            ">

                <img
                    src='https://tinda-express-app.onrender.com/static/images/logo.png'
                    style='
                        width:90px;
                        height:90px;
                        border-radius:50%;
                        object-fit:cover;
                        border:4px solid #ff8a00;
                        margin-bottom:15px;
                        background:white;
                    '
                >

                <h1 style="
                    color:white;
                    margin:0;
                    font-size:38px;
                ">
                    Tinda Express
                </h1>

                <div style="
                    display:inline-block;
                    margin-top:18px;
                    background:#1b2435;
                    color:#ffffff;
                    padding:12px 22px;
                    border-radius:30px;
                    font-size:15px;
                    font-weight:bold;
                ">
                    Demande reçue avec succès
                </div>

            </div>

            <!-- BODY -->
            <div style="
                padding:45px 30px;
            ">

                <h2 style="
                    font-size:36px;
                    color:#111827;
                    margin-top:0;
                    line-height:1.3;
                ">
                    Merci d’avoir choisi
                    Tinda Express 🚚
                </h2>

                <div style="
                    width:90px;
                    height:6px;
                    background:#ff8a00;
                    border-radius:10px;
                    margin:25px 0;
                "></div>

                <p style="
                    font-size:18px;
                    color:#555;
                    line-height:1.8;
                ">

                    Bonjour
                    <strong>{user.fullname}</strong>,

                </p>

                <p style="
                    font-size:18px;
                    color:#555;
                    line-height:1.8;
                ">

                    Nous avons bien reçu votre
                    demande d’envoi pour :

                </p>

                <!-- PARCEL -->
                <div style="
                    background:#fff7ed;
                    border-radius:25px;
                    padding:30px;
                    margin-top:25px;
                ">

                    <h3 style="
                        margin-top:0;
                        color:#ff8a00;
                        font-size:28px;
                    ">
                        {parcel.parcel_name}
                    </h3>

                    <p style="
                        color:#444;
                        font-size:17px;
                        line-height:1.8;
                    ">

                        Destinataire :
                        <strong>
                            {parcel.receiver_name}
                        </strong>

                    </p>

                    <p style="
                        color:#444;
                        font-size:17px;
                        line-height:1.8;
                    ">

                        Livraison :

                        <strong>

                            {parcel.delivery_ville or ''}

                            {parcel.delivery_commune or ''}

                            {parcel.delivery_avenue or ''}

                            {parcel.delivery_numero or ''}

                            {parcel.delivery_reference or ''}

                        </strong>

                    </p>

                </div>

                <!-- IMAGE -->
                {f'''
                <div style="margin-top:35px;">

                    <img
                        src="{parcel.parcel_image}"
                        style="
                            width:100%;
                            border-radius:25px;
                            object-fit:cover;
                        "
                    >

                </div>
                ''' if parcel.parcel_image else ''}

                <!-- INFO -->
                <div style="
                    margin-top:40px;
                    background:#f9fafb;
                    padding:25px;
                    border-radius:20px;
                ">

                    <p style="
                        color:#444;
                        font-size:17px;
                        line-height:1.8;
                        margin:0;
                    ">

                        Un agent
                        <strong>Tinda Express</strong>
                        vous contactera bientôt pour
                        confirmer et prendre en charge
                        votre colis.

                    </p>

                </div>

                <!-- FOOTER -->
                <div style="
                    margin-top:45px;
                    text-align:center;
                ">

                    <p style="
                        color:#888;
                        font-size:16px;
                        line-height:1.8;
                    ">

                        Merci d’utiliser
                        <strong>Tinda Express</strong>

                    </p>

                    <p style="
                        color:#aaa;
                        font-size:14px;
                        margin-top:25px;
                    ">

                        Livraison rapide • Sécurisée • Intelligente

                    </p>

                </div>

            </div>

        </div>

    </div>

    """

    msg = Message(

        subject=subject,

        sender=(
            "Tinda Express",
            app.config['MAIL_USERNAME']
        ),

        recipients=[user.email]

    )

    msg.html = html

    mail.send(msg)


# =========================
# SEND ADMIN NEW ORDER EMAIL
# =========================
def send_admin_order_email(parcel):

    # =========================
    # GET USER
    # =========================
    user = User.query.get(parcel.user_id)

    if not user:
        return

    # =========================
    # ADMIN EMAILS
    # =========================
    admin_emails = [
        "johnnsale54@gmail.com",
        "contact@gustaveshumbusho.com",
        "tindaexpress.cd@gmail.com"
    ]

    subject = "Tinda Express • Nouvelle demande d’envoi"

    html = f"""

    <div style="
        background:#f4f4f4;
        padding:30px 15px;
        font-family:Arial,sans-serif;
    ">

        <div style="
            max-width:700px;
            margin:auto;
            background:white;
            border-radius:30px;
            overflow:hidden;
            box-shadow:0 5px 20px rgba(0,0,0,0.08);
        ">

            <!-- HEADER -->
            <div style="
                background:#0b1220;
                padding:45px 30px;
                text-align:center;
            ">

                <img
                    src="https://tinda-express-app.onrender.com/static/images/logo.png"
                    style="
                        width:90px;
                        height:90px;
                        border-radius:50%;
                        background:white;
                        padding:5px;
                        object-fit:cover;
                        border:4px solid #ff8a00;
                        margin-bottom:15px;
                    "
                >

                <h1 style="
                    color:white;
                    margin:0;
                    font-size:38px;
                ">
                    Tinda Express
                </h1>

                <div style="
                    display:inline-block;
                    margin-top:18px;
                    background:#1b2435;
                    color:#ffffff;
                    padding:12px 24px;
                    border-radius:30px;
                    font-size:15px;
                    font-weight:bold;
                ">
                    Nouvelle demande reçue
                </div>

            </div>

            <!-- BODY -->
            <div style="
                padding:40px 30px;
            ">

                <h2 style="
                    font-size:34px;
                    color:#111827;
                    margin-top:0;
                ">
                    Nouvelle demande d’envoi 🚚
                </h2>

                <div style="
                    width:90px;
                    height:6px;
                    background:#ff8a00;
                    border-radius:10px;
                    margin:25px 0;
                "></div>

                <!-- USER -->
                <div style="
                    background:#f9fafb;
                    border-radius:25px;
                    padding:30px;
                    margin-top:30px;
                ">

                    <h3 style="
                        margin-top:0;
                        color:#111827;
                        font-size:24px;
                    ">
                        Expéditeur
                    </h3>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">
                        <strong>Nom :</strong>
                        {user.fullname}
                    </p>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">
                        <strong>Téléphone :</strong>
                        {user.phone}
                    </p>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">
                        <strong>Email :</strong>
                        {user.email or "-"}
                    </p>

                </div>

                <!-- PARCEL -->
                <div style="
                    background:#fff7ed;
                    border-radius:25px;
                    padding:30px;
                    margin-top:30px;
                ">

                    <h3 style="
                        margin-top:0;
                        color:#ff8a00;
                        font-size:24px;
                    ">
                        Détails du colis
                    </h3>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">
                        <strong>Nom du colis :</strong>
                        {parcel.parcel_name}
                    </p>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">
                        <strong>Catégorie :</strong>
                        {parcel.category}
                    </p>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">
                        <strong>Destinataire :</strong>
                        {parcel.receiver_name}
                    </p>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">
                        <strong>Téléphone :</strong>
                        {parcel.receiver_phone}
                    </p>

                </div>

                <!-- PICKUP -->
                <div style="
                    background:#f9fafb;
                    border-radius:25px;
                    padding:30px;
                    margin-top:30px;
                ">

                    <h3 style="
                        margin-top:0;
                        color:#111827;
                        font-size:24px;
                    ">
                        Ramassage
                    </h3>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">

                        {parcel.pickup_ville or ''},
                        {parcel.pickup_commune or ''},
                        {parcel.pickup_avenue or ''},
                        N° {parcel.pickup_numero or ''},
                        {parcel.pickup_reference or ''}

                    </p>

                </div>

                <!-- DELIVERY -->
                <div style="
                    background:#f9fafb;
                    border-radius:25px;
                    padding:30px;
                    margin-top:30px;
                ">

                    <h3 style="
                        margin-top:0;
                        color:#111827;
                        font-size:24px;
                    ">
                        Livraison
                    </h3>

                    <p style="
                        font-size:17px;
                        line-height:1.8;
                        color:#444;
                    ">

                        {parcel.delivery_ville or ''},
                        {parcel.delivery_commune or ''},
                        {parcel.delivery_avenue or ''},
                        N° {parcel.delivery_numero or ''},
                        {parcel.delivery_reference or ''}

                    </p>

                </div>

                <!-- PARCEL IMAGE -->
                {f'''
                <div style="margin-top:35px;">

                    <img
                        src="{parcel.parcel_image}"
                        style="
                            width:100%;
                            border-radius:25px;
                            object-fit:cover;
                        "
                    >

                </div>
                ''' if parcel.parcel_image else ''}

                <!-- FOOTER -->
                <div style="
                    margin-top:45px;
                    text-align:center;
                ">

                    <p style="
                        color:#888;
                        font-size:16px;
                        line-height:1.8;
                    ">
                        Tableau de bord administratif
                        <strong>Tinda Express</strong>
                    </p>

                    <p style="
                        color:#aaa;
                        font-size:14px;
                        margin-top:25px;
                    ">
                        Livraison rapide • Sécurisée • Intelligente
                    </p>

                </div>

            </div>

        </div>

    </div>

    """

    msg = Message(

        subject=subject,

        sender=(
            "Tinda Express",
            app.config['MAIL_USERNAME']
        ),

        recipients=admin_emails

    )

    msg.html = html

    mail.send(msg)              

# =========================
# ROUTES
# =========================
@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    # BLOCK NON ADMINS
    if not user.is_admin:
        return "Accès refusé"

    parcels = Parcel.query.order_by(
        Parcel.id.desc()
    ).all()

    return render_template(
        "admin/dashboard.html",
        parcels=parcels
    )

@app.route("/admin/parcel/<int:parcel_id>", methods=["GET", "POST"])
def admin_parcel(parcel_id):

    # LOGIN REQUIRED
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    # ADMIN SECURITY
    if (
        user.email not in ADMIN_EMAILS
        and user.phone not in ADMIN_PHONES
    ):

        return "Accès refusé"

    # GET PARCEL
    parcel = Parcel.query.get_or_404(parcel_id)

    # ====================================
    # UPDATE PARCEL
    # ====================================

    if request.method == "POST":

        # NEW STATUS
        new_status = request.form.get("status")

        parcel.status = new_status

        # ====================================
        # DELIVERY PROOF IMAGE
        # ====================================

        proof_image = request.files.get(
            "delivery_proof_image"
        )

        if (
            proof_image
            and proof_image.filename != ""
        ):

            upload_result = cloudinary.uploader.upload(
                proof_image
            )

            parcel.delivery_proof_image = (
                upload_result["secure_url"]
            )

        # SAVE
        db.session.commit()

        send_push_notification(

            parcel.user_id,

            "Tinda Express",

            f"Votre colis est maintenant : {parcel.status}"

        )
        # SEND EMAIL
        send_status_email(parcel)

        return redirect(
            url_for(
                "admin_parcel",
                parcel_id=parcel.id
            )
        )

    return render_template(
        "admin/parcel.html",
        parcel=parcel
    )    

@app.route("/")
def index():

    if "user_id" in session:

        user = User.query.get(
            session["user_id"]
        )

        # VALID USER
        if user:

            # ADMIN
            if user.is_admin:

                return redirect(
                    url_for("admin_dashboard")
                )

            # NORMAL USER
            return redirect(
                url_for("dashboard")
            )

        # INVALID SESSION
        session.clear()

    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form.get("fullname")
        phone = normalize_phone(
        request.form.get("phone")
        )
        email = request.form.get(
            "email",
            ""
        ).strip().lower()
        password = request.form.get("password")

        # CLEAN PHONE
        clean_phone = normalize_phone(phone)

        # CHECK EXISTING USER
        users = User.query.all()

        for u in users:

            db_phone = normalize_phone(u.phone)

            if db_phone == clean_phone:

                return render_template(
                    "register.html",
                    error="Ce numéro existe déjà"
                )

        # CREATE USER
        new_user = User(

            fullname=fullname,

            phone=phone,

            email=email,

            password=generate_password_hash(password)

        )

        db.session.add(new_user)

        db.session.commit()
        session.permanent = True
        # LOGIN USER
        session["user_id"] = new_user.id

        return redirect(
            url_for("dashboard")
        )

    return render_template("register.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )    

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        # INPUTS
        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # NORMALIZE PHONE
        clean_phone = normalize_phone(phone)

        # FIND USER
        users = User.query.all()

        user = None

        for u in users:

            db_phone = normalize_phone(u.phone)

            if db_phone == clean_phone:

                user = u
                break

        # USER NOT FOUND
        if not user:

            return render_template(
                "login.html",
                error="Compte introuvable"
            )

        # WRONG PASSWORD
        if not check_password_hash(
            user.password,
            password
        ):

            return render_template(
                "login.html",
                error="Mot de passe incorrect"
            )
        
        session.permanent = True
        # LOGIN SUCCESS
        session["user_id"] = user.id

        # ADMIN
        if user.is_admin:

            session["is_admin"] = True

            return redirect(
                url_for("admin_dashboard")
            )

        # NORMAL USER
        return redirect(
            url_for("dashboard")
        )

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    parcels = Parcel.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Parcel.id.desc()).all()

    return render_template(
        "dashboard.html",
        parcels=parcels
    )


@app.route("/create_parcel", methods=["POST"])
def create_parcel():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # CATEGORY
    category = request.form.get("category")

    # PICKUP
    pickup_ville = request.form.get("pickup_ville")
    pickup_commune = request.form.get("pickup_commune")
    pickup_avenue = request.form.get("pickup_avenue")
    pickup_numero = request.form.get("pickup_numero")
    pickup_reference = request.form.get("pickup_reference")

    # DELIVERY
    delivery_ville = request.form.get("delivery_ville")
    delivery_commune = request.form.get("delivery_commune")
    delivery_avenue = request.form.get("delivery_avenue")
    delivery_numero = request.form.get("delivery_numero")
    delivery_reference = request.form.get("delivery_reference")

    # RECEIVER
    receiver_name = request.form.get("receiver_name")
    receiver_phone = request.form.get("receiver_phone")
    receiver_email = request.form.get("receiver_email")

    # PARCEL
    parcel_name = request.form.get("parcel_name")
    parcel_description = request.form.get("parcel_description")

    # =================================
    # CLOUDINARY IMAGE UPLOAD
    # =================================

    image = request.files.get("parcel_image")

    parcel_image_url = None

    if image and image.filename != "":

        upload_result = cloudinary.uploader.upload(image)

        parcel_image_url = upload_result["secure_url"]

    # =================================
    # SAVE PARCEL
    # =================================

    new_parcel = Parcel(

        user_id=session["user_id"],

        category=category,

        pickup_ville=pickup_ville,
        pickup_commune=pickup_commune,
        pickup_avenue=pickup_avenue,
        pickup_numero=pickup_numero,
        pickup_reference=pickup_reference,

        delivery_ville=delivery_ville,
        delivery_commune=delivery_commune,
        delivery_avenue=delivery_avenue,
        delivery_numero=delivery_numero,
        delivery_reference=delivery_reference,

        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        receiver_email=receiver_email,

        parcel_name=parcel_name,
        parcel_description=parcel_description,

        # SAVE CLOUDINARY URL
        parcel_image=parcel_image_url,

        status="En attente"

    )

    db.session.add(new_parcel)

    db.session.commit()

    send_push_notification(

        session["user_id"],

        "Tinda Express",

        "Votre demande a été envoyée avec succès 🚚"

    )
    # SEND CONFIRMATION EMAIL
    send_order_confirmation(new_parcel)
    send_admin_order_email(new_parcel)

    return redirect(url_for("mes_envois"))

@app.route("/mes-envois")
def mes_envois():

    if "user_id" not in session:
        return redirect(url_for("login"))

    parcels = Parcel.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Parcel.id.desc()).all()

    return render_template(
        "mes-envois.html",
        parcels=parcels
    )


@app.route("/profil")
def profil():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    return render_template(
        "profil.html",
        user=user
    ) 


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

    return render_template(
        "parcel-details.html",
        parcel=parcel
    ) 

def normalize_phone(phone):

    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
    )

    # 0991234567 -> +243991234567
    if phone.startswith("0"):
        phone = "+243" + phone[1:]

    # 243991234567 -> +243991234567
    elif phone.startswith("243"):
        phone = "+" + phone

    return phone          

@app.route(
    "/save-subscription",
    methods=["POST"]
)
def save_subscription():

    if "user_id" not in session:
        return {"success": False}

    data = request.json

    existing = PushSubscription.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if existing:

        existing.subscription = json.dumps(data)

    else:

        sub = PushSubscription(

            user_id=session["user_id"],

            subscription=json.dumps(data)

        )

        db.session.add(sub)

    db.session.commit()

    return {"success": True}

def send_push_notification(
    user_id,
    title,
    body
):

    subscriptions = PushSubscription.query.filter_by(
        user_id=user_id
    ).all()

    for sub in subscriptions:

        try:

            webpush(

                subscription_info=json.loads(
                    sub.subscription
                ),

                data=json.dumps({

                    "title": title,

                    "body": body

                }),

                vapid_private_key=app.config[
                    "VAPID_PRIVATE_KEY"
                ],

                vapid_claims={
                    "sub":
                    "mailto:contact@gustaveshumbusho.com"
                }

            )

        except Exception as e:

            print(e)    

# =========================
# RUN
# =========================

with app.app_context():

    db.create_all()

    create_admins()

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )