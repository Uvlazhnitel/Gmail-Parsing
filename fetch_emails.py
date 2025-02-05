import base64
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from gmail_auth import authenticate_gmail

def get_email_body(payload):
    """Extracts the HTML version of the email."""
    html_body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part['body']:
                html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors="ignore")
    return html_body.strip()

def extract_product_details(email_html):
    """Extracts product names and images from the HTML."""
    if not email_html:
        return []

    soup = BeautifulSoup(email_html, 'html.parser')

    order_items = []
    seen_items = set()

    product_blocks = soup.find_all("tr")  # Find all table rows containing products

    for block in product_blocks:
        name_tag = block.find("a", style=lambda value: value and "text-decoration:none" in value)
        img_tag = block.find("img")

        name = name_tag.get_text(strip=True) if name_tag else None
        img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

        # Filter out irrelevant images (logos, Mastercard, etc.)
        if img_url and ("asoslogo" in img_url or "content/images" in img_url or "mastercard" in img_url):
            continue

        if name and img_url and (name, img_url) not in seen_items:
            order_items.append({"name": name, "image": img_url})
            seen_items.add((name, img_url))

    return order_items

def fetch_asos_orders():
    """Fetches orders from ASOS."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    query = 'from:orders@asos.com AND subject:"Thanks for your order!" AND after:2021/02/01'

    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])

    if not messages:
        print("❌ No ASOS orders found.")
        return
    
    for msg in messages:
        try:
            msg_id = msg['id']
            email_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = email_data['payload']
            email_html = get_email_body(payload)

            order_items = extract_product_details(email_html)

            if order_items:
                print(f"\n📩 Found in email ID: {msg_id}")
                for item in order_items:
                    print(f"- {item['name']}")
                    print(f"  🖼 {item['image']}")

        except Exception as e:
            print(f"❌ Error processing email {msg_id}: {e}")

if __name__ == "__main__":
    fetch_asos_orders()