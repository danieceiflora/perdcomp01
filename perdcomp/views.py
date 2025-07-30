from django.shortcuts import render

def token_jwt_view(request):
    return render(request, 'token_jwt.html')
