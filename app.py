from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import time
import os
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "aldopensi_secret_key_123"
DB_NAME = "users.db"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            score INTEGER DEFAULT 0,
            game_limit INTEGER DEFAULT 10,
            balance INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nokprem_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_service TEXT,
            price INTEGER,
            stock INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            service_name TEXT,
            price INTEGER,
            phone_number TEXT,
            status TEXT DEFAULT 'Menunggu sms otp',
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount INTEGER,
            status TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            image_url TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE username = 'owner'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (first_name, last_name, phone, username, password, role, score, game_limit, balance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       ("Admin", "Owner", "62800000000", "owner", "ownerpassword123", "owner", 150, 25, 100000))
        conn.commit()
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_link', 'https://t.me/namachannelkamu')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cs_link', 'https://t.me/namaownerkamu')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('qris_image', 'https://i.ibb.co.com/6X421y9/qris-sample.png')")
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AldoMultiDevice V1</title>
    <style>
        :root {
            --bg-color: #060913;
            --sidebar-bg: #0b111e;
            --card-bg: rgba(18, 25, 38, 0.85);
            --border-color: rgba(56, 189, 248, 0.2);
            --accent-green: #14b8a6;
            --accent-blue: #0ea5e9;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --danger: #ef4444;
            --success: #22c55e;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(20, 184, 166, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(14, 165, 233, 0.15) 0px, transparent 50%);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }
        
        .marquee-container {
            background: linear-gradient(90deg, #0f172a, #134e4a, #0f172a);
            border-bottom: 1px solid var(--accent-green);
            color: #2dd4bf;
            padding: 8px 0;
            font-size: 13px;
            font-weight: 600;
            overflow: hidden;
            white-space: nowrap;
            box-shadow: 0 2px 10px rgba(20, 184, 166, 0.2);
        }
        .marquee-container marquee { width: 100%; }

        .sidebar {
            height: 100%;
            width: 270px;
            position: fixed;
            top: 0;
            left: -270px;
            background-color: var(--sidebar-bg);
            transition: left 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1000;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 5px 0 25px rgba(0,0,0,0.6);
        }
        .sidebar.active { left: 0; }
        
        .sidebar-header {
            padding: 20px;
            font-size: 18px;
            font-weight: bold;
            color: var(--accent-green);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .close-sidebar-btn {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid var(--danger);
            color: var(--danger);
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: 0.2s;
        }
        .close-sidebar-btn:hover { background: var(--danger); color: white; }

        .sidebar-menu { list-style: none; padding: 0; margin: 0; }
        .sidebar-menu li a {
            display: block;
            padding: 14px 20px;
            color: var(--text-main);
            text-decoration: none;
            font-size: 14px;
            border-left: 4px solid transparent;
            transition: 0.2s;
        }
        .sidebar-menu li a:hover, .sidebar-menu li a.active {
            background-color: rgba(20, 184, 166, 0.1);
            border-left-color: var(--accent-green);
            color: var(--accent-green);
        }

        .topnav {
            background-color: var(--sidebar-bg);
            padding: 12px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 900;
        }
        .menu-btn {
            background: none;
            border: none;
            color: var(--text-main);
            font-size: 20px;
            cursor: pointer;
        }
        .main-content { padding: 15px; max-width: 600px; margin: auto; padding-bottom: 40px; }
        
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(14px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 15px;
            width: 100%;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px 14px;
            margin: 6px 0 14px 0;
            background: rgba(6, 9, 19, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: white;
            font-size: 14px;
            transition: all 0.3s;
        }
        input:focus {
            border-color: var(--accent-green);
            outline: none;
            box-shadow: 0 0 10px rgba(20, 184, 166, 0.3);
        }
        
        .btn-green {
            background: linear-gradient(135deg, #14b8a6, #0ea5e9);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
            text-align: center;
            text-decoration: none;
            display: block;
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3);
            transition: 0.2s;
        }
        .btn-green:hover { opacity: 0.95; transform: translateY(-1px); }
        
        .auth-container { max-width: 420px; margin: 20px auto; padding: 15px; }
        
        .brand-logo-container { text-align: center; margin-bottom: 15px; }
        .brand-logo {
            width: 75px; height: 75px; border-radius: 50%;
            background: linear-gradient(135deg, #14b8a6, #0ea5e9);
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 32px; box-shadow: 0 0 25px rgba(20, 184, 166, 0.4);
            border: 2px solid rgba(255,255,255,0.2); margin-bottom: 8px;
        }
        
        .status-badge-container { display: flex; justify-content: center; margin-bottom: 12px; }
        .status-badge {
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(15, 20, 28, 0.8); border: 1px solid var(--border-color);
            padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 600; color: var(--text-muted);
        }
        .dot { width: 8px; height: 8px; border-radius: 50%; background-color: var(--success); box-shadow: 0 0 8px var(--success); animation: blink 1.5s infinite; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

        .game-grid, .action-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        .game-card, .action-btn-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.8));
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px 10px;
            text-align: center;
            text-decoration: none;
            color: var(--text-main);
            transition: 0.25s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            display: block;
        }
        .game-card:hover, .action-btn-card:hover {
            border-color: var(--accent-green);
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(20, 184, 166, 0.25);
        }
        .game-icon { font-size: 28px; margin-bottom: 6px; display: block; }
        .game-title { font-size: 13px; font-weight: bold; color: var(--accent-green); }

        .deposit-quick-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 12px;
        }
        .deposit-chip {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 10px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 13px;
            text-align: center;
            transition: 0.2s;
        }
        .deposit-chip:hover { border-color: var(--accent-green); background: rgba(20, 184, 166, 0.15); color: var(--accent-green); }

        .nokprem-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 10px;
        }
        .nokprem-table th, .nokprem-table td {
            padding: 10px 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .nokprem-table th { color: var(--accent-blue); background: rgba(15, 23, 42, 0.5); }
        .badge-stock-false { background: rgba(239, 68, 68, 0.2); color: var(--danger); padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }

        .bomb-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
            margin-top: 15px;
            margin-bottom: 15px;
        }
        .circle-btn {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0ea5e9, #14b8a6);
            border: 2px solid rgba(255,255,255,0.2);
            color: white;
            font-weight: bold;
            font-size: 15px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
            transition: transform 0.2s, background 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .circle-btn:active { transform: scale(0.9); }
        
        @keyframes explosion-effect {
            0% { transform: scale(0.6); background-color: #ff0000; box-shadow: 0 0 15px #ff5500; }
            50% { transform: scale(1.25); background-color: #ff3300; box-shadow: 0 0 50px #ff0000, 0 0 90px #ff9900; }
            100% { transform: scale(1); background-color: #380202; box-shadow: 0 0 20px #000; }
        }
        .exploded { animation: explosion-effect 0.7s ease-out forwards; }

        @keyframes dice-roll {
            0% { transform: rotate(0deg) scale(1); }
            25% { transform: rotate(90deg) scale(1.15); }
            50% { transform: rotate(180deg) scale(1); }
            75% { transform: rotate(270deg) scale(1.15); }
            100% { transform: rotate(360deg) scale(1); }
        }
        .rolling-dice { animation: dice-roll 0.5s infinite linear; display: inline-block; }

        .leaderboard-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 10px;
        }
        .leaderboard-table th, .leaderboard-table td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .leaderboard-table th { color: var(--accent-blue); background: rgba(15, 23, 42, 0.5); }
        .rank-1 { color: #f59e0b; font-weight: bold; }
        .rank-2 { color: #94a3b8; font-weight: bold; }
        .rank-3 { color: #b45309; font-weight: bold; }

        .chat-box {
            height: 250px; overflow-y: auto; background: rgba(6, 9, 19, 0.6);
            border: 1px solid var(--border-color); border-radius: 10px; padding: 10px; margin-bottom: 10px; font-size: 13px;
            display: flex; flex-direction: column; gap: 8px;
        }
        .chat-msg { margin-bottom: 4px; padding: 8px 12px; border-radius: 10px; width: fit-content; max-width: 80%; }
        .chat-me { background: rgba(20, 184, 166, 0.25); margin-left: auto; text-align: right; border: 1px solid rgba(20, 184, 166, 0.3); }
        .chat-other { background: rgba(30, 41, 59, 0.7); border: 1px solid var(--border-color); }
        .chat-img { max-width: 150px; border-radius: 8px; margin-top: 6px; display: block; border: 1px solid rgba(255,255,255,0.2); }
    </style>
</head>
<body>

    <!-- Musik Latar Belakang (Otomatis & Bisa Diatur Volumenya) -->
    <audio id="bg-music" loop>
        <source src="{{ url_for('static', filename='aldomulti.mp3') }}" type="audio/mpeg">
        Browser Anda tidak mendukung elemen audio.
    </audio>

    <div class="marquee-container">
        <marquee behavior="scroll" direction="left" scrollamount="5">
            ⚡ SELAMAT DATANG DI ALDOMULTIDEVICE V1 • SILAKAN ORDER NOKPREM DAN DEPOSIT SALDO QRIS DENGAN AMAN! 🚀
        </marquee>
    </div>

    {% if session.get('user') %}
    <div class="sidebar" id="sidebar">
        <div>
            <div class="sidebar-header">
                <div>⚡ AldoMultiDevice <br><span style="font-size: 11px; color: var(--text-muted);">Panel v1 Pro</span></div>
                <button class="close-sidebar-btn" onclick="toggleSidebar()">✕</button>
            </div>
            <ul class="sidebar-menu">
                <li><a href="/dashboard" {% if page == 'dashboard' %}class="active"{% endif %}>📊 Dashboard</a></li>
                {% if session.get('role') == 'owner' %}
                <li><a href="/owner/restock" {% if page == 'restock_nokprem' %}class="active"{% endif %}>📦 Restock Nokprem (Owner)</a></li>
                <li><a href="/owner/deposits" {% if page == 'owner_deposits' %}class="active"{% endif %}>💰 Verifikasi Deposit (Owner)</a></li>
                {% endif %}
                <li><a href="/order/nokprem" {% if page == 'order_nokprem' %}class="active"{% endif %}>🛒 Order Nokprem</a></li>
                <li><a href="/riwayat-pesanan" {% if page == 'riwayat_pesanan' %}class="active"{% endif %}>📋 Riwayat Pesanan</a></li>
                <li><a href="/deposit" {% if page in ['deposit', 'deposit_qris'] %}class="active"{% endif %}>💳 Deposit Saldo</a></li>
                <li><a href="/game/bomb" {% if page in ['game_bomb', 'game_dice'] %}class="active"{% endif %}>🎮 Game Center</a></li>
                <li><a href="/leaderboard" {% if page == 'leaderboard' %}class="active"{% endif %}>🏆 Leaderboard Game</a></li>
                <li><a href="/livechat" {% if page == 'livechat' %}class="active"{% endif %}>💬 Live Chat CS</a></li>
                <li><a href="/settings" {% if page == 'settings' %}class="active"{% endif %}>⚙️ Pengaturan URL</a></li>
            </ul>
        </div>
        <div style="padding: 15px; border-top: 1px solid var(--border-color);">
            <div style="font-size: 12px; margin-bottom: 4px;">👤 <b>{{ session['user'] }}</b></div>
            <div style="font-size: 11px; color: var(--accent-green); margin-bottom: 4px;">Saldo: Rp {{ "{:,}".format(user_data['balance']) }}</div>
            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">Score: {{ user_data['score'] }} | Limit: {{ user_data['game_limit'] }}</div>
            <a href="/logout" style="color: var(--danger); text-decoration: none; font-weight: bold; font-size: 12px;">🚪 Logout</a>
        </div>
    </div>

    <div class="topnav">
        <button class="menu-btn" onclick="toggleSidebar()">☰</button>
        <span style="font-weight: bold; font-size: 15px; color: var(--accent-green);">AldoMultiDevice V1</span>
        <div>
            <a href="{{ channel_link }}" target="_blank" style="text-decoration: none; font-size: 18px; margin-right: 10px;" title="Channel Telegram">📢</a>
            <a href="{{ cs_link }}" target="_blank" style="text-decoration: none; font-size: 18px;" title="CS Owner">💬</a>
        </div>
    </div>

    <div class="main-content">
        {% if error %}
        <div style="background: rgba(239, 68, 68, 0.2); border: 1px solid var(--danger); color: var(--text-main); padding: 10px; border-radius: 10px; margin-bottom: 15px; font-size: 13px;">
            ⚠️ {{ error }}
        </div>
        {% endif %}

        {% if success_msg %}
        <div style="background: rgba(34, 197, 94, 0.2); border: 1px solid var(--success); color: var(--text-main); padding: 10px; border-radius: 10px; margin-bottom: 15px; font-size: 13px;">
            ✨ {{ success_msg }}
        </div>
        {% endif %}

        {% if page == 'dashboard' %}
        <div class="status-badge-container">
            <div class="status-badge">
                <span class="dot"></span> SALDO: Rp {{ "{:,}".format(user_data['balance']) }} &bull; AKTIF
            </div>
        </div>

        <!-- Panel Kontrol Musik di Dashboard -->
        <div class="card" style="border: 1px solid var(--accent-green); background: linear-gradient(135deg, rgba(20, 184, 166, 0.1), rgba(18, 25, 38, 0.9));">
            <h3 style="margin-top:0; font-size: 15px; color: var(--accent-green); display: flex; align-items: center; justify-content: space-between;">
                <span>🎵 Background Music Player</span>
                <button type="button" id="playPauseBtn" onclick="togglePlayMusic()" style="background: var(--accent-green); color: white; border: none; padding: 4px 10px; border-radius: 6px; font-size: 12px; cursor: pointer; font-weight: bold;">Pause</button>
            </h3>
            <div style="display: flex; align-items: center; gap: 12px; margin-top: 10px;">
                <span style="font-size: 13px; color: var(--text-muted);">Volume:</span>
                <input type="range" id="volumeSlider" min="0" max="1" step="0.05" value="0.3" style="margin: 0; cursor: pointer;">
            </div>
        </div>

        <div class="card" style="border: 1px solid var(--accent-blue); background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(18, 25, 38, 0.9));">
            <h3 style="margin-top:0; font-size: 16px; color: var(--accent-blue);">⚡ Layanan Cepat Nokos & Saldo</h3>
            <div class="action-grid">
                <a href="/order/nokprem" class="action-btn-card">
                    <span class="game-icon">🛒</span>
                    <span class="game-title">Order Nokprem</span>
                </a>
                <a href="/deposit" class="action-btn-card">
                    <span class="game-icon">💳</span>
                    <span class="game-title">Deposit Saldo</span>
                </a>
            </div>
        </div>

        <div class="card" style="border: 1px solid var(--accent-green); background: linear-gradient(135deg, rgba(20, 184, 166, 0.08), rgba(18, 25, 38, 0.9));">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="margin:0; font-size: 16px; color: var(--accent-green);">🎮 Realistis Mini Games</h3>
                <span style="font-size: 11px; background: rgba(245, 158, 11, 0.2); color: var(--warning); padding: 3px 8px; border-radius: 8px; border: 1px solid var(--warning);">Limit: <b id="userLimitCount">{{ user_data['game_limit'] }}</b></span>
            </div>
            <p style="color: var(--text-muted); font-size: 12px; margin-bottom: 10px;">Mainkan mini games interaktif bergaya Telegram untuk meraih hadiah limit acak & score tertinggi!</p>
            
            <div class="game-grid">
                <a href="/game/bomb" class="game-card">
                    <span class="game-icon">💣</span>
                    <span class="game-title">Tebak Bom Bulat</span>
                </a>
                <a href="/game/dice" class="game-card">
                    <span class="game-icon">🎲</span>
                    <span class="game-title">Dadu Telegram vs Bot</span>
                </a>
            </div>
        </div>

        {% elif page == 'restock_nokprem' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">📦 Restock Nokprem (Owner)</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <form method="POST">
                <label style="font-size: 13px;">Nama Layanan / Negara:</label>
                <input type="text" name="country_service" placeholder="Telegram - Indonesia" required>
                <label style="font-size: 13px;">Harga (Rupiah):</label>
                <input type="number" name="price" placeholder="5000" required>
                <label style="font-size: 13px;">Jumlah Stok:</label>
                <input type="number" name="stock" placeholder="10" required>
                <button type="submit" class="btn-green">Simpan / Restock Nokprem</button>
            </form>
        </div>

        {% elif page == 'owner_deposits' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">💰 Verifikasi Deposit User</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <table class="nokprem-table">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Nominal</th>
                        <th>Status</th>
                        <th>Waktu</th>
                        <th>Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for d in deposits %}
                    <tr>
                        <td><b>{{ d['username'] }}</b></td>
                        <td>Rp {{ "{:,}".format(d['amount']) }}</td>
                        <td>
                            {% if d['status'] == 'Pending' %}
                            <span style="color:var(--warning); font-weight:bold;">PENDING</span>
                            {% else %}
                            <span style="color:var(--success); font-weight:bold;">SUKSES</span>
                            {% endif %}
                        </td>
                        <td><small>{{ d['timestamp'] }}</small></td>
                        <td>
                            {% if d['status'] == 'Pending' %}
                            <a href="/owner/approve_deposit/{{ d['id'] }}" style="background:var(--success); color:white; padding:4px 8px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:bold;">ACC</a>
                            {% else %}
                            -
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        {% elif page == 'order_nokprem' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">🛒 Order Nokprem</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <div style="font-size: 12px; color: var(--accent-green); margin-bottom: 12px;">Saldo Anda: <b>Rp {{ "{:,}".format(user_data['balance']) }}</b></div>
            <table class="nokprem-table" style="margin-bottom: 15px;">
                <thead>
                    <tr>
                        <th>Layanan</th>
                        <th>Harga</th>
                        <th>Stok</th>
                        <th>Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in products %}
                    <tr>
                        <td>{{ p['country_service'] }}</td>
                        <td>Rp {{ "{:,}".format(p['price']) }}</td>
                        <td>{{ p['stock'] }}</td>
                        <td>
                            {% if p['stock'] > 0 %}
                            <form method="POST" style="margin:0;">
                                <input type="hidden" name="product_id" value="{{ p['id'] }}">
                                <button type="submit" style="background:var(--accent-green); color:white; border:none; padding:5px 10px; border-radius:6px; cursor:pointer; font-size:11px; font-weight:bold;">Beli</button>
                            </form>
                            {% else %}
                            <span class="badge-stock-false">KOSONG</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        {% elif page == 'riwayat_pesanan' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">📋 Riwayat Pesanan Nokprem</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            
            {% if pesanan %}
            <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 15px;">Detail transaksi pesanan aktif nokos premium Anda:</div>
            
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>ID Pesanan:</span>
                    <b>#TRX-{{ pesanan['id'] }}</b>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Layanan:</span>
                    <b>{{ pesanan['service_name'] }}</b>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Nomor:</span>
                    <b style="color: var(--accent-green);">{{ pesanan['phone_number'] }}</b>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Harga Terpotong:</span>
                    <b style="color: var(--danger);">- Rp {{ "{:,}".format(pesanan['price']) }}</b>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Sisa Saldo Anda:</span>
                    <b style="color: var(--accent-blue);">Rp {{ "{:,}".format(user_data['balance']) }}</b>
                </div>
            </div>

            <div style="background: rgba(245, 158, 11, 0.15); border-left: 4px solid var(--warning); padding: 12px; border-radius: 6px; margin-bottom: 15px;">
                <div style="font-weight: bold; color: var(--warning); font-size: 14px;">
                    Status: Menunggu sms otp<span id="loadingDots"></span>
                </div>
            </div>

            <div style="display: flex; gap: 10px;">
                <button type="button" onclick="cancelOrder({{ pesanan['id'] }})" style="flex: 1; background: rgba(239, 68, 68, 0.2); border: 1px solid var(--danger); color: var(--danger); padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer;">Batalkan Pemesanan</button>
                <button type="button" onclick="location.reload()" style="flex: 1; background: rgba(14, 165, 233, 0.2); border: 1px solid var(--accent-blue); color: var(--accent-blue); padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer;">Refresh</button>
            </div>
            {% else %}
            <div style="text-align: center; padding: 30px; color: var(--text-muted);">
                <p style="font-size: 14px;">Belum ada riwayat pesanan aktif saat ini.</p>
                <a href="/order/nokprem" class="btn-green" style="display: inline-block; width: auto; padding: 10px 20px; margin-top: 10px;">Order Nokprem Sekarang</a>
            </div>
            {% endif %}
        </div>

        {% elif page == 'deposit' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">💳 Deposit Saldo Akun</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <p style="color: var(--text-muted); font-size: 13px;">Pilih nominal instan atau masukkan nominal manual untuk melanjutkan pembayaran QRIS.</p>
            <div style="font-size: 12px; color: var(--accent-green); margin-bottom: 12px;">Saldo Anda: <b>Rp {{ "{:,}".format(user_data['balance']) }}</b></div>

            <div class="deposit-quick-grid">
                <button type="button" class="deposit-chip" onclick="setDepositAmount(2000)">Rp 2.000</button>
                <button type="button" class="deposit-chip" onclick="setDepositAmount(5000)">Rp 5.000</button>
                <button type="button" class="deposit-chip" onclick="setDepositAmount(10000)">Rp 10.000</button>
                <button type="button" class="deposit-chip" onclick="setDepositAmount(25000)">Rp 25.000</button>
            </div>

            <form method="POST" action="/deposit/qris">
                <label style="font-size: 13px;">Nominal Deposit (Rupiah):</label>
                <input type="number" id="depositInput" name="amount" placeholder="Contoh: 15000" required>
                <button type="submit" class="btn-green">Lanjutkan ke Pembayaran QRIS</button>
            </form>
        </div>

        {% elif page == 'deposit_qris' %}
        <div class="card" style="text-align: center;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">📷 Scan QRIS Pembayaran</h3>
                <a href="/deposit" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <p style="font-size: 14px; color: var(--text-muted);">Silakan scan QRIS di bawah ini untuk melakukan pembayaran sebesar:</p>
            <div style="font-size: 22px; font-weight: bold; color: var(--accent-green); margin-bottom: 15px;">Rp {{ "{:,}".format(amount) }}</div>
            
            <div style="background: white; padding: 10px; border-radius: 12px; display: inline-block; margin-bottom: 15px;">
                <img src="{{ qris_image }}" alt="QRIS Code" style="width: 220px; height: 220px; object-fit: contain;">
            </div>

            <div style="background: rgba(245, 158, 11, 0.15); border: 1px dashed var(--warning); padding: 12px; border-radius: 10px; font-size: 12px; color: var(--warning); text-align: left; line-height: 1.5; margin-bottom: 15px;">
                ⚠️ <b>PENTING:</b> Setelah Anda melakukan transfer sesuai nominal, <b>wajib mengirimkan foto screenshot (SS) bukti transfer</b> ke menu <b>Live Chat CS</b> agar deposit Anda diverifikasi dan saldo ditambahkan oleh Admin!
            </div>

            <a href="/livechat" class="btn-green">Kirim Bukti SS ke Live Chat Sekarang 💬</a>
        </div>

        {% elif page == 'game_bomb' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">💣 Game Tebak Bom Bulat</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <div id="bombAlert" style="display: none; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 15px; font-size: 14px; font-weight: bold;"></div>
            <div class="bomb-grid" id="bombContainer">
                {% for i in range(6) %}
                <button type="button" class="circle-btn" onclick="chooseBomb({{ i }})">#{{ i+1 }}</button>
                {% endfor %}
            </div>
            <div style="text-align: center; font-size: 12px; color: var(--text-muted);">Sisa Limit: <b id="currentLimit">{{ user_data['game_limit'] }}</b></div>
        </div>

        {% elif page == 'game_dice' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">🎲 Dadu Lawan Bot Telegram</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <div id="diceAlert" style="display: none; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 15px; font-size: 14px;"></div>
            <div style="text-align: center; margin: 20px 0;">
                <div id="diceDisplay" style="font-size: 50px; margin-bottom: 15px;">🎲</div>
                <div id="diceInfo" style="font-size: 13px; color: var(--text-muted); margin-bottom: 15px;">Tekan tombol di bawah untuk mulai melempar dadu.</div>
            </div>
            <div style="display: flex; gap: 10px;">
                <button type="button" id="rollBtn" class="btn-green" onclick="rollDice()" style="flex: 2;">Lempar Dadu 🎲</button>
                <a href="/dashboard" class="btn-green" style="background: rgba(239, 68, 68, 0.3); border: 1px solid var(--danger); flex: 1; text-align: center; display: flex; align-items: center; justify-content: center;">Batal</a>
            </div>
            <div style="text-align: center; font-size: 12px; color: var(--text-muted); margin-top: 12px;">Sisa Limit: <b id="currentDiceLimit">{{ user_data['game_limit'] }}</b></div>
        </div>

        {% elif page == 'leaderboard' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">🏆 Leaderboard Top 10</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            <table class="leaderboard-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Username</th>
                        <th>Score</th>
                        <th>Limit</th>
                    </tr>
                </thead>
                <tbody>
                    {% for lb in leaders %}
                    <tr>
                        <td>
                            {% if loop.index == 1 %}<span class="rank-1">🥇 #1</span>
                            {% elif loop.index == 2 %}<span class="rank-2">🥈 #2</span>
                            {% elif loop.index == 3 %}<span class="rank-3">🥉 #3</span>
                            {% else %}#{{ loop.index }}{% endif %}
                        </td>
                        <td><b>{{ lb['username'] }}</b></td>
                        <td style="color: var(--accent-green);">{{ lb['score'] }} pts</td>
                        <td>{{ lb['game_limit'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        {% elif page == 'livechat' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">💬 Live Chat CS & Bukti Transfer</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            
            <div class="chat-box" id="chatBox">
                {% for chat in chats %}
                <div class="chat-msg {% if chat['sender'] == session['user'] %}chat-me{% else %}chat-other{% endif %}">
                    <small style="color: var(--text-muted); display:block; font-size:10px;">{{ chat['sender'] }} ({{ chat['timestamp'] }})</small>
                    {% if chat['message'] %}
                    <div>{{ chat['message'] }}</div>
                    {% endif %}
                    {% if chat['image_url'] %}
                    <a href="{{ chat['image_url'] }}" target="_blank">
                        <img src="{{ chat['image_url'] }}" class="chat-img" alt="Bukti Transfer">
                    </a>
                    {% endif %}
                </div>
                {% endfor %}
            </div>

            <form method="POST" enctype="multipart/form-data" style="display: flex; flex-direction: column; gap: 8px;">
                {% if session.get('role') == 'owner' %}
                <input type="text" name="target_user" placeholder="Kirim ke user..." required style="margin:0;">
                {% else %}
                <input type="hidden" name="target_user" value="owner">
                {% endif %}
                
                <div style="display: flex; gap: 6px; align-items: center;">
                    <textarea name="message" placeholder="Tulis pesan atau keterangan bukti transfer..." rows="1" style="flex: 1; margin: 0; resize: none; padding: 10px;"></textarea>
                    
                    <label title="Kirim Foto dari Galeri" style="background: rgba(14, 165, 233, 0.2); border: 1px solid var(--accent-blue); color: var(--accent-blue); padding: 10px 12px; border-radius: 10px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center;">
                        📷
                        <input type="file" name="image" accept="image/*" style="display: none;" onchange="previewFileName(this)">
                    </label>

                    <button type="submit" class="btn-green" style="width: auto; padding: 10px 16px; margin: 0;">Kirim</button>
                </div>
                <div id="fileIndicator" style="font-size: 11px; color: var(--accent-green);"></div>
            </form>
        </div>

        {% elif page == 'settings' %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="margin:0;">⚙️ Pengaturan Panel</h3>
                <a href="/dashboard" style="background:rgba(239, 68, 68, 0.2); border:1px solid var(--danger); color:var(--danger); padding:4px 10px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:bold;">✕ Kembali</a>
            </div>
            {% if success %}
            <div style="background:rgba(20,184,166,0.2); border:1px solid var(--accent-green); padding:10px; border-radius:8px; margin-bottom:10px; font-size:13px;">
                ✨ Pengaturan berhasil disimpan!
            </div>
            {% endif %}
            
            {% if session.get('role') == 'owner' %}
            <form method="POST">
                <label style="font-size: 13px;">URL Channel Telegram:</label>
                <input type="text" name="channel_link" value="{{ channel_link }}">
                <label style="font-size: 13px;">URL CS / Owner Telegram:</label>
                <input type="text" name="cs_link" value="{{ cs_link }}">
                <label style="font-size: 13px;">URL Gambar QRIS:</label>
                <input type="text" name="qris_image" value="{{ qris_image }}">
                <button type="submit" class="btn-green">Simpan Pengaturan</button>
            </form>
            {% else %}
            <p style="color: var(--danger); font-size: 13px;">Menu khusus Owner website.</p>
            {% endif %}
        </div>
        {% endif %}
    </div>

    <script>
        // Logika Audio & Volume
        const bgMusic = document.getElementById('bg-music');
        const volumeSlider = document.getElementById('volumeSlider');
        const playPauseBtn = document.getElementById('playPauseBtn');

        if (bgMusic) {
            bgMusic.volume = volumeSlider ? volumeSlider.value : 0.3;

            // Coba putar otomatis
            bgMusic.play().catch(error => {
                console.log("Autoplay dicegah browser, menunggu interaksi klik pertama.");
                document.body.addEventListener('click', function() {
                    bgMusic.play();
                }, { once: true });
            });
        }

        if (volumeSlider) {
            volumeSlider.addEventListener('input', function() {
                if (bgMusic) bgMusic.volume = volumeSlider.value;
            });
        }

        function togglePlayMusic() {
            if (!bgMusic) return;
            if (bgMusic.paused) {
                bgMusic.play();
                if(playPauseBtn) playPauseBtn.innerText = "Pause";
            } else {
                bgMusic.pause();
                if(playPauseBtn) playPauseBtn.innerText = "Play";
            }
        }

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('active');
        }
        var chatBox = document.getElementById('chatBox');
        if(chatBox) { chatBox.scrollTop = chatBox.scrollHeight; }

        function setDepositAmount(val) {
            document.getElementById('depositInput').value = val;
        }

        function previewFileName(input) {
            let indicator = document.getElementById('fileIndicator');
            if (input.files && input.files[0]) {
                indicator.innerText = "📎 Terpilih: " + input.files[0].name;
            } else {
                indicator.innerText = "";
            }
        }

        let dotCount = 0;
        setInterval(() => {
            let dotsElem = document.getElementById('loadingDots');
            if(dotsElem) {
                dotCount = (dotCount + 1) % 4;
                dotsElem.innerText = " .".repeat(dotCount);
            }
        }, 500);

        function cancelOrder(orderId) {
            if(confirm("Yakin ingin membatalkan pemesanan? Saldo akan dikembalikan.")) {
                fetch('/api/order/cancel/' + orderId, {method: 'POST'})
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    if(data.success) { location.reload(); }
                });
            }
        }

        function chooseBomb(index) {
            fetch('/api/game/bomb', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ index: index })
            })
            .then(res => res.json())
            .then(data => {
                let btn = document.querySelectorAll('.circle-btn')[index];
                let alertBox = document.getElementById('bombAlert');
                alertBox.style.display = 'block';
                document.getElementById('currentLimit').innerText = data.remaining_limit;
                if(document.getElementById('userLimitCount')) {
                    document.getElementById('userLimitCount').innerText = data.remaining_limit;
                }
                if(data.status === 'boom') {
                    btn.classList.add('exploded');
                    btn.innerHTML = '🔥';
                    alertBox.style.background = 'rgba(239, 68, 68, 0.2)';
                    alertBox.style.border = '1px solid var(--danger)';
                    alertBox.style.color = 'var(--danger)';
                    alertBox.innerHTML = data.message;
                    setTimeout(() => { location.reload(); }, 2200);
                } else {
                    btn.style.background = '#22c55e';
                    btn.innerHTML = '💎';
                    alertBox.style.background = 'rgba(34, 197, 94, 0.2)';
                    alertBox.style.border = '1px solid var(--success)';
                    alertBox.style.color = 'var(--success)';
                    alertBox.innerHTML = data.message;
                }
            });
        }

        function rollDice() {
            let diceDisplay = document.getElementById('diceDisplay');
            let diceInfo = document.getElementById('diceInfo');
            let alertBox = document.getElementById('diceAlert');
            let rollBtn = document.getElementById('rollBtn');

            rollBtn.disabled = true;
            diceDisplay.classList.add('rolling-dice');
            diceInfo.innerText = "Bot mengocok dadu...";
            alertBox.style.display = 'none';

            let interval = setInterval(() => {
                diceDisplay.innerText = ['🎲','⚀','⚁','⚂','⚃','⚄','⚅'][Math.floor(Math.random()*6)];
            }, 100);

            setTimeout(() => {
                clearInterval(interval);
                diceDisplay.classList.remove('rolling-dice');
                fetch('/api/game/dice', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                })
                .then(res => res.json())
                .then(data => {
                    rollBtn.disabled = false;
                    alertBox.style.display = 'block';
                    document.getElementById('currentDiceLimit').innerText = data.remaining_limit;
                    if(document.getElementById('userLimitCount')) {
                        document.getElementById('userLimitCount').innerText = data.remaining_limit;
                    }
                    diceDisplay.innerText = '⚅';
                    diceInfo.innerHTML = `Anda: <b>${data.player_roll}</b> vs Bot: <b>${data.bot_roll}</b>`;
                    alertBox.style.background = data.result === 'win' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)';
                    alertBox.style.border = data.result === 'win' ? '1px solid var(--success)' : '1px solid var(--danger)';
                    alertBox.style.color = data.result === 'win' ? 'var(--success)' : 'var(--danger)';
                    alertBox.innerHTML = data.message;
                });
            }, 1200);
        }
    </script>

    {% else %}
    <div class="auth-container">
        <div class="card">
            <div class="brand-logo-container">
                <div class="brand-logo">⚡</div>
                <h2 style="color: #2dd4bf; margin: 5px 0 0 0; font-size: 20px;">AldoMultiDevice V1</h2>
                <span style="color: var(--text-muted); font-size: 12px;">MultiDevice Panel & Services</span>
            </div>

            {% if error %}
                <p style="color: var(--danger); text-align: center; font-size: 13px;">{{ error }}</p>
            {% endif %}

            <form method="POST">
                {% if page == 'register' %}
                <label style="font-size: 13px;">Nama Depan</label>
                <input type="text" name="first_name" required>
                <label style="font-size: 13px;">Nama Belakang</label>
                <input type="text" name="last_name">
                <label style="font-size: 13px;">Nomor Telepon</label>
                <input type="text" name="phone" placeholder="628xxxxxxxxxx" required>
                {% endif %}
                <label style="font-size: 13px;">Username</label>
                <input type="text" name="username" placeholder="Masukkan username" required>
                <label style="font-size: 13px;">Password</label>
                <input type="password" name="password" placeholder="Masukkan password" required>
                <button type="submit" class="btn-green">{{ title }}</button>
            </form>

            <p style="text-align: center; margin-top: 12px; font-size: 13px;">
                {% if page == 'login' %}
                    Belum punya akun? <a href="/register" style="color: var(--accent-blue);">Daftar di sini</a><br><br>
                    <span style="color: var(--text-muted); font-size: 11px;">Owner default: username: <b>owner</b> | password: <b>ownerpassword123</b></span>
                {% else %}
                    Sudah punya akun? <a href="/login" style="color: var(--accent-blue);">Login di sini</a>
                {% endif %}
            </p>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    data = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return data.get('channel_link', ''), data.get('cs_link', ''), data.get('qris_image', '')

def get_user_data(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    return render_template_string(HTML_TEMPLATE, page='dashboard', user_data=u_data, channel_link=c_link, cs_link=cs_link)

@app.route('/owner/restock', methods=['GET', 'POST'])
def restock_nokprem():
    if 'user' not in session or session.get('role') != 'owner': 
        return redirect(url_for('dashboard'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    success_msg = None
    error = None

    if request.method == 'POST':
        country_service = request.form['country_service'].strip()
        try:
            price = int(request.form['price'])
            stock = int(request.form['stock'])
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO nokprem_products (country_service, price, stock) VALUES (?, ?, ?)", (country_service, price, stock))
            conn.commit()
            conn.close()
            success_msg = "Stok Nokprem berhasil ditambahkan!"
        except ValueError:
            error = "Harga dan stok harus angka valid!"

    return render_template_string(HTML_TEMPLATE, page='restock_nokprem', user_data=u_data, success_msg=success_msg, error=error, channel_link=c_link, cs_link=cs_link)

@app.route('/owner/deposits')
def owner_deposits():
    if 'user' not in session or session.get('role') != 'owner': 
        return redirect(url_for('dashboard'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deposits ORDER BY id DESC")
    deposits = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='owner_deposits', deposits=deposits, user_data=u_data, channel_link=c_link, cs_link=cs_link)

@app.route('/owner/approve_deposit/<int:deposit_id>')
def approve_deposit(deposit_id):
    if 'user' not in session or session.get('role') != 'owner': 
        return redirect(url_for('dashboard'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,))
    dep = cursor.fetchone()
    if dep and dep['status'] == 'Pending':
        cursor.execute("UPDATE deposits SET status = 'Sukses' WHERE id = ?", (deposit_id,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (dep['amount'], dep['username']))
        conn.commit()
    conn.close()
    return redirect(url_for('owner_deposits'))

@app.route('/order/nokprem', methods=['GET', 'POST'])
def order_nokprem():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    error = None
    success_msg = None

    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        product_id = request.form['product_id']
        cursor.execute("SELECT * FROM nokprem_products WHERE id = ?", (product_id,))
        prod = cursor.fetchone()

        if not prod or prod['stock'] <= 0:
            error = "Maaf, stok nokprem ini kosong!"
        elif u_data['balance'] < prod['price']:
            error = "Saldo Anda tidak mencukupi!"
        else:
            new_stock = prod['stock'] - 1
            new_balance = u_data['balance'] - prod['price']
            dummy_phone = f"+{random.randint(628100000000, 628999999999)}"
            timestamp = time.strftime('%d-%m-%Y %H:%M')

            cursor.execute("UPDATE nokprem_products SET stock = ? WHERE id = ?", (new_stock, product_id))
            cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, session['user']))
            cursor.execute("INSERT INTO orders (username, service_name, price, phone_number, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                           (session['user'], prod['country_service'], prod['price'], dummy_phone, 'Menunggu sms otp', timestamp))
            conn.commit()
            success_msg = f"Berhasil memesan nokprem! Silakan cek menu Riwayat Pesanan."
            u_data = get_user_data(session['user'])

    cursor.execute("SELECT * FROM nokprem_products ORDER BY id DESC")
    products = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='order_nokprem', products=products, user_data=u_data, error=error, success_msg=success_msg, channel_link=c_link, cs_link=cs_link)

@app.route('/riwayat-pesanan')
def riwayat_pesanan_page():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE username = ? ORDER BY id DESC LIMIT 1", (session['user'],))
    pesanan = cursor.fetchone()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, page='riwayat_pesanan', pesanan=pesanan, user_data=u_data, channel_link=c_link, cs_link=cs_link)

@app.route('/api/order/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'user' not in session: return jsonify({'success': False})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ? AND username = ?", (order_id, session['user']))
    ord_data = cursor.fetchone()
    
    if ord_data and ord_data['status'] == 'Menunggu sms otp':
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (ord_data['price'], session['user']))
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Pesanan berhasil dibatalkan dan saldo telah dikembalikan.'})
    
    conn.close()
    return jsonify({'success': False, 'message': 'Pesanan tidak ditemukan atau sudah diproses.'})

@app.route('/deposit', methods=['GET'])
def deposit_saldo():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    return render_template_string(HTML_TEMPLATE, page='deposit', user_data=u_data, channel_link=c_link, cs_link=cs_link)

@app.route('/deposit/qris', methods=['POST'])
def deposit_qris():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, qris_img = get_settings()
    u_data = get_user_data(session['user'])
    try:
        amount = int(request.form['amount'])
        if amount <= 0: raise ValueError()
        
        timestamp = time.strftime('%d-%m-%Y %H:%M')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO deposits (username, amount, status, timestamp) VALUES (?, ?, ?, ?)", 
                       (session['user'], amount, 'Pending', timestamp))
        conn.commit()
        conn.close()
        return render_template_string(HTML_TEMPLATE, page='deposit_qris', amount=amount, qris_image=qris_img, user_data=u_data, channel_link=c_link, cs_link=cs_link)
    except ValueError:
        return redirect(url_for('deposit_saldo'))

@app.route('/game/bomb')
def game_bomb_page():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    return render_template_string(HTML_TEMPLATE, page='game_bomb', user_data=u_data, channel_link=c_link, cs_link=cs_link)

@app.route('/game/dice')
def game_dice_page():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    return render_template_string(HTML_TEMPLATE, page='game_dice', user_data=u_data, channel_link=c_link, cs_link=cs_link)

@app.route('/api/game/bomb', methods=['POST'])
def api_game_bomb():
    if 'user' not in session: return jsonify({'success': False})
    u_data = get_user_data(session['user'])
    if u_data['game_limit'] <= 0:
        return jsonify({'status': 'boom', 'message': '⚠️ Limit game habis!', 'remaining_limit': 0})
    
    data = request.get_json()
    chosen_index = data.get('index')
    bomb_index = random.randint(0, 5)
    
    conn = get_db()
    cursor = conn.cursor()
    new_limit = u_data['game_limit'] - 1
    
    if chosen_index == bomb_index:
        new_score = max(0, u_data['score'] - 15)
        cursor.execute("UPDATE users SET score = ?, game_limit = ? WHERE username = ?", (new_score, new_limit, session['user']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'boom', 'message': '💥 <b>BOOM!</b> Kotak bom meledak! Score -15', 'remaining_limit': new_limit})
    else:
        reward_score = random.randint(15, 30)
        new_score = u_data['score'] + reward_score
        cursor.execute("UPDATE users SET score = ?, game_limit = ? WHERE username = ?", (new_score, new_limit, session['user']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'safe', 'message': f'🎉 <b>AMAN!</b> Anda dapat <b>+{reward_score} Score</b>!', 'remaining_limit': new_limit})

@app.route('/api/game/dice', methods=['POST'])
def api_game_dice():
    if 'user' not in session: return jsonify({'success': False})
    u_data = get_user_data(session['user'])
    if u_data['game_limit'] <= 0:
        return jsonify({'result': 'lose', 'message': '⚠️ Limit habis!', 'remaining_limit': 0})
    
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    conn = get_db()
    cursor = conn.cursor()
    new_limit = u_data['game_limit'] - 1
    
    if player_roll > bot_roll:
        reward_limit = random.randint(150, 250)
        new_limit += reward_limit
        new_score = u_data['score'] + 30
        msg = f"🎉 <b>MENANG!</b> Dadu ({player_roll}) vs Bot ({bot_roll}). +{reward_limit} Limit!"
        res = 'win'
    elif player_roll == bot_roll:
        new_score = u_data['score'] + 5
        msg = f"🤝 <b>SERI!</b> Nilai sama ({player_roll})."
        res = 'draw'
    else:
        new_score = max(0, u_data['score'] - 5)
        msg = f"😢 <b>KALAH!</b> Dadu ({player_roll}) vs Bot ({bot_roll})."
        res = 'lose'
        
    cursor.execute("UPDATE users SET score = ?, game_limit = ? WHERE username = ?", (new_score, new_limit, session['user']))
    conn.commit()
    conn.close()
    return jsonify({'result': res, 'player_roll': player_roll, 'bot_roll': bot_roll, 'message': msg, 'remaining_limit': new_limit})

@app.route('/leaderboard')
def leaderboard():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, score, game_limit FROM users ORDER BY score DESC LIMIT 10")
    leaders = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='leaderboard', user_data=u_data, leaders=leaders, channel_link=c_link, cs_link=cs_link)

@app.route('/livechat', methods=['GET', 'POST'])
def livechat():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, _ = get_settings()
    u_data = get_user_data(session['user'])
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        message = request.form.get('message', '')
        target_user = request.form.get('target_user', 'owner')
        sender = session['user']
        timestamp = time.strftime('%H:%M')
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(f"{int(time.time())}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/{filepath}"

        cursor.execute("INSERT INTO live_chat (sender, receiver, message, image_url, timestamp) VALUES (?, ?, ?, ?, ?)", 
                       (sender, target_user, message, image_url, timestamp))
        conn.commit()
        conn.close()
        return redirect(url_for('livechat'))
    
    if session.get('role') == 'owner':
        cursor.execute("SELECT * FROM live_chat ORDER BY id ASC")
    else:
        cursor.execute("SELECT * FROM live_chat WHERE sender = ? OR receiver = ? ORDER BY id ASC", (session['user'], session['user']))
    chats = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='livechat', chats=chats, user_data=u_data, channel_link=c_link, cs_link=cs_link)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session: return redirect(url_for('login'))
    c_link, cs_link, qris_img = get_settings()
    u_data = get_user_data(session['user'])
    success = False
    if request.method == 'POST' and session.get('role') == 'owner':
        new_c = request.form['channel_link']
        new_cs = request.form['cs_link']
        new_qris = request.form['qris_image']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO settings (key, value) VALUES ('channel_link', ?)", (new_c,))
        cursor.execute("REPLACE INTO settings (key, value) VALUES ('cs_link', ?)", (new_cs,))
        cursor.execute("REPLACE INTO settings (key, value) VALUES ('qris_image', ?)", (new_qris,))
        conn.commit()
        conn.close()
        success = True
        c_link, cs_link, qris_img = new_c, new_cs, new_qris
    return render_template_string(HTML_TEMPLATE, page='settings', user_data=u_data, channel_link=c_link, cs_link=cs_link, qris_image=qris_img, success=success)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            error = "Username atau password salah!"
    return render_template_string(HTML_TEMPLATE, page='login', title='Login AldoMultiDevice', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (first_name, last_name, phone, username, password, role, score, game_limit, balance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                           (first_name, last_name, phone, username, password, 'user', 0, 10, 0))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = "Username sudah terdaftar!"
    return render_template_string(HTML_TEMPLATE, page='register', title='Daftar Akun AldoMultiDevice', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
