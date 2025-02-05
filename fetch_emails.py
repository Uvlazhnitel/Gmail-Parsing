import base64
import re
import datetime
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from gmail_auth import authenticate_gmail

def get_email_body(payload):
    """Извлекает текстовую и HTML-версию письма"""
    message_body = ""
    html_body = ""

    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            if 'body' in part and 'data' in part['body']:
                data = part['body']['data']
                decoded_text = base64.urlsafe_b64decode(data).decode('utf-8', errors="ignore")

                if mime_type == 'text/plain':
                    message_body += decoded_text + "\n"
                elif mime_type == 'text/html':
                    html_body = decoded_text  # Сохраняем HTML-версию

    elif 'body' in payload and 'data' in payload['body']:
        data = payload['body']['data']
        message_body = base64.urlsafe_b64decode(data).decode('utf-8', errors="ignore")

    return message_body if message_body else "No content available", html_body

def extract_order_details(email_text, email_html):
    """Извлекает названия товаров и ссылки на изображения из писем ASOS"""
    order_items = []

    print("🔎 Ищем товары...")
    item_pattern = re.findall(r'(\b[A-Za-z0-9&\-\s]+)\s+\€\d+[\.,]\d{2}', email_text)

    image_links = re.findall(r'(https?://[^\s]+(?:jpg|jpeg|png|webp))', email_text)

    # 🔹 Если нет картинок в тексте, ищем их в HTML
    if not image_links and email_html:
        print("🔎 Ищем изображения в HTML...")
        soup = BeautifulSoup(email_html, 'html.parser')
        img_tags = soup.find_all('img')
        image_links = [img['src'] for img in img_tags if 'src' in img.attrs]

    for index, item in enumerate(item_pattern):
        item_info = {
            "name": item.strip(),
            "image": image_links[index] if index < len(image_links) else "No image available"
        }
        order_items.append(item_info)

    print(f"🛍 Найдено товаров: {len(order_items)}")
    return order_items

def convert_timestamp_to_date(timestamp):
    """Преобразует UNIX timestamp из Gmail API в читаемый формат даты"""
    date = datetime.datetime.fromtimestamp(int(timestamp) / 1000, datetime.UTC)
    return date.strftime('%Y-%m-%d %H:%M:%S')

def fetch_asos_orders():
    """Ищет все чеки из ASOS с subject 'Thanks for your order!' начиная с сегодняшнего дня"""
    print("🚀 Запуск fetch_asos_orders.py...")

    creds = authenticate_gmail()
    print("✅ Gmail API аутентифицирован!")

    service = build('gmail', 'v1', credentials=creds)
    print("📩 Подключение к Gmail API...")

    # 🔹 Получаем сегодняшнюю дату в формате YYYY/MM/DD
    today = datetime.datetime.today().strftime('%Y/%m/%d')

    # 🔹 Ищем ТОЛЬКО письма от ASOS с темой "Thanks for your order!" с сегодняшнего дня
    query = f'from:ilija.junkin@gmail.com AND subject:"Thanks for your order!" AND after:2021/02/01'

    print(f"🔎 Выполняем поиск писем с запросом: {query}")
    results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
    messages = results.get('messages', [])

    print(f"📬 Найдено {len(messages)} писем!" if messages else "❌ Писем не найдено.")

    if not messages:
        return
    
    for msg in messages:
        try:
            msg_id = msg['id']
            print(f"\n📧 Обрабатываем письмо ID: {msg_id}")

            email_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = email_data['payload']
            headers = payload['headers']

            # 🔹 Получаем тему письма
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')

            # 🔹 Получаем отправителя
            sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')

            # 🔹 Получаем дату письма
            date_timestamp = email_data.get('internalDate', 'Unknown Date')
            email_date = convert_timestamp_to_date(date_timestamp) if date_timestamp != 'Unknown Date' else "Unknown Date"

            print(f"📩 Subject: {subject}\n👤 Sender: {sender}\n📅 Date: {email_date}")

            # 🔹 Получаем полный текст и HTML-версию письма
            email_text, email_html = get_email_body(payload)

            # 🔹 Извлекаем товары и картинки
            order_items = extract_order_details(email_text, email_html)
            if not order_items:
                print("❌ Товары не найдены в этом письме.")
                continue  # Пропускаем письмо, если нет товаров

            print("🛍 Ordered items:")
            for item in order_items:
                print(f"- {item['name']}")
                print(f"  🖼 Image: {item['image']}")

        except Exception as e:
            print(f"❌ Ошибка обработки письма {msg_id}: {e}")

if __name__ == "__main__":
    fetch_asos_orders()