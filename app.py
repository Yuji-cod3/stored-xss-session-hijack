"""
VULNERABLE-BY-DESIGN GUESTBOOK APP
-----------------------------------
This app deliberately contains a stored XSS vulnerability for educational
purposes only. Run it ONLY on 127.0.0.1 (localhost). Do not deploy this
code anywhere reachable by other people or the internet.

The vulnerability: comments are rendered with the Jinja2 `|safe` filter,
which disables Jinja2's default HTML autoescaping. Any HTML/JS a user
submits is written directly into the page and will execute in the
browser of every single visitor who later views the guestbook -- this
is what makes it "stored" (persistent) rather than "reflected"
(one-shot, URL-based).
"""

from flask import Flask, request, render_template_string, make_response
import uuid

app = Flask(__name__)

# In-memory "database" of guestbook comments (resets when the app restarts)
comments = []

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Guestbook (Vulnerable Lab)</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 40px auto; }
        input[type=text] { width: 300px; padding: 6px; }
        button { padding: 6px 14px; }
        .session-banner { background: #eef; padding: 8px; border-radius: 4px; margin-bottom: 20px; }
        .comment { border-bottom: 1px solid #ddd; padding: 8px 0; }
    </style>
</head>
<body>
    <div class="session-banner">
        Your session ID: <b>{{ session_id }}</b>
        <br><small>(this simulates a logged-in user's session cookie)</small>
    </div>

    <h1>Guestbook</h1>
    <form method="POST">
        <input type="text" name="comment" placeholder="Leave a comment">
        <button type="submit">Post</button>
    </form>
    <hr>
    {% for c in comments %}
        <div class="comment">{{ c|safe }}</div>
    {% endfor %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def guestbook():
    resp = make_response()

    # Assign a fake "session cookie" to anyone who doesn't already have one
    session_id = request.cookies.get("session_id")
    new_cookie = False
    if not session_id:
        session_id = str(uuid.uuid4())
        new_cookie = True

    if request.method == "POST":
        comment = request.form.get("comment", "")
        comments.append(comment)

    html = render_template_string(PAGE, comments=comments, session_id=session_id)
    resp.set_data(html)

    if new_cookie:
        resp.set_cookie("session_id", session_id, httponly=False)  # HttpOnly OFF on purpose for the lab

    return resp

if __name__ == "__main__":
    print("Vulnerable guestbook running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
