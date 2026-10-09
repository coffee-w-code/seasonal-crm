from django.urls import path
from . import views


urlpatterns = [
    path(
        "test-assistant/",
        views.test_voice_assistant,
        name="test_assistant",
    ),

    path(
        "stock/",
        views.inventory_list_view,
        name="inventory_list",
    ),

    path(
        "movements/",
        views.movement_history_view,
        name="movement_history",
    ),

    path(
        "audit-check/",
        views.audit_check_view,
        name="audit_check",
    ),

    path(
        "audit-commit/",
        views.audit_commit_view,
        name="audit_commit",
    ),

    path(
        "move/",
        views.stock_move_view,
        name="stock_move",
    ),
]