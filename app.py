from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
from flask import Flask, session
from flask_session import Session
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()  # Only needed for local development

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Google Sheets setup using env variable
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Get full JSON from env variable
creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not creds_json:
    raise ValueError("GOOGLE_CREDENTIALS_JSON not set in environment")

creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet_name = os.getenv("GOOGLE_SHEET_NAME")
sheet = client.open(sheet_name).sheet1  # Ensure this spreadsheet exists

# Plot data
plot_data = {
    "Rajapark": [
        {
            "id": 1,
            "title": "Option 1 – Compact & Calm",
            "location": "Near Jain Mandir",
            "size": "550 sq yards",
            "price": "₹1.3 Crore",
            "image": "static/images/rajapark1.jpg",
            "details": "A peaceful plot near Jain Mandir with compact layout, suitable for small families."
        },
        {
            "id": 2,
            "title": "Option 2 – Spacious & Premium",
            "location": "Near Central Park",
            "size": "700 sq yards",
            "price": "₹1.6 Crore",
            "image": "static/images/rajapark2.jpg",
            "details": "Large spacious plot near Central Park with premium amenities nearby."
        }
    ],
    "Mansarovar": [
        {
            "id": 1,
            "title": "Option 1 – Family Friendly",
            "location": "Near Mansarovar Market",
            "size": "600 sq yards",
            "price": "₹90 Lakh",
            "image": "static/images/mansarovar1.jpg",
            "details": "Ideal family plot near Mansarovar Market with excellent connectivity."
        },
        {
            "id": 2,
            "title": "Option 2 – Green Surroundings",
            "location": "Near Mansarovar Park",
            "size": "750 sq yards",
            "price": "₹1.2 Crore",
            "image": "static/images/mansarovar2.jpg",
            "details": "Lush green surroundings near Mansarovar Park, perfect for nature lovers."
        }
    ],
    "Vaishali": []
}

known_areas = list(plot_data.keys())

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()
    user_msg_lower = user_msg.lower()

    if "restart" in user_msg_lower:
        session.clear()
        session['step'] = 'wait_hello'
        return jsonify({"reply": "🔄 Restarted! Please say 'hello' to start."})

    # FIXED BLOCK 👇 — properly handle first message if it's 'hi', 'hello', etc.
    if 'step' not in session:
        if any(greet in user_msg_lower for greet in ['hello', 'hi', 'hey', 'namaste']):
            session['step'] = 'ask_name'
            return jsonify({"reply": "👋 Hello! May I know your good name?"})
        else:
            session['step'] = 'wait_hello'
            return jsonify({"reply": "👋 Please say 'hello' to start."})

    if session['step'] == 'wait_hello':
        if any(greet in user_msg_lower for greet in ['hello', 'hi', 'hey', 'namaste']):
            session['step'] = 'ask_name' if 'name' not in session else 'ask_area'
            if 'name' not in session:
                return jsonify({"reply": "👋 Hello! May I know your good name?"})
            else:
                return jsonify({"reply": f"Welcome back, Mr. {session['name']}! Where would you like to explore land in Jaipur?\nOptions:\n- Rajapark\n- Mansarovar\n- Vaishali Nagar\nPlease type the area name."})
        else:
            return jsonify({"reply": "👋 Please say 'hello' to start."})

    if session['step'] == 'ask_name':
        if user_msg_lower in ['no', 'nahi', 'nahin']:
            session.clear()
            return jsonify({"reply": "Okay sir, thank you for your valuable time!"})
        session['name'] = user_msg
        session['step'] = 'ask_area'
        return jsonify({"reply": f"Nice to meet you, Mr. {session['name']}! Where would you like to explore land in Jaipur?\nOptions:\n- Rajapark\n- Mansarovar\n- Vaishali Nagar\nPlease type the area name."})

    if session['step'] == 'ask_area':
        if user_msg_lower in ['no', 'nahi', 'nahin']:
            session.clear()
            return jsonify({"reply": "Okay sir, thank you for your valuable time!"})

        area_input = user_msg_lower.replace("nagar", "").strip().capitalize()
        if area_input in known_areas and plot_data[area_input]:
            session['area'] = area_input
            session['step'] = 'show_options'
            plots = plot_data[area_input]

            reply = f"Excellent choice, Mr. {session['name']}! {area_input} is a prime location. Here are some available plots:\n"
            for idx, p in enumerate(plots, 1):
                reply += f"{idx}. {p['title']}\n"
            reply += "Please select an option number (e.g., 1 or 2) to get more details."

            images = [p['image'] for p in plots]
            return jsonify({"reply": reply, "images": images})
        else:
            session['step'] = 'ask_contact_unknown_area'
            return jsonify({"reply": f"Sorry Mr. {session['name']}, we do not have listings in '{user_msg}'. Our executive will contact you.\nPlease share your mobile number to proceed."})

    if session['step'] == 'show_options':
        if user_msg_lower in ['no', 'nahi', 'nahin']:
            session.clear()
            return jsonify({"reply": "Okay sir, thank you for your valuable time!"})

        if user_msg_lower in ['1', '2']:
            selected_idx = int(user_msg_lower) - 1
            selected_plot = plot_data[session['area']][selected_idx]
            session['selected_plot'] = selected_plot
            session['step'] = 'ask_contact_after_plot'

            reply = (f"You selected **{selected_plot['title']}**.\n"
                     f"Location: {selected_plot['location']}\n"
                     f"Size: {selected_plot['size']}\n"
                     f"Price: {selected_plot['price']}\n"
                     f"Details: {selected_plot['details']}\n\n"
                     "If you'd like to proceed, please share your contact number and email.")
            return jsonify({"reply": reply, "image": selected_plot['image']})
        else:
            return jsonify({"reply": "Please select a valid option number: 1 or 2."})

    if session['step'] in ['ask_contact_after_plot', 'ask_contact_unknown_area']:
        if user_msg_lower in ['no', 'nahi', 'nahin']:
            session.clear()
            return jsonify({"reply": "Okay sir, thank you for your valuable time!"})

        contact_info = user_msg
        location = session.get('area', 'Unknown')
        plot_info = session.get('selected_plot', {})
        plot_title = plot_info.get('title', 'N/A')
        sheet.append_row([session.get('name', 'N/A'), location, plot_title, contact_info])
        session['step'] = 'done'

        reply = ("📲 Thank you! Our executive will contact you shortly.\n"
                 "If you want to search another property, please type 'restart'.")
        return jsonify({"reply": reply})

    return jsonify({"reply": "🤖 Sorry, I didn't understand that. Please type 'restart' to start over."})

if __name__ == "__main__":
    app.run(debug=True)

