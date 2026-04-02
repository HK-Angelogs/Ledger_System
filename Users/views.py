from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout

# Create your views here.


def login_view(request):
    if request.method == 'POST':
        # Grab data from the 'name' attributes in the HTML
        un = request.POST.get('username')
        pw = request.POST.get('password')

        # Django checks the password hash and the role in db.sqlite3
        user = authenticate(request, username=un, password=pw)

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to your main page
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'Login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')  # Redirect back to your login page
