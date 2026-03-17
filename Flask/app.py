import os
import json
import secrets
from urllib.parse import urlencode

import requests
from flask import Flask, redirect, request, session, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI = os.environ["SPOTIFY_REDIRECT_URI"]

SCOPES = "user-read-recently-played user-top-read"

TOKENS_FILE = "tokens.json"


def save_tokens(token_payload: dict) -> None:
    # Salva tokens localmente (MVP). Em produção: DB/Secrets Manager.
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(token_payload, f, ensure_ascii=False, indent=2)


def load_tokens() -> dict | None:
    if not os.path.exists(TOKENS_FILE):
        return None
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
def home():
    return """
    <h2>Spotify OAuth (Flask)</h2>
    <a href="/login">Login com Spotify</a>
    <br/><br/>
    <a href="/recently-played">Testar Recently Played</a>
    """


@app.get("/login")
def login():
    # state ajuda a proteger contra CSRF
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    }

    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return redirect(auth_url)


@app.get("/callback")
def callback():
    # 1) validar state
    state = request.args.get("state")
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return f"Erro no login: {error}", 400

    if not state or state != session.get("oauth_state"):
        return "State inválido. Tente novamente.", 400

    if not code:
        return "Code não veio no callback.", 400

    # 2) trocar code por tokens
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    resp = requests.post(
        token_url,
        data=data,
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    if resp.status_code != 200:
        return f"Falha ao obter token: {resp.status_code} {resp.text}", 500

    token_payload = resp.json()
    # token_payload contém: access_token, refresh_token, expires_in, token_type, scope
    save_tokens(token_payload)

    return """
    <h3>Autenticado! Tokens salvos em tokens.json ✅</h3>
    <a href="/recently-played">Testar Recently Played</a>
    """


def refresh_access_token(refresh_token: str) -> dict:
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    resp = requests.post(
        token_url,
        data=data,
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


@app.get("/recently-played")
def recently_played():
    tokens = load_tokens()
    if not tokens:
        return redirect("/login")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    # Se não tem access token, nem chama API
    if not access_token:
        # Se tiver refresh token, tenta gerar um access token novo
        if refresh_token:
            new_tokens = refresh_access_token(refresh_token)
            new_access = new_tokens.get("access_token")
            if not new_access:
                return redirect("/login")

            tokens["access_token"] = new_access
            tokens["expires_in"] = new_tokens.get("expires_in", tokens.get("expires_in"))
            if "refresh_token" in new_tokens:
                tokens["refresh_token"] = new_tokens["refresh_token"]
            save_tokens(tokens)
            access_token = new_access
        else:
            return redirect("/login")

    def call_api(token: str):
        url = "https://api.spotify.com/v1/me/player/recently-played"
        headers = {"Authorization": f"Bearer {token}"}
        return requests.get(url, headers=headers, timeout=30)

    r = call_api(access_token)

    # Se expirou, tenta refresh e repete
    if r.status_code == 401 and refresh_token:
        new_tokens = refresh_access_token(refresh_token)
        new_access = new_tokens.get("access_token")
        if not new_access:
            return redirect("/login")

        # refresh nem sempre devolve refresh_token de novo, então preserva
        tokens["access_token"] = new_access
        tokens["expires_in"] = new_tokens.get("expires_in", tokens.get("expires_in"))
        if "refresh_token" in new_tokens:
            tokens["refresh_token"] = new_tokens["refresh_token"]
        save_tokens(tokens)

        r = call_api(new_access)

    if r.status_code != 200:
        return f"Erro API: {r.status_code} {r.text}", 500

    return jsonify(r.json())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888, debug=True)