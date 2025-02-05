from googleapiclient.discovery import build
from gmail_auth import authenticate_gmail

def search_order_emails():
    """Ищет письма с подтверждением заказов только от магазинов одежды"""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Фильтр: ищем письма от магазинов одежды с ключевыми словами "заказ", "order", "purchase"
    fashion_stores = [
        "asos.com", "zara.com", "hm.com", "uniqlo.com", "nike.com",
        "adidas.com", "mango.com", "pullandbear.com", "bershka.com"
    ]
    
    query = " OR ".join([f"from:{store}" for store in fashion_stores])
    query += " AND (subject:order OR subject:purchase OR subject:заказ OR subject:pasūtījums)"
    
    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])

    if not messages:
        print("❌ No order emails from fashion stores found!")
        return
    
    print(f"✅ Found {len(messages)} order-related emails from fashion stores.")
    
    for msg in messages:
        msg_id = msg['id']
        email_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = email_data['payload']
        headers = payload['headers']

        # Получаем тему письма
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')

        # Получаем отправителя
        sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')

        print(f"\n📩 Subject: {subject}\n👤 Sender: {sender}")

if __name__ == "__main__":
    search_order_emails()