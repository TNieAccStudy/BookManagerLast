from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import json
import os
# Load credentials and tokens
current_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(current_dir, 'credentials.json')
token_path = os.path.join(current_dir, 'token.json')
with open(credentials_path,mode ='r') as creds_file:
    credentials_info = json.load(creds_file)['installed']
    
with open(token_path,'r') as token_file:
    token_info = json.load(token_file)

def get_gmail_service():
    creds = Credentials(
        token=token_info['access_token'],
        refresh_token=token_info['refresh_token'],
        token_uri=credentials_info['token_uri'],
        client_id=credentials_info['client_id'],
        client_secret=credentials_info['client_secret']
    )
    print(creds)
    return build('gmail', 'v1', credentials=creds)

def create_message_html(from_address, to, subject, body, is_html=False):
    message = MIMEText(body, 'html' if is_html else 'plain')
    message['to'] = to
    message['from'] = from_address
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}
def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text, 'html') 
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    return {'raw': raw}

def send_email(cart, name, phone, email, address, total_amount, order_id, method_bank=None):
    try:
        service = get_gmail_service()
        subject = "Thông Tin Đơn Hàng"
        formatted_total_amount = "{:,.0f}".format(total_amount).replace(",", ".")
        
        method_bank_html = ""
        if method_bank:
            method_bank_html = f"<h1>Vui lòng thanh toán với stk: {method_bank} - Ngân hàng: MoMo</h1>"

        body = f"""
        <html>
        <body>
            <h1>Cảm ơn bạn đã đặt hàng tại Book Delta ❤️</h1>
            <h1>Thông Tin Đơn Hàng</h1>
            <h2>Mã Đơn Hàng: #{order_id}</h2>
            <h2>Thông Tin Người Nhận:</h2>
            <p><strong>Họ Tên :</strong> {name}</p>
            <p><strong>Số Điện Thoại:</strong> {phone}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Địa Chỉ Nhận:</strong> {address}</p>
            <p><strong>Tổng Tiền:</strong> {formatted_total_amount} VNĐ</p>
            {method_bank_html}
            <h2>Chi Tiết Đơn Hàng:</h2>
            <table class="table table-bordered table-striped table-hover"  border="1">
                <thead class="table-dark fs-3">
                    <tr>
                        <th scope="col">Sản phẩm</th>
                        <th scope="col">Đơn giá</th>
                        <th scope="col">Số lượng</th>
                        <th scope="col">Thành Tiền</th>
                    </tr>
                </thead>
                <tbody class="fs-4">
        """
        for item, details in cart.items():
            if details['is_selected']:
                formatted_price = "{:,.0f}".format(details['price']).replace(",", ".")
                formatted_total = "{:,.0f}".format(details['price'] * details['quantity']).replace(",", ".")
                body += f"""
                    <tr style="height:60px;" id="books{details['id']}">
                        <td class="align-middle">
                            <div class="d-flex align-items-center">
                                <img src="{details['image']}" class="img-fluid rounded-3" style="width: 120px;height:100px;" alt="Book">
                                <div class="flex-column ms-4">
                                    <p class="mb-2">{details['title']}</p>
                                </div>
                            </div>
                        </td>
                        <td class="align-middle">
                            <p class="mb-0" style="font-weight: 500;">{formatted_price} VNĐ</p>
                        </td>
                        <td class="align-middle">
                            <div class="d-flex flex-row align-items-center">
                                <p class="fs-4 mb-0">{details['quantity']}</p>
                            </div>
                        </td>
                        <td class="align-middle">
                            <p class="mb-0" style="font-weight: 500;">{formatted_total} VNĐ</p>
                        </td>
                    </tr>
                """
        body += """
                </tbody>
            </table>
        </body>
        </html>
        """
        to_address = email
        message = create_message("prolathe633@gmail.com", to_address, subject, body)
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        print(f"Message sent. ID: {sent_message['id']}")
        return sent_message['id']
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def send_email_android(order_details, name, phone, email, address, order_id, method_bank=None):

    try:
        service = get_gmail_service()
        subject = "Thông Tin Đơn Hàng"
        total_amount=0
        for  taked_book in order_details:
            total_amount+=taked_book.book.prices[0].price * taked_book.quantity
        formatted_total_amount = "{:,.0f}".format(total_amount).replace(",", ".")
        
        method_bank_html = ""
        if method_bank:
            method_bank_html = f"<h1>Vui lòng thanh toán với stk: {method_bank} - Ngân hàng: MoMo</h1>"

        body = f"""
        <html>
        <body>
            <h1>Cảm ơn bạn đã đặt hàng tại Book Delta ❤️</h1>
            <h1>Thông Tin Đơn Hàng</h1>
            <h2>Mã Đơn Hàng: #{order_id}</h2>
            <h2>Thông Tin Người Nhận:</h2>
            <p><strong>Họ Tên :</strong> {name}</p>
            <p><strong>Số Điện Thoại:</strong> {phone}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Địa Chỉ Nhận:</strong> {address}</p>
            <p><strong>Tổng Tiền:</strong> {formatted_total_amount} VNĐ</p>
            {method_bank_html}
            <h2>Chi Tiết Đơn Hàng:</h2>
            <table class="table table-bordered table-striped table-hover"  border="1">
                <thead class="table-dark fs-3">
                    <tr>
                        <th scope="col">Sản phẩm</th>
                        <th scope="col">Đơn giá</th>
                        <th scope="col">Số lượng</th>
                        <th scope="col">Thành Tiền</th>
                    </tr>
                </thead>
                <tbody class="fs-4">
        """
        for details in order_details:
                formatted_price = "{:,.0f}".format(details.book.prices[0].price).replace(",", ".")
                formatted_total = "{:,.0f}".format(details.book.prices[0].price * details.quantity).replace(",", ".")
                body += f"""
                    <tr style="height:60px;" id="books{details.id}">
                        <td class="align-middle">
                            <div class="d-flex align-items-center">
                                <img src="{details.book.image}" class="img-fluid rounded-3" style="width: 120px;height:100px;" alt="Book">
                                <div class="flex-column ms-4">
                                    <p class="mb-2">{details.book.title}</p>
                                </div>
                            </div>
                        </td>
                        <td class="align-middle">
                            <p class="mb-0" style="font-weight: 500;">{formatted_price} VNĐ</p>
                        </td>
                        <td class="align-middle">
                            <div class="d-flex flex-row align-items-center">
                                <p class="fs-4 mb-0">{details.quantity}</p>
                            </div>
                        </td>
                        <td class="align-middle">
                            <p class="mb-0" style="font-weight: 500;">{formatted_total} VNĐ</p>
                        </td>
                    </tr>
                """
        body += """
                </tbody>
            </table>
        </body>
        </html>
        """
        to_address = email
        message = create_message("prolathe633@gmail.com", to_address, subject, body)
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        print(f"Message sent. ID: {sent_message['id']}")
        return sent_message['id']
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

