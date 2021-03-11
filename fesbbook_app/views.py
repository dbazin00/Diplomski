from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .forms import StudentForm, LoginForm
from .models import Student

# Create your views here.

loggedInNavbar = [{"text": "Početna", "path": "/"}, {"text": "Kontakt", "path": "contact"}]
loggedOutNavbar = [{"text": "Početna", "path": "/"}, {"text": "Kontakt", "path": "contact"}, {"text": "Registracija", "path": "registration"}]

def index(request):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "/"}
    return render(request, "fesbbook_app/index.html", context)

def contact(request):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo": pathInfo, "active": "contact"}
    return render(request, "fesbbook_app/contact.html", context)

def login(request):
    
    if request.session.get("loggedInUser") != None:
        return redirect("/")
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        isAuthorised = authoriseStudent(request, form)
        if isAuthorised:
            return redirect("/")
        else:
            context = {"pathinfo" : loggedOutNavbar, "form" : form}
            return render(request, "fesbbook_app/login.html", context)
    else:
        form = LoginForm()
        context = {"pathinfo" : loggedOutNavbar, "form" : form}
        return render(request, "fesbbook_app/login.html", context)

def authoriseStudent(request, form):

    if form.is_valid():
        request.session["loggedInUser"] = request.POST.get("username")
        loggedInUser = Student.objects.get(username=request.session.get("loggedInUser"))
        loggedInUser.isActive = True
        loggedInUser.save()
        return True
        
    return False

def logout(request):
    del request.session["loggedInUser"]
    return redirect("/")

def registration(request):
    if request.session.get("loggedInUser") != None:
        return redirect("/")
    
    if request.method == "POST":
        newStudent = StudentForm(request.POST, request.FILES)
        newStudentValid = createStudent(request, newStudent)
        if newStudentValid:
            return redirect("/")
        else:
            context = {"pathinfo" : loggedOutNavbar, "active": "registration", "form": newStudent}
            return render(request, "fesbbook_app/registration.html", context)
    else:
        form = StudentForm()
        context = {"pathinfo" : loggedOutNavbar, "active": "registration", "form": form}
        return render(request, "fesbbook_app/registration.html", context)

def createStudent(request, newStudent):
    
    
    profile_image = request.FILES["profile_image"] if "profile_image" in request.FILES else False

    if profile_image:
        newStudent.profile_image = profile_image

        fs = FileSystemStorage("media/profile_images")
        name = fs.save(username + "_profile_image." + profile_image.name.rsplit("/", 1)[0], profile_image)
        
    if newStudent.is_valid():
        form = newStudent.save(commit=False)
        form.isActive = False
        form.save()
        return True
        context = {"pathinfo" : loggedOutNavbar, "active": "registration","form": newStudent}
    return False

def navbarPathInfo(request):
    if request.session.get("loggedInUser") == None:
        return loggedOutNavbar
    else:
        return loggedInNavbar
