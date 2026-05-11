from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

@ensure_csrf_cookie
def home(request):
    return render(request, 'hladanie_spojeni.html', {})

@ensure_csrf_cookie
def hladanie_spojeni(request):
    return render(request, 'hladanie_spojeni.html', {})

@login_required(login_url='prihlasenie')
def nahravanie_udajov(request):
    return render(request, 'nahravanie_udajov.html', {})

def zisti_adresu(request):
    return render(request, 'zisti_adresu.html', {})

@ensure_csrf_cookie
def prihlasenie(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('nahravanie_udajov')
    else:
        form = AuthenticationForm()
    
    return render(request, 'prihlasenie.html', {'form': form})