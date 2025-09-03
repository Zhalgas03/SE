# api/weekly_token.py
import json, gzip, base64, datetime as dt
import jwt  # pip install PyJWT

def encode_weekly_payload(payload: dict, secret: str, exp_days: int = 14) -> str:
    raw = json.dumps(payload).encode("utf-8")
    gz = gzip.compress(raw)
    b64 = base64.urlsafe_b64encode(gz).decode("ascii")
    now = dt.datetime.utcnow()
    return jwt.encode(
        {"b": b64, "iat": now, "exp": now + dt.timedelta(days=exp_days)},
        secret,
        algorithm="HS256"
    )

def decode_weekly_payload(token: str, secret: str) -> dict:
    data = jwt.decode(token, secret, algorithms=["HS256"])
    gz = base64.urlsafe_b64decode(data["b"].encode("ascii"))
    return json.loads(gzip.decompress(gz).decode("utf-8"))
