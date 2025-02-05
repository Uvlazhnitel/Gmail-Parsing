import base64
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from gmail_auth import authenticate_gmail

def get_email_body(payload):
    html_body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part['body']:
                html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors="ignore")
    return html_body.strip()

def extract_product_details(email_html):
    if not email_html:
        return []

    soup = BeautifulSoup(email_html, 'html.parser')

    order_items = []
    seen_items = set()

    for offer in soup.find_all("div", itemprop="acceptedOffer"):
        name_tag = offer.find("meta", itemprop="name")
        img_tag = offer.find("link", itemprop="image")
        price_tag = offer.find("meta", itemprop="price")

        name = name_tag["content"] if name_tag else "Неизвестный товар"
        img_url = img_tag["href"] if img_tag else None
        price = price_tag["content"] if price_tag else "Нет данных"

        if name and img_url and (name, img_url) not in seen_items:
            order_items.append({"name": name, "image": img_url, "price": price})
            seen_items.add((name, img_url))

    return order_items

def fetch_asos_orders():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    query = 'from:orders@asos.com AND subject:"Thanks for your order!" AND after:2021/02/01'

    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])

    if not messages:
        print("❌ Заказы ASOS не найдены.")
        return
    
    for msg in messages:
        try:
            msg_id = msg['id']
            email_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = email_data['payload']
            email_html = get_email_body(payload)

            order_items = extract_product_details(email_html)

            if order_items:
                print(f"\n📩 Найдено в письме ID: {msg_id}")
                for item in order_items:
                    print(f"- {item['name']} | {item['price']}")
                    print(f"  🖼 {item['image']}")

        except Exception as e:
            print(f"❌ Ошибка обработки письма {msg_id}: {e}")

if __name__ == "__main__":
    fetch_asos_orders()