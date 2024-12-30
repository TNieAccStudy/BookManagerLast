from config import app, db
from flask import render_template,request,jsonify,redirect,flash,session
import dao
from flask_login import login_user, logout_user,login_required
from flask_login import current_user
from enum import Enum as RoleEnum
from admins import admin,em_admin
import json
import dao
import utils
from datetime import datetime
import math
import services
from models import CancelReasonState, Order, StateOrder, UserRole, MethodBank, Book
from apscheduler.schedulers.background import BackgroundScheduler
import random

@app.route("/")
def index():
    if current_user.is_authenticated:
        if dao.get_taked_books_by_user_id(current_user.id):
            session['cart'] = dao.get_taked_books_by_user_id(current_user.id)
    cates = dao.load_categories()
    cate_id = request.args.get('cate_id',type=int)
    kw = request.args.get('kw')
    page = request.args.get('page', 1)
    order = request.args.get('order', 'desc')
    total = 0
    params = {}
    if cate_id:
        params['category_id'] = cate_id
        total = dao.count_books_by_cate_id(cate_id)
    else:
        total = dao.count_books()
    if kw:
        params['kw'] = kw
    print(page)
    books = dao.load_books(cate_id=cate_id, kw=kw, page=int(page),order=order)
    page_size = app.config.get('PAGE_SIZE', 0)
    print('total',total)
    print('size',math.ceil(total/page_size))
    print(cate_id)
    return render_template('index.html', categories=cates, books=books,
                           pages=math.ceil(total/page_size),cate_id=cate_id,current_page=int(page),order=order)

@app.route("/books/<int:book_id>")
def book_detail(book_id):
    has_successfully_ordered_and_can_comment = False
    book_ids = dao.get_book_ids_in_order_by_user_id()
    print('book',book_ids)
    if book_id in book_ids:
        has_successfully_ordered_and_can_comment = True
    book = dao.load_book_by_id(book_id)
    reviews = dao.get_review_by_book_id(book_id)
    previous_url = request.referrer or '/'
    return render_template('details.html', book=book,reviews=reviews,previous_url=previous_url,has_successfully_ordered_and_can_comment=has_successfully_ordered_and_can_comment)


@app.route("/books/<book_id>/reviews", methods=['POST'])
def add_review(book_id):
    try:
        check_review = dao.get_review_by_book_id_and_user_id(book_id)
        if check_review:
            return jsonify({'status': 500, 'err_msg': 'Bạn đã đánh giá cuốn sách này rồi!'})
        data = request.json
        review = dao.add_review(book_id, data.get('content'), data.get('rating'))
    except Exception as ex:
        return jsonify({'status': 500, 'err_msg': str(ex)})
    else:
        print(review.client.name)
        return jsonify({'status': 200, 'review': {
            'content': review.content,
            'created_date': review.created_at,
            'rating': review.rate,
            'user': {
                'name': review.client.name
            }
        }})
    
@app.route("/books/<book_id>/reviews/status", methods=['GET'])
def status_review(book_id):
    review = dao.get_review_by_book_id_and_user_id(book_id)
    if review:
        return jsonify({'status': 'reviewed'})
    return jsonify({'status': 'active'})


@app.context_processor
def common_responses():
    return {
        'categories': dao.load_categories(),
        'cart_stats': utils.count_cart(session.get('cart'))
    }

@app.route("/cart")
def cart():
    return render_template('cart.html')

@app.route("/checkout",methods=['GET'])
def check_out():
    info_user = None
    if  current_user.is_authenticated:
        info_user = dao.load_info_user_order_by_user_id(current_user.id)
        print(info_user)
    return render_template('checkout.html',info_user=info_user)


@app.route("/api/check-cart",methods=['GET'])
def api_check_out():
    cart = session.get('cart', {})
    selected_items = [item for item in cart.values() if item.get('is_selected')]
    if selected_items:
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'empty'})

from sendEmail.sendmail import send_email,send_email_android
@app.route("/orders", methods=['POST'])
def order_process():
    data = request.form
    if data.get('name') == '' or data.get('phone') == '' or data.get('email') == '' or data.get('address') == '' \
    or data.get('payment_method') == '' or (data.get('address-receive') == '' and data.get('store') == ''):
        return ''
    print("orders",data)
    cart = session.get('cart', {})
    print("cart",cart)
    method_bank = data.get('payment_method')
    if method_bank == 'cash':
        method_bank =MethodBank.BANKWHENGET
    if method_bank =='card':
        method_bank =MethodBank.MOMO
    method_bank=method_bank.name
    selected_items= {}
    selected_items = {k: v for k, v in cart.items() if v.get('is_selected')}
    stk_payment = None
    if not current_user.is_authenticated:
        if method_bank == MethodBank.MOMO.name:
            stk_payment = '0337562131'
        if 'address-receive' in data and data.get('address-receive'):
            order_id = dao.add_orders(data, selected_items,address = data.get('address-receive'),method_bank=method_bank)
            send_email(selected_items, data.get('name'), data.get('phone'), data.get('email'), data.get('address-receive'), utils.count_cart(cart).get('total_amount'),order_id=order_id,method_bank=stk_payment)
        if 'store' in data:
            order_id = dao.add_orders(data, selected_items, address = data.get('store'),method_bank=method_bank)
            send_email(selected_items, data.get('name'), data.get('phone'), data.get('email'), data.get('store'), utils.count_cart(cart).get('total_amount'),order_id,method_bank=stk_payment)
    else:
        user_id = current_user.id
        print(data)
        if 'address-receive' in data and data.get('address-receive'):
            dao.add_orders(data, selected_items,address = data.get('address-receive'),user_id=user_id,method_bank=method_bank)
        if 'store' in data :
            dao.add_orders(data, selected_items, address = data.get('store'),user_id=user_id,method_bank=method_bank)
        print("selected",selected_items)
        dao.delete_book_selected_in_taked_book_detail(selected_items)
    flash("Đặt hàng thành công!", "success")
    session['cart'] = {k: v for k, v in cart.items() if not v.get('is_selected')}
    if 'selected_all' in session:
        del session['selected_all']
    if not current_user.is_authenticated:
        return redirect('/')
    return redirect('/historyorder')

@app.route("/orders/<order_id>",methods=['GET'])
def order_detail(order_id):
    order = dao.load_order_by_id(order_id)
    order_detail = order['order_details']
    total_price = order['total_price']
    total_quantity = order['total_quantity']
    return render_template('order-detail.html', order=order_detail, total_price=total_price, total_quantity=total_quantity,order_id=order_id)


@app.route("/orders/<order_id>/review",methods=['GET'])
def order_detail_review(order_id):
    order = dao.load_order_by_id(order_id)
    order_detail = order['order_details']
    print(order_detail)
    total_price = order['total_price']
    total_quantity = order['total_quantity']
    return render_template('review-order.html', order=order_detail, total_price=total_price, total_quantity=total_quantity,order_id=order_id)
@app.route("/orders/<order_id>/cancel",methods=['GET'])
@login_required
def cancel_order(order_id):
    order = dao.load_order_by_id(order_id)
    order_detail = order['order_details']
    total_price = order['total_price']
    total_quantity = order['total_quantity']
    return render_template('cancel-order.html', order=order_detail, total_price=total_price, total_quantity=total_quantity,order_id=order_id)

@app.route("/orders/<order_id>/cancel",methods=['POST'])
def cancel_order_process(order_id):
    order_ids= dao.get_order_ids_in_cancle_order()
    if order_id in order_ids:
        return jsonify({'status': 500, 'err_msg': 'Đơn hàng đã được yêu cầu hủy rồi!'})
    
    data = request.json
    dao.add_cancel_order(order_id, data.get('reason'),CancelReasonState.PENDINGCANCEL)
    return jsonify({'status': 200})

@app.route("/orders/<order_id>/status", methods=['GET'])
def get_order_status(order_id):
    order_ids = dao.get_order_ids_in_cancle_order()
    state = dao.load_state_order_by_id(order_id)
    print('state',state)
    print('order_id',order_id)
    order_id = int(order_id)
    if state == 'CONFIRM':
        return jsonify({'status': 'confirmed'})
    if state == 'CANCEL':
        return jsonify({'status': 'cancelled'})
    
    
    if (order_id in order_ids and state == 'PENDINGPROCESSING') \
        or (order_id in order_ids and state == 'PENDINGCONFIRM') \
            or (order_id in order_ids and state == 'DELIVERING') \
                or (order_id in order_ids and state == 'PENDINGPAYMENT'):
        return jsonify({'status': 'requestcancelled__pending'})
    if state == 'PENDINGPAYMENT':
        return jsonify({'status': 'active'})
    if order_id in order_ids :
        return jsonify({'status': 'requestcancelled'})
    if state == 'PENDINGCONFIRM' or state == 'PENDINGPROCESSING' or 'DELIVERING' or '':
        return jsonify({'status': 'pending'})
    
    return jsonify({'status': 'confirmed'})
    





@app.route("/api/order/<order_id>",methods=['DELETE'])
def delete_order(order_id):
    dao.delete_order(order_id)
    return jsonify({'status': 200})


@app.route("/api/book/add", methods=['POST'])
def add_book():
    data = request.json
    books_data = data.get('books', [])
    added_books = []    
    for book_data in books_data:
        title = book_data.get('title')
        author = book_data.get('author')
        price = book_data.get('price')
        image = book_data.get('image')
        quantity = book_data.get('quantity')
        price_reduced= book_data.get('price_reduced')
        category_books = book_data.get('category_books')
        book = dao.add_book(title, author, image,price, quantity,price_reduced ,category_books)
        added_books.append(book)

    return jsonify([book.to_dict() for book in added_books])

@app.route("/historyorder",methods=['GET'])
@login_required
def history_order():
    orders= None
    data = request.args.to_dict()
    print('data',data)
    if data:
        print(f"Redirect data: {data}")
        result_code = services.ger_respone_momo(data)
        
        order_id = data.get('orderInfo').split('#')[1]
        if result_code == '0':
            dao.update_status_payed_order(int(order_id))
            print("Thanh Toán Thành Công")
        else:
            print("Thanh Toán Thất Bại")
    if current_user.is_authenticated:
        orders = dao.load_orders(current_user.id)
        print(orders)
    return render_template('historyorder.html',orders=orders)


@app.route("/orders/<order_id>/pay",methods=['get'])
def pay_order(order_id):
    order = dao.load_order_by_id(order_id)
    total_price = int(order['total_price'])
    response = services.get_qr_momo(total_price,'/historyorder',order_id=order_id)
    if response.status_code == 200:
        response_data = response.json()
        pay_url = response_data.get('payUrl')
        print(f'pay_url: {pay_url}')
        if pay_url:
            return redirect(pay_url)
        else:
            return jsonify({'error': 'Pay URL not found in MoMo response'}), 400
    else:
        return jsonify({'error': 'Failed to connect to MoMo API', 'details': response.text}), 500
    

@app.route("/api/historyorder",methods=['GET'])
def history_order_android():
    data = request.args.to_dict()
    print('data',data)
    if data:
        print(f"Redirect data: {data}")
        result_code = services.ger_respone_momo(data)
        
        order_id = data.get('orderInfo').split('#')[1]
        if result_code == '0':
            dao.update_status_payed_order(int(order_id))
            return "<h1>Payment successful</h1>"
    return "<h1>Payment failed</h1>"
@app.route("/orders/<order_id>/pay_android",methods=['get'])
def pay_order_android(order_id):
    orders = dao.load_order_by_id_android(order_id)
    total_price=0
    for order in orders:
        total_price+=order['price']*order['quantity']
    total_price = int(total_price)
    print(total_price)
    response = services.get_qr_momo(total_price,'/api/historyorder',order_id=order_id)
    if response.status_code == 200:
        response_data = response.json()
        pay_url = response_data.get('deeplink')
        if pay_url:
            return jsonify({'momo_deep_link': pay_url})
        else:
            return jsonify({'error': 'Pay URL not found in MoMo response'}), 400
    else:
        return jsonify({'error': 'Failed to connect to MoMo API', 'details': response.text}), 500
@app.route("/api/cart", methods=['POST'])
def add_to_cart():
    data = request.json
    print('cart',data)
    cart = session.get('cart', {})
    id= str(data.get('id'))
    price = data.get('price')
    if id in cart:
        cart[id]['quantity']+=1
    else:
        cart[id] = {
            "id": id,
            "title": data.get("title"),
            "price": price,
            "image": data.get("image"),
            "quantity": 1,
            "is_selected": False
        }
    if current_user.is_authenticated:
        dao.add_taked_book(int(id),price)
    session['cart'] = cart
    print(utils.count_cart(cart))
    return jsonify(utils.count_cart(cart))

@app.route("/api/cart/<book_id>", methods=['PUT'])
def update_cart(book_id):
    cart = session.get('cart',{})
    data = request.json
    if cart and book_id in cart:
        cart[book_id]['quantity'] = int(data.get('quantity'))
        print('Done')
        if current_user.is_authenticated:
            dao.update_taked_book_quantity(current_user.id, book_id, data.get('quantity'))
    session['cart'] = cart
    return jsonify(utils.count_cart(cart))

@app.route("/api/cart/<book_id>/select", methods=['PUT'])
def update_selection(book_id):
    data = request.json
    cart = session.get('cart', {})
    if data.get('is_selected') is False:
        session['selected_all'] = False
    if cart and book_id in cart:
        print(book_id)
        cart[book_id]['is_selected'] = data.get('is_selected', cart[book_id]['is_selected'])
        session['cart'] = cart
        print(session['cart'])
        return jsonify(utils.count_cart(cart))
    return jsonify({"error": "Item not found"}), 404

@app.route("/api/cart/select-all", methods=['PUT'])
def update_selection_all():
    data = request.json
    ids = data.get('ids', [])
    print(ids)
    cart = session.get('cart', {})
    if cart and ids:
        for book_id in ids:
            print(book_id)
            cart[book_id]['is_selected'] = data.get('is_selected', cart[book_id]['is_selected'])
        session['cart'] = cart
        if 'selected_all' not in session:
            session['selected_all'] = False
        
        session['selected_all'] = not session['selected_all']
        print(session['cart'])
        return jsonify(utils.count_cart(cart))
    return jsonify({"error": "Item not found"}), 404
@app.route("/api/cart/<book_id>", methods=['DELETE'])
def delete_cart(book_id):
    cart = session.get('cart',{})
    print(cart)
    if cart and book_id in cart:
        del cart[book_id]
        if current_user.is_authenticated:
            dao.delete_taked_book_detail_by_book_id(book_id, current_user.id)
    session['cart'] = cart

    print(session['cart'])
    
    return jsonify(utils.count_cart(cart))

@app.route('/admin/login', methods=['post'])
def login_admin():
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user, remember=True)
        next = request.args.get('next')
        print(next)
        if next:
            return redirect(next)
        return redirect('/admin')

@app.route('/login', methods=['post'])
def login_view():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username=username, password=password)
        cart = session.get('cart')
        if user:
            login_user(user, remember=True)
        else:
            return jsonify({'status': 500, 'err_msg': 'Sai Username Hoặc Password'})
        if cart:
            dao.add_taked_book_by_cart(cart)
            del session['cart']
        print(user)
        
        next = request.args.get('next')
        print(next)
        if next:
            return redirect(next)
        return jsonify({'status': 200})

    return jsonify({'status': 500, 'err_msg': 'Something wrong!'})

@app.route("/logout")
def logout_process():
    logout_user()
    if 'cart' in session:
        del session['cart']
    return redirect('/')
@app.route('/register', methods=['GET', 'POST'])
def register_process():
    err_msg = None
    if request.method == 'POST':
        confirm = request.form.get('password_confirmation')
        password = request.form.get('password')
        if password == confirm:
            data = request.form.copy()
            print(data)
            data.pop('password_confirmation', None)
            if dao.check_user_exist(data.get('username')):
                err_msg = 'Tên đăng nhập đã tồn tại!'
                return jsonify({'success': False, 'err_msg': err_msg})
            elif dao.check_email_exist(data.get('email')):
                err_msg = 'Email đã tồn tại!'
                return jsonify({'success': False, 'err_msg': err_msg})
            elif request.form.get('name') == '' or request.form.get('username') == '' or request.form.get('email') == '' or request.form.get('password') == '' or request.form.get('password_confirmation') == '':
                err_msg = ''
            else:
                dao.add_user(**data)
                return jsonify({'success': True, 'status': 200})
        else:
            err_msg = 'Mật khẩu KHÔNG khớp!'
    
    return jsonify({'success': False, 'err_msg': err_msg})

@app.route('/scan', methods=['POST'])
def scan():
    book_id = services.scan_barcode()
    print(book_id)
    if 'cart' not in session:
        session['cart'] = {}
    session['cart'] = dao.load_cart(session['cart'], book_id)
    print(session['cart'])
    return jsonify(utils.count_cart(session['cart']))


@app.route("/api/books", methods=['GET'])
def get_books():
    books = dao.load_books()
    print(books)
    return jsonify([book.to_dict() for book in books])
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = dao.load_categories()
    return jsonify([cate.to_dict() for cate in categories])




# @app.route('/em/cart', methods=['GET'])
# def load_em_cart():
#     pass

# phai sua lai cau truc cua Receipt boi vi no khong on
# xu ly viec xoa du lieu khoi session vi co luu trong database

@app.route('/api/em/pay', methods=['POST'])
def pay_taked_book():
    payment_method = request.json.get("paymentMethod")
    cart = utils.count_cart(session['cart'])
    print(payment_method)
    if(payment_method == "card"):
        total_price = cart.get('total_amount')
        print(total_price)
        total_price = int(total_price)
        response = services.get_qr_momo(total_price,'/em/cart')
        if response.status_code == 200:
            print('have momo get')
            response_data = response.json()
            pay_url = response_data.get('payUrl')
            if pay_url:
                print(f'redirect url: {pay_url}')
                return jsonify({'redirect': pay_url}),200
            else:
                return jsonify({'error': 'Pay URL not found in MoMo response'}), 400
        return jsonify({'error': 'Failed to connect to MoMo API', 'details': response.text}), 500
    elif payment_method == "cash":
        result = dao.add_receipt(details=cart['books'].values())
        if result:
            print('add reciept -- delete cart')
            if session['cart']:
                dao.delete_book_selected_in_taked_book_detail(session['cart'])
            session['cart'] = {}
        else:
            return jsonify({'error': 'Failed to effort add receipt to data'}), 501
        

    return jsonify({'redirect': '/em/cart'}),200



    


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.form
    username = data.get('username')
    password = data.get('password')

    user = dao.auth_user(username=username, password=password)
    print(user)
    if user:
        return jsonify({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'fullname': user.name,
            'password': user.password,
            
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    err_msg = None
    if request.method == 'POST':
        confirm = request.form.get('password_confirmation')
        password = request.form.get('password')
        if password == confirm:
            data = request.form.copy()
            print(data)
            data.pop('password_confirmation', None)
            if dao.check_user_exist(data.get('username')):
                err_msg = 'Tên đăng nhập đã tồn tại!'
                return jsonify({'success': False, 'err_msg': err_msg})
            elif dao.check_email_exist(data.get('email')):
                err_msg = 'Email đã tồn tại!'
                return jsonify({'success': False, 'err_msg': err_msg})
            elif request.form.get('name') == '' or request.form.get('username') == '' or request.form.get('email') == '' or request.form.get('password') == '' or request.form.get('password_confirmation') == '':
                err_msg = ''
            else:
                dao.add_user(**data)
                return jsonify({'success': True, 'status': 200})
        else:
            err_msg = 'Mật khẩu KHÔNG khớp!'
    
    return jsonify({'success': False, 'err_msg': err_msg})

@app.route('/api/user/<int:id>', methods=['GET'])
def get_user_by_id(id):
    user = dao.load_user_by_id(id)
    if user:
        return jsonify(user.to_dict())
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/user/<int:user_id>/taked_books', methods=['GET'])
def get_taked_books_by_user_id(user_id):
    taked_books = dao.load_taked_books_by_user_id(user_id)
    if not taked_books:
        return jsonify({'message': 'No books found for this user'}), 404
    result = []
    details = taked_books.details
    print(details)
    for detail in details:
        book_detail = dao.load_taked_book_detail_by_book_id(detail.book_id)
        if book_detail is None:
            continue
        book = book_detail
        print(book)
        if book:
            result.append({
                'title': book.title,
                'quantity': detail.quantity,
                'price': book.prices[0].price,
                'id':book.id,
                'image': book.image
            })
    return jsonify(result), 200
@app.route("/api/category/", methods=['GET'])
def get_book_in_category():
    cate_id = request.args.get('cate_id')
    kw = request.args.get('kw')
    page = request.args.get('page', 1)
    books = dao.load_books(cate_id=cate_id, kw=kw, page=int(page))
    return jsonify([book.to_dict() for book in books])

@app.route("/api/books/<int:book_id>")
def get_book_detail(book_id):
    book = dao.load_book_by_id(book_id)
    return jsonify(book.to_dict())

@app.route("/api/user/<int:user_id>/taked_book_details",methods=['POST'])
def add_taked_book_detail(user_id):
    data = request.form
    book_id = data.get('book_id')
    dao.add_taked_book_android(book_id,user_id)
    return jsonify({'status': 200})


@app.route("/api/user/<int:user_id>/taked_book_details/<int:book_id>",methods=['DELETE'])
def delete_taked_book_detail(user_id,book_id):
    if dao.delete_taked_book_detail_by_book_id(book_id,user_id):
        return jsonify({'status': 200})
    return jsonify({'status': 500})
# index.py

@app.route("/api/user/<int:user_id>/taked_book_details/<int:book_id>/quantity", methods=['PATCH'])
def update_taked_book_quantity(user_id, book_id):
    data = request.form
    new_quantity = data.get('quantity')

    if new_quantity is None:
        return jsonify({'message': 'Invalid data'}), 400

    success = dao.update_taked_book_quantity(user_id, book_id, new_quantity)
    if success:
        return jsonify({'status': 200, 'message': 'Quantity updated successfully'})
    else:
        return jsonify({'status': 500, 'message': 'Failed to update quantity'})


@app.route("/api/user/<int:user_id>/orders", methods=['POST'])
def order_process_android(user_id):
    data = request.form
    order_id = dao.add_orders_android(data,user_id=user_id)
    print(order_id)
    order_details = dao.load_orders_by_order_id_android(order_id)
    send_email_android(order_details, data.get('name'), data.get('phone'), data.get('email'), data.get('address'),order_id)
    
    return jsonify({'status': 200})


@app.route("/api/orders/<int:order_id>", methods=['GET'])
def get_order_detail(order_id):
    order = dao.load_order_by_id_android(order_id)

    return jsonify(order), 200
    
@app.route("/api/user/<int:user_id>/historyorder", methods=['GET'])
def get_history_order(user_id):
    orders = dao.load_orders(user_id)
    print( orders)
    return jsonify(orders), 200

@app.route("/api/regulations/book-amount", methods=['GET'])
def get_regulations():
    regulation = dao.get_regulation('import_book_amount')
    if regulation:
        regulation_dict = {
            'id': regulation.id,
            'name': regulation.name,
            'value': regulation.value
        }
        return jsonify(regulation_dict)
    else:
        return jsonify({'error': 'Regulation not found'}), 404


@app.route("/api/cancel_orders/<int:cancel_order_id>", methods=['PATCH'])
def update_cancel_order(cancel_order_id):
    print(f"cancel_id  : {cancel_order_id}")
    cancel_confirm = dao.confirm_cancel_order(cancel_order_id,CancelReasonState.CLIENTREQUIRED)
    return jsonify(cancel_confirm)

#thieu update
@app.route("/api/orders/<int:order_id>", methods=['PATCH'])
def update_order(order_id):
    confirmed_state = request.json.get("confirmedState")
    delivery_state = request.json.get("deliveryState")

    state = None
    cancel_state = None
    reason = ""
    
    if confirmed_state:
        
        if confirmed_state == 'cancel':
            state = StateOrder.CANCEL
        elif confirmed_state == 'confirm':
            state = StateOrder.PENDINGPROCESSING
        elif confirmed_state == 'delivery':
            state = StateOrder.DELIVERING
        elif confirmed_state == 'success':
            state = StateOrder.CONFIRM
        elif confirmed_state == 'shopcancel':
            state = StateOrder.CANCEL
            reason = "nhan vien huy vi co van de trong shop"
            cancel_state = CancelReasonState.SHOPREASON

        print(state)
    
    if delivery_state:
        #xu ly du lieu delivery tra ve
        state = StateOrder.CANCEL
        if delivery_state == 'SUCCESS':
            state = StateOrder.CONFIRM
        elif delivery_state == 'CLIENTNOTRECEIVE':
            cancel_state = CancelReasonState.CLIENTNOTRECEIVE
            reason = "nguoi dung khong nhan don hang"
        elif delivery_state == 'DELIVERYPROBLEM':
            cancel_state = CancelReasonState.DELIVERYREASON
            reason = "ben van chuyen co van de"
        
    return dao.update_order_with_state(order_id,state=state,reason=reason,cancel_state=cancel_state)



@app.route("/api/books/<book_id>/reviews", methods=['GET','POST'])
def add_review_android(book_id):
    if request.method == 'GET':
        reviews = dao.get_review_by_book_id(book_id)
        return jsonify([review.to_dict() for review in reviews])
    data = request.form
    content = data.get('content')
    user_id= data.get('user_id')
    try:
        dao.add_review(book_id,content,user_id )
    except Exception as ex:
        return jsonify({'status': 500, 'err_msg': str(ex)})
    else:
        return jsonify({'status': 200})
    
@app.route("/api/users/<user_id>/books/<book_id>/reviews/status", methods=['GET'])
def status_review_android(user_id,book_id):

    review = dao.get_review_in_review_by_user_id_android(book_id,user_id)
    if review:
        return jsonify({'status': 'reviewed'})
    return jsonify({'status': 'active'})


@app.route("/api/orders/<order_id>/status", methods=['GET'])
def get_order_status_android(order_id):
    state = dao.load_state_order_by_id(order_id)
    print('state',state)
    order_id = int(order_id)
    if state == 'CONFIRM':
        return jsonify({'status': 'confirmed'})
    if state == 'CANCEL':
        return jsonify({'status': 'cancelled'})
    return jsonify({'status': 'active'})
# @app.route("/em/cart")
# def load_employee_cart():
#     return render_template('admin/cart.html')
@app.route("/api/orders/<order_id>/update_state_cancel",methods=['GET'])
def update_state_order_android(order_id):
    dao.update_status_cancle_order_android(int(order_id))
    return jsonify({'status': 'success'})

@app.route("/em/login", methods=['POST'])
def process_em_login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = dao.auth_user(username=username, password=password)
    if user and UserRole.EMPLOYEE.__eq__(user.user_role):
        login_user(user)
        next = request.args.get('next')
        print(next)
        if next:
            return redirect(next)
    
    return redirect('/em')


@app.route("/em/logout")
def process_em_logout():
    logout_user()
    return redirect('/em/index')

@app.route("/bookcontents/")
def load_bookcontent():
    book_contents={}
    if current_user.is_authenticated:
        book_contents = dao.get_book_content_with_receipt_with_user(current_user)
        return jsonify(book_contents),200
    else:
        return jsonify(book_contents),302
    


    
scheduler = BackgroundScheduler()
scheduler.add_job(Order.update_order_status, 'interval', hours=1)
scheduler.start()
if __name__ == '__main__':
    # ngrok start --config "C:\Users\MINH\AppData\Local\ngrok\ngrok2.yml" tunnel2
    app.run(debug=True)