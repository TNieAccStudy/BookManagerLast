import json

import requests
from models import BookContent, CategoryBook,TakedBook,TakedBookDetail,Category, Book,Client,Order,InfoUserOrder,OrderDetail,Price,Review,CategoryBook,CancelOrder,Receipt,ReceiptDetail, CancelReasonState, MethodBank, Regulation, StateOrder
from config import login,db,app
import hashlib
from flask_login import current_user
import cloudinary
from enum import Enum as RoleEnum
from sqlalchemy import func
from datetime import datetime
import services

def load_user_by_id(user_id):
    return Client.query.get(user_id)

def load_info_user_order_by_user_id(user_id):
    return InfoUserOrder.query.filter(InfoUserOrder.user_id == user_id).first()

def get_order_ids_in_cancle_order():
    cancle_order = CancelOrder.query.all()
    order_ids=[item.order_id for item in cancle_order]
    return order_ids

def update_status_payed_order(order_id):
    order = Order.query.get(order_id)
    order.state = StateOrder.CONFIRM.name
    db.session.commit()
def update_status_cancle_order_android(order_id):
    order = Order.query.get(order_id)
    order.state = StateOrder.CANCEL.name
    db.session.commit()

def load_taked_book_detail_by_book_id(book_id):
    return Book.query.filter(Book.id == book_id).first()

def add_taked_book_android(book_id,user_id):
        price_book =Book.query.filter(Book.id == book_id).first().prices[0].price
        taked_book = db.session.query(TakedBook).filter_by(client_id=user_id).first()
        if not taked_book:
            taked_book = TakedBook(client_id=user_id)
            db.session.add(taked_book)
            db.session.commit()
        taked_book_detail = db.session.query(TakedBookDetail).filter_by(taked_book_id=taked_book.id, book_id=book_id).first()
        print(taked_book_detail)
        if taked_book_detail:
            taked_book_detail.quantity += 1
        else:
            taked_book_detail = TakedBookDetail(taked_book_id=taked_book.id, book_id=book_id, quantity=1,price=price_book)
            db.session.add(taked_book_detail)
        
        try:
            db.session.commit()
        except Exception as ex:
            print(ex)
            return False
        else:
            return True
        
def load_order_by_id_android(order_id):
    result = db.session.query(
        OrderDetail.id,
        Book.title,
        Book.image, 
        OrderDetail.quantity,
        Price.price.label('price'),
    ).join(Book, OrderDetail.book_id == Book.id) \
     .join(Price, Book.prices).filter(Price.name_price.__eq__('Giá Gốc')) \
     .filter(OrderDetail.order_id == order_id).all()
    print(result)
    order_details = [{'id': item.id, 'title': item.title,'image':item.image, 'quantity': item.quantity, 'price': float(item.price)} for item in result]
    
    return order_details
def delete_taked_book_detail_by_book_id(book_id,user_id):
    taked_book = TakedBook.query.filter_by(client_id=user_id).first()
    if not taked_book:
        return False
    taked_book_detail = TakedBookDetail.query.filter_by(taked_book_id=taked_book.id, book_id=book_id).first()
    if not taked_book_detail:
        return False
    db.session.delete(taked_book_detail)
    db.session.commit()
    return True

def update_taked_book_quantity(user_id, book_id, new_quantity):
    taked_book = TakedBook.query.filter_by(client_id=user_id).first()
    if not taked_book:
        return False

    taked_book_detail = TakedBookDetail.query.filter_by(taked_book_id=taked_book.id, book_id=book_id).first()
    if not taked_book_detail:
        return False

    taked_book_detail.quantity = new_quantity

    try:
        db.session.commit()
    except Exception as ex:
        print(ex)
        return False
    return True

def add_orders_android(data,address=None,user_id=None):
        address=data.get('address')
        existing_entry = None
        if user_id:
            existing_entry = InfoUserOrder.query.filter_by(user_id=user_id).first()
        else:
            existing_entry = InfoUserOrder.query.filter_by(phone=data.get('phone')).first()
        if existing_entry:
            info_user_order = existing_entry
        else:
            info_user_order = InfoUserOrder(
                name=data.get('name'),
                phone=data.get('phone'),
                address=data.get('address'),
                email=data.get('email'),
                user_id=user_id
            )
            db.session.add(info_user_order)
            db.session.commit()
        order = Order(info_user_order_id=info_user_order.id, delivery_address=address)
        db.session.add(order)
        db.session.commit()
        order_id = order.id
        taked_book = TakedBook.query.filter_by(client_id=user_id).first()
        taked_book_details=TakedBookDetail.query.filter_by(taked_book_id=taked_book.id).all()
        
        for taked_book_detail in taked_book_details:
            print('price',taked_book_detail.price)
            order_detail = OrderDetail(order_id=order_id, book_id=taked_book_detail.book_id, quantity=taked_book_detail.quantity,price = taked_book_detail.price)
            db.session.add(order_detail)
        db.session.commit()
        for taked_book_detail in taked_book_details:
            db.session.delete(taked_book_detail)
        db.session.commit()
        return order_id

def load_categories():
    return Category.query.order_by("id").all()


def load_taked_books_by_user_id(user_id):
    return TakedBook.query.filter_by(client_id=user_id).first()

def load_orders_by_order_id_android(order_id):
    return OrderDetail.query.filter(OrderDetail.order_id == order_id).all()

def load_books(cate_id=None,kw=None,page=1,order='desc'):
    query = Book.query
    if cate_id:
        print(cate_id)
        query = Book.query.filter(Book.categories.any(id=cate_id))
    if kw:
        query = query.filter(Book.title.contains(kw)) 
    
    query = query.join(Price)

    if order == 'asc':
        query = query.filter(Price.name_price=='Giá Giảm').order_by(Price.price)
    elif order == 'desc':
        query = query.filter(Price.name_price=='Giá Giảm').order_by(-Price.price)
    page_size = app.config['PAGE_SIZE']
    start = (page - 1) * page_size
    end = start + page_size
    query = query.slice(start,end)
    return query.all()

def add_review(book_id, content,user_id,rating=5):
    review = Review(book_id=book_id, content=content, rate=rating,client_id =user_id)
    db.session.add(review)
    db.session.commit()
    return review

def get_review_in_review_by_user_id_android(book_id,user_id):
    return Review.query.filter(Review.book_id.__eq__(book_id),Review.client_id.__eq__(user_id)).first()

def get_review_by_book_id(book_id):
    return Review.query.filter(Review.book_id.__eq__(book_id)).order_by(-Review.id)

def get_review_by_book_id_and_user_id(book_id):
    if not current_user.is_authenticated:
        return None
    return Review.query.filter(Review.book_id.__eq__(book_id),Review.client_id.__eq__(current_user.id)).first()

def get_book_ids_in_order_by_user_id():
    book_ids=[]
    if not current_user.is_authenticated:
        return book_ids
    info_user_order_id= get_id_info_user_order(current_user.id)
    if  info_user_order_id :
        order = Order.query.filter(Order.info_user_order_id == info_user_order_id.id,
                                Order.state == StateOrder.CONFIRM.name).all()
        order_ids = [item.id for item in order]
        order_details = OrderDetail.query.filter(OrderDetail.order_id.in_(order_ids)).all()
        print('order',order_details)
        book_ids=[ order_detail.book_id for order_detail in order_details]
    return book_ids
def load_book_by_id(book_id):
    return Book.query.get(book_id)

def count_books():
    return Book.query.count()
def count_books_by_cate_id(cate_id):
    return Book.query.join(CategoryBook).filter(CategoryBook.category_id == cate_id).count()

@login.user_loader
def load_user(user_id):
    return Client.query.get(user_id)

def check_user_exist(username):
    return Client.query.filter(Client.username==username).first()

def check_email_exist(email):
    return Client.query.filter(Client.email==email).first()
def add_user(name, username, password,email, avatar=None):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    u = Client(name=name, username=username, password=password,email=email)
    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')
    db.session.add(u)
    db.session.commit()

def add_cancel_order(order_id, reason,reason_state):
    cancel_order = CancelOrder(order_id=order_id, reason=reason,reason_state = reason_state.name)
    db.session.add(cancel_order)
    db.session.commit()
    return cancel_order


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return Client.query.filter(Client.username.__eq__(username),
                             Client.password.__eq__(password)).first()


def get_or_create_category(name):
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
    return category

def add_book(title, author,image, price,quantity, price_reduced,category_books):
    book = Book.query.filter_by(title=title, author=author).first()
    if book:
        book.quantity += quantity
    else:
        book = Book(
            title=title,
            author=author,
            image=image,
            quantity=quantity,
            prices=[
                Price(name_price='Giá Gốc', price=price),
                Price(name_price='Giá giảm', price=price_reduced)
            ],
            categories=[get_or_create_category(category) for category in category_books]
        )
        db.session.add(book)
    
    db.session.commit()
    return book

def add_orders(data,cart=None,address=None,user_id=None,method_bank=None):
        existing_entry = None
        if user_id:
            existing_entry = InfoUserOrder.query.filter_by(user_id=user_id).first()
        else:
            existing_entry = InfoUserOrder.query.filter_by(phone=data.get('phone')).first()
        
        if existing_entry:
            info_user_order = existing_entry
        else:
            info_user_order = InfoUserOrder(
                name=data.get('name'),
                phone=data.get('phone'),
                address=data.get('address'),
                email=data.get('email'),
                user_id=user_id
            )
            db.session.add(info_user_order)
            db.session.commit()
        state = StateOrder.PENDINGPAYMENT.name if method_bank==MethodBank.MOMO.name else StateOrder.PENDINGCONFIRM.name
        print(state)
        order = Order(info_user_order_id=info_user_order.id, delivery_address=address,methodBank=method_bank,state=state)
        db.session.add(order)
        db.session.commit()
        order_id = order.id
        if cart:
            for v in cart.values():
                print(v)
                order_detail = OrderDetail(order_id=order_id, book_id=v.get('id'), quantity=v.get('quantity'),price = v.get('price'))
                db.session.add(order_detail)
        db.session.commit()
        return order_id

def delete_order(order_id):
    order = Order.query.get(order_id)
    db.session.delete(order)
    db.session.commit()
def count_book_by_cate():
    result = db.session.query(
        Book.id,
        Book.title,
        Price.price.label('original_price'),
    ).join(Book.categories).join(Book.prices).filter(Price.name_price.__eq__('Giá Gốc')).all()
    
    return result

def get_id_info_user_order(user_id):
    return InfoUserOrder.query.filter(InfoUserOrder.user_id == user_id).order_by(InfoUserOrder.id.desc()).first()

def load_order_by_id(order_id):
    result = db.session.query(
        OrderDetail.id,
        Book.title,
        OrderDetail.quantity,
        OrderDetail.price,
        Book.id
    ).join(Book, OrderDetail.book_id == Book.id) \
     .filter(OrderDetail.order_id == order_id).all()
    order_details = [(item.id, item.title, item.quantity, float(item.price),item.id) for item in result]
    total_price = sum(item.price * item.quantity for item in result)
    total_quantity = sum(item.quantity for item in result)
    
    return {
        'order_details': order_details,
        'total_price': total_price,
        'total_quantity': total_quantity
    }

def load_state_order_by_id(order_id):
    order = Order.query.get(order_id)
    return order.state.name
def load_orders(user_id):
    id_info_user_order = None
    result = db.session.query(
            Order.id,
            Order.created_at,
            InfoUserOrder.name.label('name'),
            Order.delivery_address,
            InfoUserOrder.phone.label('phone'),
            Order.methodBank,
            Order.state
        ).join(InfoUserOrder, Order.info_user_order_id == InfoUserOrder.id)
    if user_id:
        id_info_user_order = get_id_info_user_order(user_id)
        print(f'info_user {id_info_user_order}')
        if id_info_user_order:
            result = result.filter(Order.info_user_order_id == id_info_user_order.id)
   
            result = result.all()
            print("result",result)
            status_display = {
                "PENDINGPAYMENT": "Chờ Thanh Toán",
                "PENDINGPROCESSING": "Đã Được Xác Nhận",
                "PENDINGCONFIRM": "Chờ Xác Nhận",
                "DELIVERING": "Đang Giao Hàng",
                "CONFIRM": "Đã Hoàn Thành",
                "CANCEL": "Đã Hủy"
            }
            methodBank_display = {
                "MOMO": "Thanh Toán MoMo",
                "BANKWHENGET": "Thanh Toán Khi Nhận Hàng"
            }
            orders = []
            for order in result:
                print(order.state.name)
                time_obj = order.created_at
                formatted_time = time_obj.strftime("%H:%M:%S,  %d/%m/%Y")
                is_confirm_status = status_display.get(order.state.name, "Không xác định")
                methodBank_status = methodBank_display.get(order.methodBank.name, "Không xác định")
                order_dict = {
                    'id': order.id,
                    'created_at': formatted_time,
                    'name': order.name,
                    'delivery_address': order.delivery_address,
                    'phone': order.phone,
                    'method_bank':methodBank_status,
                    'is_confirm': is_confirm_status
                }
                orders.append(order_dict)
        
            return orders

def get_book_by_id(book_id):
    return Book.query.get(book_id)

def load_cart(cart, book_id=None):
    if book_id:
        book = get_book_by_id(book_id)
        print(f"book info: {book}")
        if book:
            book_id_str = str(book_id)
            if book_id in cart:
                cart[book_id_str]['quantity'] += 1
                print(cart[book_id_str]['quantity'])
            else:
                cart[book_id_str] = {
                    "id": book.id,
                    "title": book.title,
                    "price": book.prices[0].price,
                    "quantity": 1,
                }
    return cart

def add_receipt(details:list, client_id=None):
    receipt = Receipt(client_id=client_id)
    db.session.add(receipt)
    db.session.commit()
    print(details)
    for detail in details:
        receipt_detail = ReceiptDetail(receipt_id=receipt.id, book_id=detail.get('book_id'),
                                        quantity=detail.get('quantity'),
                                          price=detail.get('price'))
        db.session.add(receipt_detail)

    db.session.commit()
    print('success add receipt')
    return receipt


def add_taked_book_by_cart(cart):
    taked_book = TakedBook.query.filter_by(client_id=current_user.id).first()
    if not taked_book:
        taked_book = TakedBook(client_id=current_user.id)
        db.session.add(taked_book)
        db.session.commit()
    taked_book_details = TakedBookDetail.query.filter_by(taked_book_id=taked_book.id).all()
    book_ids = {taked_book_detail.book_id: taked_book_detail for taked_book_detail in taked_book_details}
    print(book_ids)
    for c in cart.values():
        book_id = c.get('id')
        quantity = c.get('quantity')
        price = c.get('price')
        if book_id in book_ids:
            taked_book_detail = book_ids[book_id]
            taked_book_detail.quantity += quantity
        else:
            taked_book_detail = TakedBookDetail(taked_book_id=taked_book.id, book_id=book_id, quantity=quantity,price=price)
            db.session.add(taked_book_detail)
    try:
        db.session.commit()
    except Exception as ex:
        print(ex)
        return False
    else:
        return True
    
def add_taked_book(book_id,price):
    taked_book = TakedBook.query.filter_by(client_id=current_user.id).first()
    if not taked_book:
        taked_book = TakedBook(client_id=current_user.id)
        db.session.add(taked_book)
        db.session.commit()
    taked_book_detail = TakedBookDetail.query.filter_by(taked_book_id=taked_book.id, book_id=book_id).first()
    print('taked',taked_book_detail)
    if taked_book_detail:
        taked_book_detail.quantity += 1
    else:
        taked_book_detail = TakedBookDetail(taked_book_id=taked_book.id, book_id=book_id, quantity=1,price=price)
        db.session.add(taked_book_detail)
    
    try:
        db.session.commit()
    except Exception as ex:
        print(ex)
        return False
    else:
        return True
    
def delete_book_selected_in_taked_book_detail( selected_items):
    taked_book = db.session.query(TakedBook).filter_by(client_id=current_user.id).first()
    for item_id in selected_items.keys():
        db.session.query(TakedBookDetail).filter_by(taked_book_id=taked_book.id, book_id=item_id).delete()
    db.session.commit()


def get_taked_books_by_user_id(user_id):
    cart = {}
    taked_books = load_taked_books_by_user_id(user_id)
    if not taked_books:
        return cart
    details = taked_books.details
    for detail in details:
        book = load_taked_book_detail_by_book_id(detail.book_id)
        if book:
            cart[book.id] = {
                "id": book.id,
                "title": book.title,
                "price": detail.price,
                "image": book.image,
                "quantity": detail.quantity,
                "is_selected": False
            }
    return cart


def test():
    total_book = db.session.query(Order.id,func.sum(OrderDetail.quantity))\
        .join(OrderDetail,OrderDetail.order_id==Order.id)\
        .group_by(Order.id)
    return total_book


def confirm_cancel_order(cancel_order_id ,reason_state = CancelReasonState.PENDINGCANCEL):
    cancel_order = CancelOrder.query.get(cancel_order_id)
    # cancel_order.order.state = StateOrder.CANCEL
    cancel_order.reason_state = reason_state
    cancel_order.order.state = StateOrder.CANCEL.name
    print('setup-data')

    # db.session.commit()
    
    try:
        db.session.commit()
    except Exception as ex:
        print(ex)
        return {
            'status': 301
        }
    else:
        print('change')
        return {
            'status': 201
        }
    
def update_order_with_state(order_id,state,reason=None,cancel_state=None):
    if state:
        order = Order.query.get(order_id)
        order.state = state.name
        
        try:
            db.session.commit()
            print('have confirm_order')
        except Exception as ex:
            print(ex)
            return {
                'status': 401
            }
        else:
            if(state == StateOrder.DELIVERING):
                print("xu ly giao order qua ben van chuyen")

                response = services.add_order_for_delivery(order_id)
                print(response.status_code)
                return response.json()

            if(state == StateOrder.CONFIRM):
                print("xu ly add_receipt")
                client_id = order.client.user_id
                print(client_id)

                details = db.session.query(OrderDetail.quantity,
                                        OrderDetail.price,
                                        OrderDetail.book_id)\
                                        .filter(OrderDetail.order_id==order.id).all()
                
                details =[
                    {
                        'quantity': d[0],
                        'price': d[1],
                        'book_id': d[2],
                    }
                    for d in details
                ]
                add_receipt(details=details,client_id=client_id)

            if(state == StateOrder.CANCEL):
                print("xu ly cancel order")
                add_cancel_order(order_id=order_id,reason=reason,reason_state=cancel_state)

            return {
                'status': 201
            }
    return {
        'status': 402
    }
    

def get_regulation(name):
    return Regulation.query.filter(Regulation.name == name).first()


def revenue_stats_by_time(time='month', year=datetime.now().year, month=None):

    total_books_sold_subquery = db.session.query(
        func.sum(OrderDetail.quantity)
    ).join(Order, Order.id == OrderDetail.order_id) \
     .filter(Order.state == StateOrder.CONFIRM.name) \
     .filter(func.extract('year', Order.created_at) == year)
    
    if month:
        total_books_sold_subquery = total_books_sold_subquery.filter(func.extract('month', Order.created_at) == month)
    
    total_books_sold = total_books_sold_subquery.scalar()

    query = db.session.query(
        func.extract(time, Order.created_at),
        Category.name,
        func.sum(OrderDetail.quantity * OrderDetail.price),
        func.sum(OrderDetail.quantity),
        (func.sum(OrderDetail.quantity)/total_books_sold *100),
    ) \
    .join(OrderDetail, OrderDetail.order_id == Order.id) \
    .join(Book, Book.id == OrderDetail.book_id) \
    .join(CategoryBook, CategoryBook.book_id == Book.id) \
    .join(Category, Category.id == CategoryBook.category_id) \
    .filter(Order.state == StateOrder.CONFIRM.name) \
    .filter(func.extract('year', Order.created_at) == year)\
    .filter(OrderDetail.book_id == Book.id)\
    .group_by(Category.id)

    # query = db.session.query(
    #     func.extract(time, Order.created_at),
    #     Category.name,
    #     func.sum(OrderDetail.quantity*OrderDetail.price), # doanh thu
    #     func.sum(OrderDetail.quantity) #so luot thue
    # ).join(CategoryBook,CategoryBook.category_id==Category.id)\
    # .join(Book,CategoryBook.book_id==Book.id)\
    # .join(OrderDetail,OrderDetail.book_id==Book.id)\
    # .group_by(Category.id)\
    # .filter(Order.state == StateOrder.CONFIRM.name) \
    # .filter(func.extract('year', Order.created_at) == year)\
    # .filter(OrderDetail.book_id == Book.id)

    if month:
        query = query.filter(func.extract('month', Order.created_at) == month)
    
    stats = query.group_by(func.extract(time, Order.created_at), Category.name) \
                 .order_by(func.extract(time, Order.created_at), func.sum(OrderDetail.quantity * OrderDetail.price).desc()).all()
    months_query = db.session.query(func.distinct(func.extract('month', Order.created_at))).all()
    months = sorted([int(month[0]) for month in months_query])
    return stats, months
    # return query

def book_sales_frequency(time='month', year=datetime.now().year, month=None):
    total_books_sold_subquery = db.session.query(
        func.sum(OrderDetail.quantity)
    ).join(Order, Order.id == OrderDetail.order_id) \
     .filter(Order.state == StateOrder.CONFIRM.name) \
     .filter(func.extract('year', Order.created_at) == year)
    
    if month:
        total_books_sold_subquery = total_books_sold_subquery.filter(func.extract('month', Order.created_at) == month)
    
    total_books_sold = total_books_sold_subquery.scalar()

    

    query = db.session.query(
        func.extract(time, Order.created_at),
        Book.title,
        Category.name,
        Book.quantity,
        func.sum(OrderDetail.quantity),
        (func.sum(OrderDetail.quantity)/total_books_sold * 100),
        # (func.count(OrderDetail.id) / total_books_sold * 100)
    ) \
    .join(OrderDetail, OrderDetail.book_id == Book.id) \
    .join(Order, Order.id == OrderDetail.order_id) \
    .join(CategoryBook, CategoryBook.book_id == Book.id) \
    .join(Category, Category.id == CategoryBook.category_id) \
    .filter(Order.state == StateOrder.CONFIRM.name) \
    .filter(func.extract('year', Order.created_at) == year)
    
    if month:
        query = query.filter(func.extract(time, Order.created_at) == month)
    
    stats = query.group_by(
        func.extract(time, Order.created_at),
        Book.id,
        Category.id,
    ).order_by(func.count(OrderDetail.id).desc()).all()
    
    return stats

def get_book_content_with_receipt_with_user(user):
    return BookContent.query\
        .join(ReceiptDetail,ReceiptDetail.book_id==BookContent.id)\
        .join(Receipt,Receipt.id==ReceiptDetail.receipt_id)\
        .join(Client,Receipt.client_id==Client.id)\
        .filter(Client.id==user.id)\
        .group_by(BookContent.id).all()

def test_get_book():
    return BookContent.query.all()


if __name__ == '__main__':
    with app.app_context():
        # print(book_sales_frequency(month =12))
        # print(revenue_stats_by_time())
        books = test_get_book()
        print(books)