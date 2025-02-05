import base64
import datetime
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from gmail_auth import authenticate_gmail

def get_email_body(payload):
    """Извлекает HTML-версию письма."""
    html_body = ""

    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part['body']:
                html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors="ignore")

    return html_body.strip()

def extract_product_details(email_html):
    """Извлекает названия товаров и изображения из HTML."""
    if not email_html:
        print("❌ HTML-контент отсутствует.")
        return []

    soup = BeautifulSoup(email_html, 'html.parser')

    # Находим все товары в письме
    product_blocks = soup.find_all('tr')  

    order_items = []
    seen_items = set()  # Используем для фильтрации дубликатов

    for block in product_blocks:
        # 🔍 Находим изображение товара
        img_tag = block.find('img')
        img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

        # Фильтруем нерелевантные изображения (логотипы, Mastercard и т. д.)
        if img_url and ("asoslogo" in img_url or "content/images" in img_url or "mastercard" in img_url):
            continue  

        # 🔍 Находим название товара (обычно в <td>)
        name_tag = block.find('td')
        name = name_tag.get_text(strip=True) if name_tag else None

        # Убираем дубликаты и пустые значения
        if name and img_url and (name, img_url) not in seen_items:
            order_items.append({"name": name, "image": img_url})
            seen_items.add((name, img_url))  # Добавляем в множество, чтобы не повторялось

    if not order_items:
        print("❌ Товары не найдены.")
        return []

    print(f"🛍 Найдено {len(order_items)} товаров.")
    return order_items

def fetch_asos_orders():
    """Ищет заказы из ASOS."""
    print("🚀 Запуск fetch_asos_orders.py...")

    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    query = f'from:ilija.junkin@gmail.com AND subject:"Thanks for your order!" AND after:2021/02/01'

    print(f"🔎 Поиск писем с запросом: {query}")
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

            email_html = get_email_body(payload)  # Получаем HTML-версию

            # 🔹 Извлекаем товары
            order_items = extract_product_details(email_html)

            if order_items:
                print("\n🛍 ASOS Order Details:")
                for item in order_items:
                    print(f"- {item['name']}")
                    print(f"  🖼 {item['image']}")

        except Exception as e:
            print(f"❌ Ошибка обработки письма {msg_id}: {e}")

if __name__ == "__main__":
    fetch_asos_orders()