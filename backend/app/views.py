import json

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
def login_view(request):
    credentials = json.loads(request.body)
    username = credentials.get('username')
    password = credentials.get('password')

    if not username or not password:
        return JsonResponse({'detail': 'provide username and password'}, status=400)

    user = authenticate(username=username, password=password)
    if not user:
        return JsonResponse({'detail': 'invalid credentials'}, status=400)

    login(request, user)
    return JsonResponse({'user': {'id': user.pk, 'username': user.username}})

@require_POST
def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'must be authenticated'}, status=403)

    logout(request)
    return JsonResponse({})