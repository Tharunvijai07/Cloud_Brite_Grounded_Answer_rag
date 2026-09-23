import os
import json
import urllib.request
import urllib.error

# Load .env manually
env_path = ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k not in os.environ:
                os.environ[k] = v

key = os.getenv("GEMINI_API_KEY", "")
print(f"GEMINI_API_KEY found : {bool(key)}")
print(f"Key preview          : {key[:12]}... (length={len(key)})")

if not key or key == "your_gemini_api_key_here":
    print("\n[ERROR] GEMINI_API_KEY is not set or still contains the placeholder value.")
    print("Please update GEMINI_API_KEY in your .env file with a real key from:")
    print("  https://aistudio.google.com/apikey")
    raise SystemExit(1)

url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-3.6-flash:generateContent?key={key}"
)
payload = {
    "contents": [{"role": "user", "parts": [{"text": "Say hello in one word."}]}]
}
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("\nCalling Gemini API...")
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
        reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"\n[SUCCESS] Gemini replied: {reply}")
        print("\nYour API key is valid. Run the RAG system with:")
        print("  python src/main.py --provider gemini --model gemini-2.0-flash")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"\n[HTTP {e.code}] Error response:")
    try:
        parsed = json.loads(body)
        print(json.dumps(parsed, indent=2))
        msg = parsed.get("error", {}).get("message", "")
        status = parsed.get("error", {}).get("status", "")
        print(f"\nStatus  : {status}")
        print(f"Message : {msg}")
        if "API_KEY_INVALID" in body or "invalid" in msg.lower():
            print("\n[FIX] The key itself is invalid. Generate a new one at:")
            print("  https://aistudio.google.com/apikey")
        elif "disabled" in msg.lower() or "not enabled" in msg.lower():
            print("\n[FIX] The Generative Language API is not enabled.")
            print("Enable it at:")
            print("  https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
        elif "quota" in msg.lower():
            print("\n[FIX] You have exceeded the free quota. Wait or upgrade your plan.")
    except Exception:
        print(body)
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
