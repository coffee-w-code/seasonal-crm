from django.urls import path

from . import views


urlpatterns = [
    path(
        "create/",
        views.create_order_view,
        name="create_order",
    ),

    path(
        "",
        views.order_list_view,
        name="order_list",
    ),

    path(
        "<int:order_id>/",
        views.order_detail_view,
        name="order_detail",
    ),
]