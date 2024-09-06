from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# Replace with your app ID and app secret
APP_ID = "YOUR_APP_ID_HERE"
APP_SECRET = "YOUR_APP_SECRET_HERE"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/handle_fb_code", methods=["POST"])
def handle_fb_code():
    data = request.json
    code = data.get("code")

    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400

    # Exchange the code for an access token
    token_exchange_url = f"https://graph.facebook.com/v20.0/oauth/access_token?client_id={APP_ID}&client_secret={APP_SECRET}&code={code}"

    response = requests.get(token_exchange_url)
    token_data = response.json()

    if "access_token" not in token_data:
        return (
            jsonify(
                {"success": False, "error": token_data.get("error", "Unknown error")}
            ),
            400,
        )

    access_token = token_data["access_token"]

    # Here you can use the access_token to install your app on the user's Facebook pages.
    # This is where you would add your app installation logic, such as making API calls
    # to install the app on pages the user manages.

    # Example of installing the app to all managed pages:
    try:
        # Fetch the user's managed pages
        pages_url = (
            f"https://graph.facebook.com/v20.0/me/accounts?access_token={access_token}"
        )
        pages_response = requests.get(pages_url)
        pages_data = pages_response.json()

        for page in pages_data["data"]:
            # Here, you would make the necessary API calls to install your app on each page
            # For example:
            install_url = (
                f'https://graph.facebook.com/v20.0/{page["id"]}/subscribed_apps'
            )
            install_response = requests.post(
                install_url,
                params={
                    "access_token": page["access_token"],
                    "subscribed_fields": "feed",
                },
            )

            if install_response.status_code == 200:
                print(f'Successfully installed on page: {page["name"]}')
            else:
                print(
                    f'Failed to install on page: {page["name"]} - {install_response.text}'
                )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
