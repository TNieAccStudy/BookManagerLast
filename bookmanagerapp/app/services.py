import cv2
from pyzbar.pyzbar import decode
import uuid
import requests
import hmac
import json
import hashlib
from flask_login import current_user
def scan_barcode():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not cap.isOpened():
        return "Không thể mở webcam."
    print("Đưa mã vạch hoặc mã QR vào trước camera...")
    while True:
        ret, frame = cap.read()
        if not ret:
            return "Không thể nhận hình ảnh từ webcam."
        barcodes = decode(frame)
        if barcodes:
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                print(f"Đã quét: {barcode_data} (Loại: {barcode_type})")
                return barcode_data
        cv2.imshow("Quét mã vạch", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return "Đã quét mã vạch thành công."

def get_qr_momo( amount, redriectUrl,ipUrl="",order_id =None):
        # Cấu hình API MoMo
        endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
        partnerCode = "MOMO"
        accessKey = "F8BBA842ECF85"
        secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
        # orderInfo=f'Thanh Toán Đơn Hàng bởi nhân viên {current_user.id} '
        orderInfo=f'Thanh Toán'
        if order_id:
            orderInfo = f"Mã đơn hàng: #{str(order_id)}"
        redirectUrl = f"http://127.0.0.1:5000{redriectUrl}"
        # redirectUrl = f"https://6bbf-2405-4802-811a-c990-7876-31-cdfc-518c.ngrok-free.app{redriectUrl}"
        ipnUrl = f"http://127.0.0.1:5000{ipUrl}"
        amount = str(amount)
        orderId = str(uuid.uuid4())
        requestId = str(uuid.uuid4())
        requestType = "captureWallet"
        extraData = ""

        # Tạo chữ ký (signature)
        rawSignature = (
            f"accessKey={accessKey}&amount={amount}&extraData={extraData}"
            f"&ipnUrl={ipnUrl}&orderId={orderId}&orderInfo={orderInfo}"
            f"&partnerCode={partnerCode}&redirectUrl={redirectUrl}"
            f"&requestId={requestId}&requestType={requestType}"
        )
        h = hmac.new(bytes(secretKey, 'utf-8'), bytes(rawSignature, 'utf-8'), hashlib.sha256)
        signature = h.hexdigest()

        # Dữ liệu gửi đến API
        data = {
            'partnerCode': partnerCode,
            'partnerName': "Test",
            'storeId': "MomoTestStore",
            'requestId': requestId,
            'amount': amount,
            'orderId': orderId,
            'orderInfo': orderInfo,
            'redirectUrl': redirectUrl,
            'ipnUrl': ipnUrl,
            'lang': "vi",
            'extraData': extraData,
            'requestType': requestType,
            'signature': signature
        }

        # Gửi yêu cầu POST đến API
        response = requests.post(endpoint, json=data, headers={'Content-Type': 'application/json'})
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.json()}")
        return response

def ger_respone_momo(data):
        partnerCode = data.get('partnerCode')
        orderId = data.get('orderId')
        requestId = data.get('requestId')
        amount = data.get('amount')
        orderInfo = data.get('orderInfo')
        orderType = data.get('orderType')
        transId = data.get('transId')
        resultCode = data.get('resultCode')
        message = data.get('message')
        payType = data.get('payType')
        responseTime = data.get('responseTime')
        extraData = data.get('extraData')
        signature = data.get('signature')

        # Verify signature
        rawSignature = f"accessKey=F8BBA842ECF85&amount={amount}&extraData={extraData}&message={message}&orderId={orderId}&orderInfo={orderInfo}&orderType={orderType}&partnerCode={partnerCode}&payType={payType}&requestId={requestId}&responseTime={responseTime}&resultCode={resultCode}&transId={transId}"
        secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
        h = hmac.new(bytes(secretKey, 'utf-8'), bytes(rawSignature, 'utf-8'), hashlib.sha256)
        expected_signature = h.hexdigest()
        return resultCode


# delivery_service_url = 'https://deliverysrv203.pythonanywhere.com'
delivery_service_url = 'http://44.204.135.140:7300/'

def add_order_for_delivery(order_id):
    url = delivery_service_url + '/api/packages/'
    body = {
        "order_id": order_id,
    }
    headers = {
        "Content-Type": "application/json",
    }
    return requests.post(url=url,json=body,headers=headers)
