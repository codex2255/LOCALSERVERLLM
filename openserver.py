from flask import Flask, request, jsonify, Response
import requests
import json
import secrets
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# File to persist our generated API keys so they survive server restarts
KEYS_FILE = "api_keys.json"

# Ollama natively supports the OpenAI format on this local port
OLLAMA_URL = "http://127.0.0.1:11434/v1/chat/completions"
# Ollama endpoint to check available local models
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"

# --- KEY MANAGEMENT SYSTEM ---
def load_keys():
    """Loads active API keys from the JSON file."""
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_keys(keys):
    """Saves active API keys to the JSON file."""
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f)

# Load keys into memory on startup
VALID_KEYS = load_keys()

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Local LLM API Gateway</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }
        h1 { color: #38bdf8; margin-top: 0; }
        h3 { color: #cbd5e1; border-bottom: 1px solid #334155; padding-bottom: 8px; margin-top: 30px; }
        pre { background: #0b1120; padding: 15px; border-radius: 5px; overflow-x: auto; color: #a5b4fc; border: 1px solid #334155; }
        code { background: #0b1120; padding: 2px 6px; border-radius: 4px; color: #f8fafc; border: 1px solid #334155; }
        .status { display: inline-block; padding: 5px 10px; background: #10b981; color: #022c22; border-radius: 5px; font-weight: bold; font-size: 0.85em; }
        
        /* Tab CSS */
        .tab { overflow: hidden; border-bottom: 1px solid #334155; margin-bottom: 20px; display: flex; }
        .tab button { background-color: inherit; color: #94a3b8; border: none; outline: none; cursor: pointer; padding: 10px 20px; font-size: 16px; font-weight: 600; transition: 0.3s; border-bottom: 2px solid transparent; }
        .tab button:hover { color: #e2e8f0; }
        .tab button.active { color: #38bdf8; border-bottom: 2px solid #38bdf8; }
        .tabcontent { display: none; animation: fadeEffect 0.5s; }
        @keyframes fadeEffect { from {opacity: 0;} to {opacity: 1;} }
        
        /* Button CSS */
        .btn-primary { background: #38bdf8; color: #0f172a; border: none; padding: 10px 15px; border-radius: 5px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .btn-primary:hover { background: #0ea5e9; }
        .btn-danger { background: #ef4444; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-weight: bold; }
        .btn-danger:hover { background: #dc2626; }
        
        ul { padding-left: 20px; }
        li { margin-bottom: 8px; }
        .key-item { background: #0b1120; padding: 12px; margin-bottom: 8px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #334155; }
    </style>
    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) { tabcontent[i].style.display = "none"; }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }

        function loadKeys() {
            fetch('/api/keys')
                .then(res => res.json())
                .then(data => {
                    const list = document.getElementById("key-list");
                    if(data.keys && data.keys.length > 0) {
                        list.innerHTML = data.keys.map(k => `
                            <div class="key-item">
                                <code>${k}</code>
                                <button class="btn-danger" onclick="revokeKey('${k}')">Revoke</button>
                            </div>
                        `).join('');
                    } else {
                        list.innerHTML = "<p style='color: #94a3b8;'>No active API keys. Generate one to get started.</p>";
                    }
                });
        }

        function generateKey() {
            fetch('/api/keys', {method: 'POST'})
                .then(res => res.json())
                .then(data => loadKeys());
        }

        function revokeKey(key) {
            if(confirm("Are you sure you want to revoke this API key? Any applications using it will be disconnected immediately.")) {
                fetch('/api/keys/' + key, {method: 'DELETE'})
                    .then(res => res.json())
                    .then(data => loadKeys());
            }
        }

        window.onload = function() {
            document.getElementById("defaultOpen").click();
            
            // Fetch Keys
            loadKeys();

            // Fetch Models
            fetch('/api/models')
                .then(response => response.json())
                .then(data => {
                    const list = document.getElementById("model-list");
                    if(data.models && data.models.length > 0) {
                        list.innerHTML = data.models.map(m => `<li><code>${m.name}</code></li>`).join('');
                    } else {
                        list.innerHTML = "<li>No models found. Try running <code>ollama pull llama3.1</code> on the host device.</li>";
                    }
                }).catch(err => {
                    document.getElementById("model-list").innerHTML = "<li style='color: #ef4444;'>Cannot connect to Ollama. Is the engine running?</li>";
                });
        }
    </script>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h1>Local LLM Gateway</h1>
            <span class="status">GATEWAY ONLINE</span>
        </div>

        <div class="tab">
            <button class="tablinks" onclick="openTab(event, 'Dashboard')" id="defaultOpen">Dashboard</button>
            <button class="tablinks" onclick="openTab(event, 'Documentation')">Documentation</button>
        </div>

        <div id="Dashboard" class="tabcontent">
            <h3>API Key Management</h3>
            <p style="font-size: 0.9em; color: #94a3b8;">Generate access keys below. Pass these in the <code>Authorization: Bearer</code> header to connect to the node.</p>
            <button class="btn-primary" onclick="generateKey()">+ Generate New API Key</button>
            <div id="key-list" style="margin-top: 15px;">
                <p style="color: #94a3b8;">Loading keys...</p>
            </div>

            <h3>Installed Models Ready for Use</h3>
            <p style="font-size: 0.9em; color: #94a3b8;">You can pass any of these exact names into the <code>"model"</code> parameter of your API request.</p>
            <ul id="model-list">
                <li style="color: #94a3b8;">Loading available models...</li>
            </ul>
        </div>

        <div id="Documentation" class="tabcontent">
            <h3>How to use this API (OpenAI Drop-in Replacement)</h3>
            <p>You can point ANY application that uses OpenAI to this server. Just change the Base URL in your client software to this device's IP and input one of your generated keys.</p>
            <pre>
curl --location 'http://[DEVICE_IP]:5000/v1/chat/completions' \\
--header 'Authorization: Bearer YOUR_GENERATED_API_KEY' \\
--header 'Content-Type: application/json' \\
--data '{
    "model": "llama3.1",
    "messages": [
        {"role": "user", "content": "Hello from across the room!"}
    ]
}'
            </pre>

            <h3>Headless Hardware Setup</h3>
            <p>If you are running this on a laptop and want to close the lid without it going to sleep:</p>
            <ol>
                <li>Ollama must be installed and running on the host device.</li>
                <li>Edit your login configuration: <code>sudo nano /etc/systemd/logind.conf</code></li>
                <li>Find <code>#HandleLidSwitch=suspend</code>, uncomment it, and change it to: <code>HandleLidSwitch=ignore</code></li>
                <li>Restart the service: <code>sudo systemctl restart systemd-logind</code></li>
                <li>Find your device's IP address by running <code>ip a</code> in the terminal.</li>
            </ol>
        </div>

    </div>
</body>
</html>
"""

# --- GUI ROUTES ---
@app.route('/', methods=['GET'])
def dashboard():
    """Serves the Web GUI and instructions."""
    return HTML_PAGE

# --- API KEY MANAGEMENT ROUTES ---
@app.route('/api/keys', methods=['GET'])
def get_keys():
    """Returns a list of all active API keys."""
    return jsonify({"keys": VALID_KEYS})

@app.route('/api/keys', methods=['POST'])
def generate_key():
    """Generates a new secure API key, saves it, and returns it."""
    # Generate a secure 32-character hex string prefixed with 'sk-local-'
    new_key = f"sk-local-{secrets.token_hex(16)}"
    VALID_KEYS.append(new_key)
    save_keys(VALID_KEYS)
    return jsonify({"key": new_key, "success": True})

@app.route('/api/keys/<key>', methods=['DELETE'])
def delete_key(key):
    """Revokes an API key instantly."""
    if key in VALID_KEYS:
        VALID_KEYS.remove(key)
        save_keys(VALID_KEYS)
        return jsonify({"success": True})
    return jsonify({"error": "Key not found."}), 404

# --- PROXY ROUTES ---
@app.route('/api/models', methods=['GET'])
def get_models():
    """Queries the local Ollama instance to see what models are currently downloaded."""
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=3)
        return jsonify(response.json())
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to connect to Ollama", "models": []}), 502

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Intercepts requests, checks the dynamic API keys, and routes to Ollama."""
    
    # 1. Check Authentication against the dynamic list
    auth_header = request.headers.get('Authorization', '')
    provided_key = auth_header.replace('Bearer ', '').strip()
    
    if provided_key not in VALID_KEYS:
        return jsonify({"error": "Invalid or missing API key. Please generate a valid key from the Gateway Dashboard."}), 401

    payload = request.json
    
    try:
        # Check if the user requested streaming
        is_streaming = payload.get('stream', False)
        
        response = requests.post(
            OLLAMA_URL, 
            json=payload, 
            stream=is_streaming,
            timeout=120 # Give the local model time to think
        )
        
        if is_streaming:
            # If streaming, pipe the chunks back to the user exactly as received
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    yield chunk
            return Response(generate(), content_type=response.headers['content-type'])
        else:
            return jsonify(response.json()), response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Ollama. Is the engine running?"}), 502

if __name__ == '__main__':
    print(f"Starting Local LLM Gateway...")
    print(f"Web Dashboard available at: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)