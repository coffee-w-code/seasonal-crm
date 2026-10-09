from django.urls import path

from .views import (
    customer_create_view,
    customer_delete_view,
    customer_detail_view,
    customer_list_view,
    customer_update_view,
)


urlpatterns = [
    path(
        "",
        customer_list_view,
        name="customer-list",
    ),
    path(
        "create/",
        customer_create_view,
        name="customer-create",
    ),
    path(
        "<int:customer_id>/",
        customer_detail_view,
        name="customer-detail",
    ),
    path(
        "<int:customer_id>/update/",
        customer_update_view,
        name="customer-update",
    ),
    path(
        "<int:customer_id>/delete/",
        customer_delete_view,
        name="customer-delete",
    ),
]