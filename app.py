from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import uuid
import mimetypes

load_dotenv()

app = Flask(__name__)

# =========================
# CONFIG
# =========================
app.config['SECRET_KEY'] = 'tinda-secret-key'

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

PARCEL_IMAGE_CID = "colis_image"


# =========================
# EMAIL HELPERS
# =========================
def attach_inline_image(msg, image_path, cid):
    if not image_path or not os.path.exists(image_path):
        return

    content_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"

    with open(image_path, "rb") as f:
        msg.attach(
            filename=os.path.basename(image_path),
            content_type=content_type,
            data=f.read(),
            disposition="inline",
            headers={"Content-ID": f"<{cid}>"}
        )


def parcel_image_html(image_path):
    if not image_path:
        return ""

    return f'''
    <div style="margin-top:35px;">
        <img
            src="cid:{PARCEL_IMAGE_CID}"
            style="
                width:100%;
                border-radius:25px;
                object-fit:cover;
            "
        >
    </div>
    '''


# =========================
# SEND ORDER CONFIRMATION (CLIENT)
# =========================
def send_order_confirmation(sender_name, sender_email, parcel_name, receiver_name,
                             delivery_ville, delivery_commune, delivery_avenue,
                             delivery_numero, delivery_reference, image_path=None):

    if not sender_email:
        return

    subject = "Tinda Express • Demande reçue"

    html = f"""
    <div style="background:#f4f4f4;padding:30px 15px;font-family:Arial,sans-serif;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:30px;overflow:hidden;box-shadow:0 5px 20px rgba(0,0,0,0.08);">

            <div style="background:#0b1220;padding:45px 30px;text-align:center;">
                <img
                    src="https://tinda-express-app.onrender.com/static/images/logo.png"
                    style="width:90px;height:90px;border-radius:50%;object-fit:cover;border:4px solid #ff8a00;margin-bottom:15px;background:white;"
                >
                <h1 style="color:white;margin:0;font-size:38px;">Tinda Express</h1>
                <div style="display:inline-block;margin-top:18px;background:#1b2435;color:#ffffff;padding:12px 22px;border-radius:30px;font-size:15px;font-weight:bold;">
                    Demande reçue avec succès
                </div>
            </div>

            <div style="padding:45px 30px;">
                <h2 style="font-size:36px;color:#111827;margin-top:0;line-height:1.3;">
                    Merci d’avoir choisi Tinda Express 🚚
                </h2>

                <div style="width:90px;height:6px;background:#ff8a00;border-radius:10px;margin:25px 0;"></div>

                <p style="font-size:18px;color:#555;line-height:1.8;">
                    Bonjour <strong>{sender_name}</strong>,
                </p>

                <p style="font-size:18px;color:#555;line-height:1.8;">
                    Nous avons bien reçu votre demande d’envoi pour :
                </p>

                <div style="background:#fff7ed;border-radius:25px;padding:30px;margin-top:25px;">
                    <h3 style="margin-top:0;color:#ff8a00;font-size:28px;">{parcel_name}</h3>
                    <p style="color:#444;font-size:17px;line-height:1.8;">
                        Destinataire : <strong>{receiver_name}</strong>
                    </p>
                    <p style="color:#444;font-size:17px;line-height:1.8;">
                        Livraison :
                        <strong>
                            {delivery_ville or ''} {delivery_commune or ''} {delivery_avenue or ''} {delivery_numero or ''} {delivery_reference or ''}
                        </strong>
                    </p>
                </div>

                {parcel_image_html(image_path)}

                <div style="margin-top:40px;background:#f9fafb;padding:25px;border-radius:20px;">
                    <p style="color:#444;font-size:17px;line-height:1.8;margin:0;">
                        Un agent <strong>Tinda Express</strong> vous contactera bientôt pour confirmer et prendre en charge votre colis.
                    </p>
                </div>

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

    msg = Message(
        subject=subject,
        sender=("Tinda Express", app.config['MAIL_USERNAME']),
        recipients=[sender_email]
    )

    msg.html = html
    attach_inline_image(msg, image_path, PARCEL_IMAGE_CID)
    mail.send(msg)


# =========================
# SEND ADMIN NEW ORDER EMAIL
# =========================
def send_admin_order_email(sender_name, sender_phone, sender_email, category,
                            pickup_ville, pickup_commune, pickup_avenue, pickup_numero, pickup_reference,
                            delivery_ville, delivery_commune, delivery_avenue, delivery_numero, delivery_reference,
                            receiver_name, receiver_phone, parcel_name, image_path=None):

    subject = "Tinda Express • Nouvelle demande d’envoi"

    html = f"""
    <div style="background:#f4f4f4;padding:30px 15px;font-family:Arial,sans-serif;">
        <div style="max-width:700px;margin:auto;background:white;border-radius:30px;overflow:hidden;box-shadow:0 5px 20px rgba(0,0,0,0.08);">

            <div style="background:#0b1220;padding:45px 30px;text-align:center;">
                <img
                    src="https://tinda-express-app.onrender.com/static/images/logo.png"
                    style="width:90px;height:90px;border-radius:50%;background:white;padding:5px;object-fit:cover;border:4px solid #ff8a00;margin-bottom:15px;"
                >
                <h1 style="color:white;margin:0;font-size:38px;">Tinda Express</h1>
                <div style="display:inline-block;margin-top:18px;background:#1b2435;color:#ffffff;padding:12px 24px;border-radius:30px;font-size:15px;font-weight:bold;">
                    Nouvelle demande reçue
                </div>
            </div>

            <div style="padding:40px 30px;">
                <h2 style="font-size:34px;color:#111827;margin-top:0;">Nouvelle demande d’envoi 🚚</h2>
                <div style="width:90px;height:6px;background:#ff8a00;border-radius:10px;margin:25px 0;"></div>

                <div style="background:#f9fafb;border-radius:25px;padding:30px;margin-top:30px;">
                    <h3 style="margin-top:0;color:#111827;font-size:24px;">Expéditeur</h3>
                    <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Nom :</strong> {sender_name}</p>
                    <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Téléphone :</strong> {sender_phone}</p>
                    <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Email :</strong> {sender_email or "-"}</p>
                </div>

                <div style="background:#fff7ed;border-radius:25px;padding:30px;margin-top:30px;">
                    <h3 style="margin-top:0;color:#ff8a00;font-size:24px;">Détails du colis</h3>
                    <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Nom du colis :</strong> {parcel_name}</p>
                    <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Catégorie :</strong> {category}</p>
                    <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Destinataire :</strong> {receiver_name}</p>
                    <p style="font-size:17px;line-height:1.8;color:#444;"><strong>Téléphone :</strong> {receiver_phone}</p>
                </div>

                <div style="background:#f9fafb;border-radius:25px;padding:30px;margin-top:30px;">
                    <h3 style="margin-top:0;color:#111827;font-size:24px;">Ramassage</h3>
                    <p style="font-size:17px;line-height:1.8;color:#444;">
                        {pickup_ville or ''}, {pickup_commune or ''}, {pickup_avenue or ''}, N° {pickup_numero or ''}, {pickup_reference or ''}
                    </p>
                </div>

                <div style="background:#f9fafb;border-radius:25px;padding:30px;margin-top:30px;">
                    <h3 style="margin-top:0;color:#111827;font-size:24px;">Livraison</h3>
                    <p style="font-size:17px;line-height:1.8;color:#444;">
                        {delivery_ville or ''}, {delivery_commune or ''}, {delivery_avenue or ''}, N° {delivery_numero or ''}, {delivery_reference or ''}
                    </p>
                </div>

                {parcel_image_html(image_path)}

                <div style="margin-top:45px;text-align:center;">
                    <p style="color:#888;font-size:16px;line-height:1.8;">
                        Notification automatique <strong>Tinda Express</strong>
                    </p>
                    <p style="color:#aaa;font-size:14px;margin-top:25px;">
                        Livraison rapide • Sécurisée • Intelligente
                    </p>
                </div>
            </div>
        </div>
    </div>
    """

    msg = Message(
        subject=subject,
        sender=("Tinda Express", app.config['MAIL_USERNAME']),
        recipients=ADMIN_EMAILS
    )

    msg.html = html
    attach_inline_image(msg, image_path, PARCEL_IMAGE_CID)
    mail.send(msg)


# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/envoyer", methods=["GET", "POST"])
def envoyer():
    if request.method == "POST":

        category = request.form.get("category")

        pickup_ville = request.form.get("pickup_ville")
        pickup_commune = request.form.get("pickup_commune")
        pickup_avenue = request.form.get("pickup_avenue")
        pickup_numero = request.form.get("pickup_numero")
        pickup_reference = request.form.get("pickup_reference")

        delivery_ville = request.form.get("delivery_ville")
        delivery_commune = request.form.get("delivery_commune")
        delivery_avenue = request.form.get("delivery_avenue")
        delivery_numero = request.form.get("delivery_numero")
        delivery_reference = request.form.get("delivery_reference")

        sender_name = request.form.get("sender_name")
        sender_phone = request.form.get("sender_phone")
        sender_email = request.form.get("sender_email", "").strip().lower() or None

        receiver_name = request.form.get("receiver_name")
        receiver_phone = request.form.get("receiver_phone")

        parcel_name = request.form.get("parcel_name")

        image = request.files.get("parcel_image")

        if not image or image.filename == "":
            return render_template("envoyer.html", error="Veuillez ajouter une photo du colis")

        unique_name = str(uuid.uuid4()) + "_" + secure_filename(image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        image.save(image_path)

        try:
            send_admin_order_email(
                sender_name, sender_phone, sender_email, category,
                pickup_ville, pickup_commune, pickup_avenue, pickup_numero, pickup_reference,
                delivery_ville, delivery_commune, delivery_avenue, delivery_numero, delivery_reference,
                receiver_name, receiver_phone, parcel_name,
                image_path=image_path
            )

            send_order_confirmation(
                sender_name, sender_email, parcel_name, receiver_name,
                delivery_ville, delivery_commune, delivery_avenue, delivery_numero, delivery_reference,
                image_path=image_path
            )
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)

        return redirect(url_for("thankyou"))

    return render_template("envoyer.html")


@app.route("/merci")
def thankyou():
    return render_template("merci.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
