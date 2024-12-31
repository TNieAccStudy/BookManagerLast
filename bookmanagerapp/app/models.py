from config import app, db
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum, SmallInteger, UniqueConstraint
from sqlalchemy_utils import EmailType
from flask_login import UserMixin
from enum import Enum as RoleEnum
from flask_login import current_user
from datetime import datetime as dt
from sqlalchemy import text
from datetime import datetime, timedelta
import hashlib
import humanize
import locale


class UserRole(RoleEnum):
    ADMIN = 1
    USER = 2
    EMPLOYEE = 3
    STORAGEMANAGER = 4

    
class MethodRecevie(RoleEnum):
    AITHECOUNTER = 1
    DELIVERY = 2


class MethodBank(RoleEnum):
    MOMO = 1
    BANKWHENGET = 2


class CancelReasonState(RoleEnum):
    PENDINGCANCEL = 0
    CLIENTREQUIRED = 1
    CLIENTNOTRECEIVE = 2
    SHOPREASON = 3
    DELIVERYREASON = 4


class StateOrder(RoleEnum):
    PENDINGCONFIRM = 0
    PENDINGPAYMENT = 1
    PENDINGPROCESSING = 2
    DELIVERING = 3
    CONFIRM = 4
    CANCEL = 5


class CategoryBook(db.Model):
    __tablename__ = 'category_book'
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('categories.id',ondelete='CASCADE'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id',ondelete='CASCADE'), nullable=False)

    def __str__(self):
        return str(self.id)

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.now())
    updated_at = Column(DateTime, default=dt.now(), onupdate=dt.now())

class Client(db.Model, UserMixin):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    active = Column(Boolean, default=True)
    username = Column(String(128), unique=True, nullable=False)
    email = Column(EmailType, unique=True, nullable=True)
    password = Column(String(512), nullable=False)
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    info_user_order = relationship('InfoUserOrder', back_populates="client", uselist=False, cascade="all, delete-orphan")
    reviews = relationship('Review', backref='client', lazy=True)
    taked_book = relationship("TakedBook", back_populates='client', uselist=False, cascade="all, delete-orphan")
    receipts = relationship('Receipt', backref='client',lazy=True)


    def __str__(self):
        return self.name
    def to_dict(self):
            return {
                'id': self.id,
                'fullname': self.name,
                'username': self.username,
                'email': self.email,
            }




class Category(BaseModel):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False,unique=True)
    books = relationship('Book', secondary='category_book', back_populates='categories')

    def __str__(self):
        return self.name
    def to_dict(self):
            return {
                'id': self.id,
                'name': self.name
            }
class Book(BaseModel):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False,unique=True)
    author = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    prices = relationship('Price', backref='book', lazy=True)
    image = Column(String(100), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)    
    categories = relationship(Category, secondary='category_book', back_populates='books')
    order_details = relationship('OrderDetail', backref='book', lazy=True)
    receipt_details = relationship('ReceiptDetail',backref='book',lazy=True)
    taked_book_details = relationship('TakedBookDetail', backref='book', lazy=True)
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'description': self.description,
            'image': self.image,
            'quantity': self.quantity,
            'categories': [category.name for category in self.categories],
            'prices': [{'name_price': price.name_price, 'price': price.price} for price in self.prices]
        }
    def __str__(self):
        return self.title

class Price(db.Model):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_price = Column(String(100), nullable=False)
    price = Column(Float, default=0, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('name_price', 'book_id', name='uq_name_book'),
    )
    
    def __str__(self):
        return self.name_price


class TakedBook(BaseModel):
    __tablename__ = 'taked_books'
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, unique=True)
    details = relationship('TakedBookDetail', backref='taked_book', lazy=True, cascade="all, delete-orphan")

    client = relationship("Client", back_populates="taked_book")

    def __str__(self):
        return str(self.id)


class TakedBookDetail(db.Model):
    __tablename__ = 'taked_book_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    taked_book_id = Column(Integer, ForeignKey(TakedBook.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    price = Column(Float, default=0, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    def __str__(self):
        return str(self.id)
    

class InfoUserOrder(BaseModel):
    __tablename__ = 'info_user_order'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(100), nullable=False,unique=True)
    address = Column(String(255), nullable=False)
    email = Column(EmailType, nullable=False)
    user_id = Column(Integer, ForeignKey(Client.id), nullable=True)
    orders = relationship('Order', backref='client', lazy=True)

    client = relationship('Client',back_populates='info_user_order')

    def __str__(self):
        return self.name
    

class Coupon(BaseModel):
    __tablename__ = 'coupons'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), nullable=False, unique=True)
    discount = Column(Float, nullable=False)

    def __str__(self):
        return self.code


class Order(BaseModel):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    info_user_order_id = Column(Integer, ForeignKey(InfoUserOrder.id), nullable=False)
    details = relationship('OrderDetail', backref='order', lazy=True, cascade="all, delete-orphan")
    methodReceive = Column(Enum(MethodRecevie), default=MethodRecevie.AITHECOUNTER)
    methodBank = Column(Enum(MethodBank), default=MethodBank.MOMO)
    coupon_id  = Column(Integer, ForeignKey(Coupon.id), nullable=True)
    delivery_address = Column(String(255), nullable=False)
    state =  Column(Enum(StateOrder), default=StateOrder.PENDINGPAYMENT)
    cancel_order = relationship("CancelOrder", back_populates="order", uselist=False, cascade="all, delete-orphan")
    
    def __str__(self):
        return str(self.id)
    
    @staticmethod
    def update_order_status():
        with app.app_context():
            now = datetime.now()
            cancel_time_regulation = Regulation.query.filter_by(name='cancelled_order_total_hour').first()
            time_limit = cancel_time_regulation.value
            cutoff_time = now - timedelta(hours=time_limit)
            orders_to_update = Order.query.filter(Order.state != StateOrder.CONFIRM, Order.created_at <= cutoff_time).all()
            for order in orders_to_update:
                order.state = StateOrder.CANCEL
                db.session.commit()


class OrderDetail(BaseModel):# db.Model
    __tablename__ = 'order_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    price = Column(Float, default=0, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint('order_id', 'book_id', name='uq_order_book'),
    )

    def __str__(self):
        return str(self.id)
    

#chap nhan receipt doc lap order
class Receipt(BaseModel):
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey(Client.id), nullable=True)
    receipt_details = relationship('ReceiptDetail', backref='receipt', lazy=True)


class ReceiptDetail(BaseModel):
    id = Column(Integer, primary_key=True, autoincrement=True)
    quantity = Column(Integer, default=0)
    price = Column(Float, default=0)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)

    __table_args__ = (
        UniqueConstraint('receipt_id', 'book_id', name='uq_receipt_book'),
    )

    def __str__(self):
        price = f'{self.price:,}'
        return f'id:{self.id}-quantity:{self.quantity}-price:{price} '
    
    

class Review(BaseModel):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey(Client.id), nullable=False)
    content = Column(String(255), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    rate = Column(SmallInteger, default=5)

    __table_args__ = (
        UniqueConstraint('client_id', 'book_id', name='uq_client_book'),
    )

    def __str__(self):
        return self.content
    
    def to_dict(self):
        now = datetime.now()
        created_at_relative = humanize.naturaltime(now - self.created_at)
        translations = {
            "a second": "1 giây",
            "a minute": "1 phút",
            "an hour": "1 giờ",
            "a day": "1 ngày",
            "a month": "1 tháng",
            "a year": "1 năm",
            " ago": " trước",
            " seconds": " giây",
            " second": " giây",
            " minutes": " phút",
            " minute": " phút",
            " hours": " giờ",
            " hour": " giờ",
            " days": " ngày",
            " day": " ngày",
            " months": " tháng",
            " month": " tháng",
            " years": " năm",
            " year": " năm",
 
        }
        
        for eng, viet in translations.items():
            created_at_relative = created_at_relative.replace(eng, viet)
        return {
            'id': self.id,
            'name': self.client.name,
            'content': self.content,
            'created_at': created_at_relative,
        }
class CancelOrder(BaseModel):
    __tablename__ = 'cancel_orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False)
    reason = Column(String(255), nullable=False,default='Order get validate time')
    reason_state = Column(Enum(CancelReasonState), nullable=False)

    order = relationship("Order", back_populates="cancel_order")

    def __str__(self):
        return self.reason
    

class Regulation(BaseModel):
    __tablename__ = 'regulations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50),nullable=False , unique=True)
    value = Column(Integer,nullable=False)

class BookContent(Book):
    url_content = Column(String(255),default="https://globalforgivenessinitiative.com/user/pages/download/Four-Steps-to-Forgiveness-William-Fergus-Martin.pdf")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # with db.engine.connect() as connection:
        #     connection.execute(text('DROP TABLE IF EXISTS taked_book_details'))
        # db.session.commit()
        # info_user_order = InfoUserOrder(name='user3', phone='user3', address='use3',email="user3@gmail.com")
        # db.session.add(info_user_order)
        # db.session.commit()
        # order = Order(info_user_order_id=info_user_order.id, delivery_address='user3')
        # db.session.add(order)
        # db.session.commit()

        u = Client(name='user', username='user', email='user2k4@gmail.com',password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), user_role=UserRole.USER)
        db.session.add(u)
        ad = Client(name='admin', username='admin', email='user224@gmail.com',password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), user_role=UserRole.ADMIN)
        db.session.add(ad)
        em = Client(name='employee', username='em', email='user224@gmail.com',password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), user_role=UserRole.EMPLOYEE)
        db.session.add(em)
        sm = Client(name='storage manager', username='sm', email='user224@gmail.com',password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), user_role=UserRole.STORAGEMANAGER)
        db.session.add(sm)
        # programming = get_or_create_category('Programming')
        # python = get_or_create_category('Python')
        # java_cat = get_or_create_category('Java')

        # co = CancelOrder(order_id=1,reason='don know',reason_state = CancelReasonState.PENDINGCANCEL)
        # db.session.add(co)
        # o = Order(info_user_order_id=1,methodReceive=MethodRecevie.AITHECOUNTER,methodBank=MethodBank.BANKWHENGET,
        #           delivery_address="xin chao test", state=StateOrder.CANCEL)
        # db.session.add(o)
        r1 = Regulation(name='import_book_amount',value=150)
        r2 = Regulation(name='cancelled_order_total_hour',value=48)
        db.session.add(r1)
        db.session.add(r2)
        db.session.commit()
        
        # review1 = Review(client_id=1,content='hello',book_id=2,rate=3)
        # client_id = Column(Integer, ForeignKey(Client.id), nullable=False)
        # content = Column(String(255), nullable=False)
        # book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
        # rate = Column(SmallInteger, default=5)

        # db.session.add(book)
        # db.session.add(java)
        # db.session.commit()