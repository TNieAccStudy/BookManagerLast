from flask import redirect, url_for, render_template_string, request, session
from markupsafe import Markup
from flask_admin import Admin,BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from sqlalchemy import func
from config import app, db
from flask_admin.actions import action
from models import Order, CancelOrder, Book, InfoUserOrder, CancelReasonState,OrderDetail, Receipt, ReceiptDetail, Client, StateOrder, UserRole, Price
from flask_login import current_user
import dao



class EmployeeAdminIndexView(BaseView):
    @expose('/')
    def index(self):
        return self.render('employee/index.html')

def check_authenticated_employee_site(current_user):
    return current_user.is_authenticated\
          and (
              UserRole.EMPLOYEE.name.__eq__(current_user.user_role.name)\
          or UserRole.STORAGEMANAGER.name.__eq__(current_user.user_role.name)\
              or UserRole.ADMIN.name.__eq__(current_user.user_role.name)
          )


em_admin = Admin(app,'Employee Site',template_mode='bootstrap4', url='/em', endpoint='em',
                 base_template='employee/em_base.html')

# print(app.blueprints)

class EmployeeAuthenticatedView(BaseView):

    def is_accessible(self):
        return check_authenticated_employee_site(current_user)
    pass

class EmployeeAuthenticatedModelView(ModelView):
    column_searchable_list = ['id']
    # edit_modal=True
    can_delete=False
    can_create=False
    can_edit=True


    page_size=10
    def is_accessible(self):
        return check_authenticated_employee_site(current_user)
    pass
    


class OrderAttachedUserModelView(EmployeeAuthenticatedModelView):
    column_list=['id','user_name','phone','delivery_adress','email',
                 'method_bank','method_receive','state',
                 'confirm','cancel']
    list_template='employee/can_modals_list.html'
    column_searchable_list=['id']
    
    column_formatters = {
        'confirm': lambda v, c, m, p: Markup(f'<a onclick="confirmOrder({m.id},this)" data-type="confirm" class="btn my_custom_button"><i class="uil uil-check-circle"></i></a>'),
        'cancel': lambda v, c, m, p: Markup(f'<a onclick="confirmOrder({m.id},this)" data-type="cancel" class="btn my_custom_button"><i class="uil uil-times-circle"></i></a>'),    
    }
    
    def get_query(self):
        return db.session.query(Order.id,
                                Order.state,
                                InfoUserOrder.name.label('user_name'), 
                                InfoUserOrder.phone.label('phone'), 
                                Order.delivery_address.label('delivery_adress'), 
                                Order.methodReceive,
                                InfoUserOrder.email.label('email'), 
                                Order.methodBank.label('method_bank'),
                                Order.methodReceive.label('method_receive'),
                                Order.state)\
                                .join(InfoUserOrder,InfoUserOrder.id==Order.info_user_order_id)\
                                .filter(Order.state==StateOrder.PENDINGCONFIRM)
    


class CancelPendingOrderModelView(EmployeeAuthenticatedModelView):
    column_list=['id','order_id','reason','reason_state',
                 'order_state','phone','name','email',
                 'method_bank','method_receive','cancel']
    column_details_list=['id','order_id','reason','reason_state',
                 'order_state','phone','name','email',
                 'method_bank','method_receive','detail_quantity']
    list_template='employee/em_list.html'

    column_formatters = {
        'cancel': lambda v, c, m, p: Markup(f'<a onclick="confirmPendingCancel({m.id})" class="btn btn-primary btn-sm">X</a>')
    }
    # <a onclick="confirmPendingCancel({{ cancel_order_id }})" class="btn btn-primary btn-sm">X</a>
    # column_formatters = {
    #     'test': lambda v, c, m, p: Markup(f'<a href="/user_action/{m.id}" class="btn btn-primary btn-sm">Action</a>')
    # }

    def get_query(self):
        return db.session.query(CancelOrder.id,
                                Order.id.label('order_id'),
                                CancelOrder.reason,
                                CancelOrder.reason_state,
                                InfoUserOrder.phone.label('phone'),
                                InfoUserOrder.name.label('name'),
                                InfoUserOrder.email.label('email'),
                                Order.state.label('order_state'),
                                Order.methodBank.label('method_bank'),
                                Order.methodReceive.label('method_receive'),
                                # func.sum(Order.state)
                                )\
                                .join(Order, CancelOrder.order_id==Order.id)\
                                .join(InfoUserOrder,Order.info_user_order_id==InfoUserOrder.id)\
                                .filter(CancelOrder.reason_state==CancelReasonState.PENDINGCANCEL and 
                                        Order.state!=StateOrder.CANCEL)
    
                                
    # db.session.query(CancelOrder)
        #not execute show details
    

class CancelOrderModelView(EmployeeAuthenticatedModelView):
    column_list = ['id','order_id','reason','reason_state']
    column_editable_list = ['reason_state']

    def get_query(self):
        return db.session.query(CancelOrder)\
            .join(Order,Order.id==CancelOrder.order_id)\
            .filter(Order.state!=StateOrder.CANCEL)


# class UserModelView(EmployeeAuthenticatedView):
#     column_list=['id','name','username','email','user_role']
#     column_editable_list=['user_role']
#     can_create=False
#     column_filters = ['id','name']
#     column_searchable_list = ['name','id']
#     # list_template = 'employee/test_list.html'

#     # column_formatters = {
#     #     'test': lambda v, c, m, p: render_template_string(
#     #         '<a href="{{ url_for("user_action", user_id=m.id) }}" class="btn btn-primary btn-sm">Action</a>',
#     #         m=m  # Truyền đối tượng m vào template
#     #     )
#     # }
    

#     # Định nghĩa hành động
#     @action('custom_action', 'Custom Action', 'Are you sure?')
#     def custom_action(self, ids):
#         for user_id in ids:
#             print(f"Custom action for user ID: {user_id}")
#         # Thực hiện hành động nào đó




# class ReceiptTempGetCreateModelView(EmployeeAuthenticatedView):
#     column_list = ['id','client_id','receipts_detail','is_pay']
#     can_create = True
#     # create_modal=True
#     # column_select_related_list = ['client_id']
#     # list_template='employee/test_list.html'
#     # create_template='employee/em_create.html'


class ReceiptModelView(EmployeeAuthenticatedModelView):
    column_list = ['id','client_id','receipt_details']
    # create_modal=True

    #issue now: detail custom, and how to custom for field & button for bar

# class ReceiptDetailModelView(EmployeeAuthenticatedView):
#     column_list = ['id','quantity','price','receipt_id','book_id']


class CartView(EmployeeAuthenticatedView):
    @expose('/')
    def index(self):
        if request.args.get('resultCode') == '0':
            result = dao.add_receipt(details=session['cart'].values())
            if result:
                print('add reciept -- delete cart')
                if session['cart']:
                    dao.delete_book_selected_in_taked_book_detail(session['cart'])
                session['cart'] = {}
        return self.render('admin/cart.html')
    
    def is_visible(self):
        return False
    

class PriceModelView(EmployeeAuthenticatedModelView):
    column_list=['id','name_price','price']
    

class IndexView(BaseView):
    @expose('/')
    def index(self):
        return self.render('employee/index.html')
    
    def is_visible(self):
        return False
    
class DeliveryOrder(EmployeeAuthenticatedModelView):
    column_list = ['id','state', 'cancel_state','delivery']
    list_template = 'employee/em_list.html'

    column_formatters = {
        'delivery': lambda v, c, m, p: Markup(f'<a onclick="confirmOrder({m.id},this)" data-type="delivery" class="btn my_custom_button"><i class="uil uil-check-circle"></i></a>'),  
    }

    def get_query(self):
        return db.session.query(Order.id,
                                Order.state,
                                CancelOrder.reason_state.label('cancel_state'))\
                                .join(CancelOrder,CancelOrder.order_id==Order.id,isouter=True)\
                                .filter(Order.state==StateOrder.PENDINGPROCESSING)
            # .filter(CancelOrder.order_id!=Order.id)

class ShopCancelOrderModelView(EmployeeAuthenticatedModelView):
    column_list = ['id','state', 'cancel_state','shop_cancel']

    column_formatters = {
        'shop_cancel': lambda v, c, m, p: Markup(f'<a onclick="confirmOrder({m.id},this)" data-type="shopcancel" class="btn my_custom_button"><i class="uil uil-check-circle"></i></a>'),  
    }

    def get_query(self):
        return db.session.query(Order.id,
                                Order.state,
                                CancelOrder.reason_state.label('cancel_state'))\
                                .join(CancelOrder,CancelOrder.order_id==Order.id,isouter=True)\
                                .filter(CancelOrder.id.is_(None))


em_admin.add_view(OrderAttachedUserModelView(Order,db.session,name="Đơn hàng chờ xác nhận",endpoint='em_orders'))
em_admin.add_view(CancelPendingOrderModelView(CancelOrder,db.session,name='Đơn chờ hủy',endpoint='em_pending_cancels'))
em_admin.add_view(ShopCancelOrderModelView(Order,db.session,name="Don hang muon huy",endpoint='em_shop_cancel_order'))
em_admin.add_view(CancelOrderModelView(CancelOrder,db.session,name='Đơn hủy',endpoint='em_cancels'))

em_admin.add_view(DeliveryOrder(Order,db.session,name="Don hang van chuyen",endpoint='em_delivery_orders'))
em_admin.add_view(ReceiptModelView(Receipt,db.session,name='Hóa đơn', endpoint='em_receipts_display'))

em_admin.add_view(CartView(name='Tạo hóa đơn bán hàng',endpoint='cart'))
em_admin.add_view(IndexView(name='test',endpoint='index'))
# em_admin.add_view(UserModelView(Client,db.session,endpoint='em_users'))
# em_admin.add_view(PriceModelView(Price,db.session,endpoint='em_prices'))
# em_admin.add_view(ReceiptDetailModelView(ReceiptDetail,db.session,endpoint='em_receipt_detail'))
# em_admin.add_view(ReceiptTempGetCreateModelView(Receipt,db.session,endpoint='em_receipts'))

