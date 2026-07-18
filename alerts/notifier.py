import os
import sqlite3
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load env variables if they exist
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs", "price_history.db"))

def send_windows_toast(title: str, message: str):
    """Sends a native Windows Toast Notification using PowerShell without external dependencies."""
    ps_script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $APP_ID = 'Universal Price Aggregator'
    $template = @"
    <toast>
        <visual>
            <binding template="ToastText02">
                <text id="1">{title}</text>
                <text id="2">{message}</text>
            </binding>
        </visual>
    </toast>
"@
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
    """
    try:
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Failed to send Windows Toast: {e}")

def send_discord_alert(product_name: str, platform: str, current_price: float, target_price: float, target_url: str):
    if not DISCORD_WEBHOOK_URL:
        return
    payload = {
        "embeds": [{
            "title": "🚨 Target Price Reached!",
            "description": f"**{product_name}** on {platform} dropped below your target of ₹{target_price:,.2f}!",
            "color": 3066993, # Green
            "fields": [
                {"name": "Current Price", "value": f"₹{current_price:,.2f}", "inline": True},
                {"name": "Target Price", "value": f"₹{target_price:,.2f}", "inline": True},
                {"name": "Link", "value": f"[View Product]({target_url})", "inline": False}
            ],
            "footer": {"text": "Universal Price Aggregator"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

def evaluate_alerts():
    """Queries DB and triggers alerts if current prices are below targets."""
    print(f"[{datetime.now().strftime('%I:%M:%S %p')}] Evaluating target price alerts...")
    
    if not os.path.exists(DB_PATH):
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all active alerts
    cursor.execute("SELECT product_name, target_price FROM price_alerts")
    alerts = cursor.fetchall()
    
    for product_name, target_price in alerts:
        # Get the latest price for this product across all platforms
        cursor.execute("""
            SELECT platform, current_price, target_url 
            FROM price_logs 
            WHERE product_name = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (product_name,))
        latest = cursor.fetchone()
        
        if latest:
            platform, current_price, target_url = latest
            
            # Check if it dropped below threshold
            if current_price <= target_price:
                # Store the last alerted price in price_alerts to avoid spamming
                try:
                    cursor.execute("SELECT last_alerted_price FROM price_alerts WHERE product_name = ?", (product_name,))
                    last_alerted = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    # Dynamically add tracking column if it doesn't exist
                    cursor.execute("ALTER TABLE price_alerts ADD COLUMN last_alerted_price REAL")
                    last_alerted = None
                    
                if last_alerted is None or current_price < last_alerted:
                    print(f" └─ > ALERT TRIGGERED: {product_name} dropped to ₹{current_price}!")
                    
                    toast_title = "Price Drop Alert!"
                    toast_msg = f"{product_name} on {platform} is now ₹{current_price:,.2f} (Target: ₹{target_price:,.2f})"
                    send_windows_toast(toast_title, toast_msg)
                    send_discord_alert(product_name, platform, current_price, target_price, target_url)
                    
                    # Update last_alerted_price to prevent notification spam tomorrow if price stays same
                    cursor.execute("UPDATE price_alerts SET last_alerted_price = ? WHERE product_name = ?", (current_price, product_name))
                    conn.commit()

    conn.close()

if __name__ == "__main__":
    evaluate_alerts()
