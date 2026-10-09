import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
def login_view(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_JSON",
                "message": "Invalid JSON request body.",
            },
            status=400,
        )

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse(
            {
                "status": "error",
                "code": "MISSING_CREDENTIALS",
                "message": "Username and password are required.",
            },
            status=400,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid username or password.",
            },
            status=401,
        )

    login(request, user)

    return JsonResponse(
        {
            "status": "success",
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "username": user.username,
            },
        }
    )


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)

    return JsonResponse(
        {
            "status": "success",
            "message": "Logout successful.",
        }
    )


@require_http_methods(["GET"])
def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "code": "NOT_AUTHENTICATED",
                "message": "User is not authenticated.",
            },
            status=401,
        )

    return JsonResponse(
        {
            "status": "success",
            "user": {
                "id": request.user.id,
                "username": request.user.username,
            },
        }
    )