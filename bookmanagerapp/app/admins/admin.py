from flask_admin.contrib.sqla import ModelView
from flask import redirect,url_for,request
from flask_admin import expose ,BaseView
from flask_login import current_user
from config import app,db,admin
import dao
from models import BookContent, CancelOrder, Receipt, ReceiptDetail,Review,Category, Book,Price,TakedBookDetail,Order,OrderDetail,Client, Regulation, UserRole
import utils

class AdminAuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and UserRole.ADMIN.name.__eq__(current_user.user_role.name)
    pass

class AdminAuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and UserRole.ADMIN.name.__eq__(current_user.user_role.name)
    pass
    

class StorageMangerAuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and (UserRole.STORAGEMANAGER.name.__eq__(current_user.user_role.name) or UserRole.ADMIN.name.__eq__(current_user.user_role.name))
    

class StorageMangerAuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and (UserRole.STORAGEMANAGER.name.__eq__(current_user.user_role.name) or UserRole.ADMIN.name.__eq__(current_user.user_role.name))
    

class BaseModelView(AdminAuthenticatedModelView):
    # column_display_pk = False
    can_create = True
    can_edit = True
    can_export = True
    can_delete = True
class CategoryModelView(StorageMangerAuthenticatedModelView):
    column_list = ['id', 'name', 'books']
    column_labels = {
        'id': 'ID',
        'name': 'Category Name',
        'books': 'Books'
    }


class BookModelView(StorageMangerAuthenticatedModelView):
    column_list = ['id', 'title', 'author','image', 'description', 'quantity', 'prices', 'categories']
    column_searchable_list = ['title']
    column_filters = ['title', 'prices']
    column_editable_list = ['title', 'prices']
    edit_modal = True

from flask_login import logout_user

class PriceModelView(StorageMangerAuthenticatedModelView):
    column_list = ['id', 'name_price', 'price', 'book_id']
    column_editable_list = ['name_price', 'price']
    form_excluded_columns = ['book_id']
class OrderModelView(BaseModelView):
    column_list = ['id', 'info_user_order_id','created_at','state', 'details']
    column_editable_list=['state','created_at']

class OrderDetailView(BaseModelView):
    column_list = ['id','quantity','client_id','book_id']


class CancelOrderView(BaseModelView):
    column_list = ['id','order_id','reason','reason_state']
    column_editable_list = ['reason','reason_state']

class ReviewView(BaseModelView):
    column_list = ['id','content','book_id','rate']

class TakedBookModelView(BaseModelView):
    column_list = ['id','client_id','taked_book_details']
class TakedBookDetailModelView(BaseModelView):
    column_list = ['id','taked_book_id','book_id','quantity']

class AboutUsView(StorageMangerAuthenticatedView):
    @expose('/')
    def index(self):
        return self.render('admin/about-us.html')
# class CartView(BaseView):
#     @expose('/')
#     def index(self):
#         return self.render('admin/cart.html')


class LogoutView(BaseView): 
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    
class StatsView(AdminAuthenticatedView):
    @expose("/")
    def index(self):
        # kw = request.args.get('kw')
        month = request.args.get('month')
        stats,months = dao.revenue_stats_by_time(month=int(month) if month else None)
        stats_book_sold = dao.book_sales_frequency(month=int(month) if month else None)
        print(months)
        return self.render('admin/stats.html', stats=stats,selected_month=month,months=months,stats_book_sold=stats_book_sold)
    

class UserModelView(AdminAuthenticatedModelView):
    column_list=['id','name','username','email','user_role']
    column_editable_list=['user_role']
    can_create=True


class RegulationModelView(AdminAuthenticatedModelView):
    column_list=['id','name','value','update_at']
    column_editable_list=['value']
    can_create=False
    can_delete=False

class BookContentModelView(AdminAuthenticatedModelView):
    column_list=['id', 'title', 'url_content']
    column_editable_list = ['url_content']

admin.add_view(BookContentModelView(BookContent,db.session))
admin_tag = "Special for Admin"
order_tag = "Order"
summon_tag = "Summon"
class ReceiptModelView(AdminAuthenticatedModelView):
    column_list=['id','client_id','details']


class ReceiptDetailModelView(AdminAuthenticatedModelView):
    column_list=['id','receipt_id','quantity','book_id']

admin.add_view(ReceiptDetailModelView(ReceiptDetail,db.session,category="Receipt"))
admin.add_view(CategoryModelView(Category, db.session))
admin.add_view(BookModelView(Book, db.session))
admin.add_view(UserModelView(Client,db.session))
admin.add_view(OrderModelView(Order, db.session,category=order_tag))
admin.add_view(CancelOrderView(CancelOrder, db.session,category=order_tag))
admin.add_view(OrderDetailView(OrderDetail, db.session,category=order_tag))
admin.add_view(ReviewView(Review, db.session,category=summon_tag))
admin.add_view(PriceModelView(Price, db.session,category=summon_tag))
admin.add_view(ReceiptModelView(Receipt, db.session,category="Receipt"))
admin.add_view(TakedBookDetailModelView(TakedBookDetail, db.session,category=summon_tag))
admin.add_view(AboutUsView(name="Nhập Sách"))
admin.add_view(LogoutView(name="Đăng Xuất"))
admin.add_view(StatsView(name="Báo Cáo",category=admin_tag))
# admin.add_view(CartView(name="Giỏ Hàng"))
admin.add_view(RegulationModelView(Regulation,db.session,category=admin_tag))