from django.shortcuts import render, redirect, reverse
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import StudentForm, LoginForm, PasswordForm
from .models import Student, Study, Message, ChatRoom

# Create your views here.

loggedInNavbar = [{"text": "Početna", "path": "/"}, {"text": "Kolege", "path": "../studentList"}, {"text": "Razgovori", "path": "../conversation"}, {"text": "Kontakt", "path": "../contact"}]
loggedOutNavbar = [{"text": "Početna", "path": "/"}, {"text": "Kontakt", "path": "contact"}, {"text": "Registracija", "path": "registration"}]

def index(request):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "/"}
    return render(request, "fesbbook_app/index.html", context)

def contact(request):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo": pathInfo, "active": "../contact"}
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
    loggedInUser = Student.objects.get(username=request.session.get("loggedInUser"))
    loggedInUser.isActive = False
    loggedInUser.save()
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

    if newStudent.is_valid():
        form = newStudent.save(commit=False)
        form.isActive = False
        
        if profile_image:
            fs = FileSystemStorage(location="media/profile_images")
            newImage = fs.save(newStudent.data["username"] + "_profile_image." + profile_image.name.rsplit(".", 1)[1], profile_image)
            fileurl = "profile_images" + fs.url(newImage)
            form.profile_image = fileurl
        else:
            form.profile_image = "profile_images/default_profile_image.png"      
        form.save()
        return True
    return False

def studentList(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")
    
    loggedInUser = Student.objects.get(username = request.session.get("loggedInUser"))

    fullQuerry = Q()

    if request.GET.get("username") != None:
        fullQuerry = fullQuerry & Q(username__contains=request.GET.get("username"))
    if request.GET.get("study"):
        fullQuerry = fullQuerry & Q(study = loggedInUser.study)
            
    studentList = Student.objects.filter(fullQuerry).exclude(username = loggedInUser.username)

    paginator = Paginator(studentList, 1)
    page = request.GET.get("page")

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items.paginator.page(paginator.num_pages)

    index = items.number - 1
    max_index = len(paginator.page_range)
    start_index = index - 5 if index >= 5 else 0
    end_index = index + 5 if index <= max_index - 5 else max_index
    page_range = paginator.page_range[start_index:end_index]

    print(request.get_full_path())
    baseURL = request.get_full_path()

    if "page" in request.get_full_path():
        baseURL = request.get_full_path().split("page")[0]
    if baseURL == "/studentList":
        baseURL += "?"
    elif not baseURL.endswith("&"):
        baseURL += "&"
    
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "../studentList", "studentList": studentList, "items": items, "page_range": page_range, "baseURL": baseURL}
    return render(request, "fesbbook_app/studentList.html", context)

def studentInfo(request, username):
    if request.session.get("loggedInUser") == None:
        return redirect("/")

    if username == request.session.get("loggedInUser"):
        return redirect("myProfile")

    studentInfo = Student.objects.get(username = username)
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "../studentList", "studentInfo": studentInfo}
    return render(request, "fesbbook_app/studentInfo.html", context)    

def myProfile(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")

    myInfo = Student.objects.get(username = request.session.get("loggedInUser"))
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "../myProfile", "studentInfo": myInfo}
    return render(request, "fesbbook_app/myProfile.html", context)

def editProfile(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/") 
    
    if request.method == "POST":
        myForm = StudentForm(request.POST, request.FILES)
        profile_image = request.FILES["profile_image"] if "profile_image" in request.FILES else False
        myInfo = Student.objects.get(username=request.session.get("loggedInUser"))
        if profile_image:
            if myInfo.profile_image.name.rsplit("/", 1)[1] != "default_profile_image.png":
                fs = FileSystemStorage(location="media/profile_images")
                fs.delete(name=myInfo.profile_image.name.rsplit("/", 1)[1])
            
            fs = FileSystemStorage(location="media/profile_images")
            newImage = fs.save(myInfo.username + "_profile_image." + profile_image.name.rsplit(".", 1)[1], profile_image)
            fileurl = "profile_images" + fs.url(newImage)
            myInfo.profile_image = fileurl

        if request.POST.get("is_image_removed")=="True" and myInfo.profile_image.name.rsplit("/", 1)[1] != "default_profile_image.png":
            fs = FileSystemStorage(location="media/profile_images")
            fs.delete(name=myInfo.profile_image.name.rsplit("/", 1)[1])
            myInfo.profile_image = "profile_images/default_profile_image.png"
                
        myInfo.first_name = myForm.data.get("first_name")
        myInfo.last_name = myForm.data.get("last_name")
        myInfo.study = Study.objects.get(study_code=myForm.data.get("study"))
        myInfo.year_of_enrollment = myForm.data.get("year_of_enrollment")

        myInfo.save()       
                
        return redirect("../myProfile")

    else:
        myInfo = Student.objects.get(username = request.session.get("loggedInUser"))
        myForm = StudentForm(instance = myInfo)
        pathInfo = navbarPathInfo(request)
        context = {"pathinfo" : pathInfo, "active": "../myProfile", "myInfo": myInfo, "myForm": myForm}
        return render(request, "fesbbook_app/editProfile.html", context)

def conversations(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")

    loggedInUser = Student.objects.get(username = request.session.get("loggedInUser"))

    myChatRooms = ChatRoom.objects.filter(Q(first_student = loggedInUser) | Q(second_student = loggedInUser)).all()

    lastMessages = []

    for currentChatRoom in myChatRooms:
        lastMessage = Message.objects.filter(chat_room=currentChatRoom).last()
        lastMessage.unreadMessages = Message.objects.filter(Q(chat_room=currentChatRoom) & Q(receiver=loggedInUser)).count()
        lastMessages.append(lastMessage)

    lastMessages.sort(key=lambda x: x.date_sent, reverse=True)

    pathInfo = navbarPathInfo(request)

    context = {"pathinfo" : pathInfo, "active": "../conversation", "lastMessages": lastMessages}
    return render(request, "fesbbook_app/conversations.html", context)

def messages(request, username):
    if request.session.get("loggedInUser") == None:
        return redirect("/")
    if request.session.get("loggedInUser") == username:
        return redirect("../conversation")
    if not Student.objects.filter(username=username).exists():
        return redirect("../conversation")

    loggedInUser = Student.objects.get(username=request.session.get("loggedInUser"))
    chatFriend = Student.objects.get(username=username)

    # if request.method == "POST":
    #     newMessage = Message()
    #     newMessage.message = request.POST.get("message_text")
    #     newMessage.sender = loggedInUser
    #     newMessage.receiver = chatFriend
    #     newMessage.save()
    #     return redirect("messages", username=username)

    pathInfo = navbarPathInfo(request)
    allMessages = Message.objects.filter((Q(sender=loggedInUser) | Q(receiver=loggedInUser)) & (Q(sender=chatFriend) | Q(receiver=chatFriend)))
    allMessages = allMessages.order_by("date_sent").reverse()
    context = {"pathinfo" : pathInfo, "active": "../conversation", "title": username, "allMessages": allMessages}
    return render(request, "fesbbook_app/messages.html", context)

def newPassword(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")
    
    if request.method == "POST":
        new_password = PasswordForm(request.POST)
        new_password.data = {**new_password.data.dict(), 'loggedInUser': request.session.get("loggedInUser")}
        if new_password.is_valid():
            myInfo = Student.objects.get(username = request.session.get("loggedInUser"))
            myInfo.password = new_password.data["new_password"]
            myInfo.save()
            return redirect("../myProfile")

        else:
            pathInfo = navbarPathInfo(request)
            context = {"pathinfo" : pathInfo, "active": "../myProfile", "password": new_password}
            return render(request, "fesbbook_app/newPassword.html", context)

    else:
        password = PasswordForm()
        password.data = {**password.data.dict(), 'loggedInUser': request.session.get("loggedInUser")}
        pathInfo = navbarPathInfo(request)
        context = {"pathinfo" : pathInfo, "active": "../myProfile", "password": password}
        return render(request, "fesbbook_app/newPassword.html", context)

def navbarPathInfo(request):
    if request.session.get("loggedInUser") == None:
        return loggedOutNavbar
    else:
        return loggedInNavbar