"""Utilitários compartilhados de autenticação Spotify (tokens + refresh)."""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
TOKENS_FILE = BASE_DIR / "tokens.json"

load_dotenv(dotenv_path=ENV_FILE)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória não encontrada: {name}")
    return value


SPOTIFY_CLIENT_ID = require_env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = require_env("SPOTIFY_CLIENT_SECRET")


def load_tokens() -> dict:
    if not TOKENS_FILE.exists():
        raise FileNotFoundError(
            "tokens.json não encontrado. Rode o fluxo OAuth primeiro no Flask."
        )
    with TOKENS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_tokens(tokens: dict) -> None:
    with TOKENS_FILE.open("w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)


def refresh_access_token(refresh_token: str) -> dict:
    """Troca um refresh_token por um novo access_token.

    O Spotify pode opcionalmente devolver um novo refresh_token;
    quando isso ocorre, o campo está presente no payload retornado.
    """
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(
        url,
        data=data,
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def ensure_valid_token(tokens: dict) -> str:
    """Garante um access_token válido, fazendo refresh se necessário.

    Atualiza e persiste o dicionário de tokens in-place.
    Retorna o access_token pronto para uso.
    """
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        if not refresh_token:
            raise ValueError("Nenhum access_token nem refresh_token disponível.")
        _apply_refresh(tokens, refresh_token)
        access_token = tokens["access_token"]

    return access_token


def _apply_refresh(tokens: dict, refresh_token: str) -> None:
    """Faz o refresh e atualiza `tokens` in-place, persistindo os novos valores."""
    new_tokens = refresh_access_token(refresh_token)
    tokens["access_token"] = new_tokens["access_token"]
    tokens["expires_in"] = new_tokens.get("expires_in", tokens.get("expires_in"))
    # Spotify pode retornar um novo refresh_token — persistir se vier
    if "refresh_token" in new_tokens:
        tokens["refresh_token"] = new_tokens["refresh_token"]
    save_tokens(tokens)