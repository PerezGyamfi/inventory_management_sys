from django.http import HttpResponse
from django.shortcuts import render, redirect , get_object_or_404

from .models import Product, Category
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import StockMovement
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from .models import Product, StockHistory
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.admin.views.decorators import staff_member_required
from openpyxl import Workbook
from django.db.models.functions import TruncMonth
import openpyxl
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from django.db import models

from inventory import models












# Create your views here.

@login_required
def dashboard(request):
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(quantity__lte=5)
    return render(request, 'inventory/dashboard.html', {
        'total_products': total_products,
        'low_stock_products': low_stock_products
    })



@permission_required('inventory.view_product', raise_exception=True)
@login_required
def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    search = request.GET.get('search')
    category_id = request.GET.get('category')
    sort = request.GET.get('sort')

    if search:
        products = products.filter(name__icontains=search)

    if category_id:
        products = products.filter(category_id=category_id)

    if sort == 'name':
        products = products.order_by('name')
    elif sort == 'quantity':
        products = products.order_by('quantity')
    elif sort == 'price':
        products = products.order_by('price')

    paginator = Paginator(products, 7)  #  5 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/product_list.html', {
        'page_obj': page_obj,
        'categories': categories
    })


@permission_required('inventory.add_product', raise_exception=True)
@login_required
def add_product(request):
    categories = Category.objects.all()

    if request.method == "POST":
        name = request.POST['name'].strip()
        category_id = request.POST['category']
        quantity = request.POST['quantity']
        price = request.POST['price']

        # 🔍 CHECK if product already exists (case-insensitive)
        exists = Product.objects.filter(
            name__iexact=name,
            category_id=category_id
        ).exists()

        if exists:
            messages.error(
                request,
                "Product already exists in this category."
            )
            return redirect('add_product')

        try:
            Product.objects.create(
                name=name,
                category_id=category_id,
                quantity=quantity,
                price=price
            )
            messages.success(request, "Product added successfully.")
            return redirect('product_list')

        except IntegrityError:
            # Extra safety (DB-level protection)
            messages.error(
                request,
                "Product already exists in this category."
            )
            return redirect('add_product')

    return render(request, 'inventory/product_form.html', {
        'categories': categories
    })



def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')

    return render(request, 'inventory/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def stock_form(request):
    products = Product.objects.all()
    return render(request, 'inventory/stock_form.html', {
        'products': products
    })




@permission_required('inventory.change_product', raise_exception=True)
@login_required
def stock_update(request):
    products = Product.objects.all()

    if request.method == 'POST':
        product_name = request.POST.get('product')
        action = request.POST.get('action')
        quantity = request.POST.get('quantity')

        if not quantity or int(quantity) <= 0:
            messages.error(request, "Quantity must be greater than zero.")
            return render(request, 'inventory/stock_form.html', {'products': products})

        quantity = int(quantity)
        product = get_object_or_404(Product, name__iexact=product_name)

        if action == 'IN':
            product.quantity += quantity
            product.save()

            # ✅ Still log history for admin
            StockHistory.objects.create(
                product=product,
                action=action,
                quantity=quantity,
                user=request.user
            )

            messages.success(request, f"Added {quantity} to {product.name}.")

        elif action == 'OUT':
            if product.quantity >= quantity:
                product.quantity -= quantity
                product.save()

                # ✅ Still log history for admin
                StockHistory.objects.create(
                    product=product,
                    action=action,
                    quantity=quantity,
                    user=request.user
                )

                messages.success(request, f"Removed {quantity} from {product.name}.")
            else:
                messages.error(
                    request,
                    f"Cannot remove {quantity} from {product.name}. Not enough stock."
                )

        # Refresh products after update
        products = Product.objects.all()

    return render(request, 'inventory/stock_form.html', {
        'products': products
    })


@staff_member_required
def stock_history_report(request):
    histories = StockHistory.objects.select_related('product', 'user').order_by('-timestamp')
    products = Product.objects.all()

    # Filters
    product_id = request.GET.get('product')
    action = request.GET.get('action')
    period = request.GET.get('period')  # daily | monthly

    # NEW: specific date filter
    selected_date = request.GET.get('date')

    if selected_date:
        histories = histories.filter(timestamp__date=selected_date)


    if product_id:
        histories = histories.filter(product_id=product_id)

    if action:
        histories = histories.filter(action=action)

    
     # 🔥 DAILY / MONTHLY LOGIC
    today = timezone.now().date()

    if period == 'daily':
        histories = histories.filter(timestamp__date=today)

    elif period == 'monthly':
        histories = histories.filter(
            timestamp__year=today.year,
            timestamp__month=today.month
        )


    context = {
        'histories': histories,
        'products': products,
        'selected_period': period,

    }
    return render(request, 'inventory/stock_history_report.html', context)


@staff_member_required
def export_stock_history_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock History"

    # Header row
    ws.append([
        "Date",
        "Product",
        "Category",
        "Action",
        "Quantity",
        "User"
    ])

    history = StockHistory.objects.select_related(
        'product', 'product__category', 'user'
    ).order_by('-timestamp')

    for record in history:
        ws.append([
            record.timestamp.strftime("%Y-%m-%d %H:%M"),
            record.product.name,
            record.product.category.name,
            record.action,
            record.quantity,
            record.user.username if record.user else "System"
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename=stock_history.xlsx'

    wb.save(response)
    return response


# MONTHLY EXCEL EXPORT

@staff_member_required
def export_monthly_stock_summary_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Monthly Stock Summary"

    # Header row
    ws.append([
        "Month",
        "Product",
        "Total IN",
        "Total OUT",
        "Net Change"
    ])

    # Aggregate data
    summaries = (
        StockHistory.objects
        .annotate(month=TruncMonth("created_at"))
        .values("month", "product__name")
        .annotate(
            total_in=Sum("quantity", filter=models.Q(action="IN")),
            total_out=Sum("quantity", filter=models.Q(action="OUT")),
        )
        .order_by("month", "product__name")
    )

    for s in summaries:
        total_in = s["total_in"] or 0
        total_out = s["total_out"] or 0

        ws.append([
            s["month"].strftime("%Y-%m"),
            s["product__name"],
            total_in,
            total_out,
            total_in - total_out
        ])

    # Response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        'attachment; filename="monthly_stock_summary.xlsx"'
    )

    wb.save(response)
    return response



