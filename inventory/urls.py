from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('add-product/', views.add_product, name='add_product'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('stock/', views.stock_history, name = 'stock'),
    path('stock/', views.stock_form, name='stock'),
    path('stock/update/', views.stock_update, name='stock_update'),
    path('stock/history/', views.stock_history_report, name='stock_history_report'),
    path(    'stock/history/export/', views.export_stock_history_excel,name='export_stock_history_excel'),
    # path("stock/history/monthly/export/",views.export_monthly_stock_summary_excel,name="export_monthly_stock_summary_excel")





]
