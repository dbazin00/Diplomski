from django.shortcuts import render, redirect, reverse
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
import datetime
import os
import shutil

from .forms import StudentForm, LoginForm, PasswordForm
from .models import Student, Study, Message, ChatRoom

# Create your views here.

loggedInNavbar = [{"text": "Početna", "path": "/", "icon":"fas fa-home"}, {"text": "Kolege", "path": "../studentList", "icon":"fas fa-address-book"}, {"text": "Razgovori", "path": "../conversation", "icon":"fas fa-comments"}, {"text": "Kontakt", "path": "../contact", "icon":"far fa-address-card"}]
loggedOutNavbar = [{"text": "Početna", "path": "/", "icon":"fas fa-home"}, {"text": "Kontakt", "path": "../contact", "icon":"far fa-address-card"}, {"text": "Registracija", "path": "registration", "icon":"fas fa-user-plus"}]

def index(request):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "/"}
    
    if(request.session.get("loggedInUser")):
        context["profile_image"] = getProfileImage(request)

    return render(request, "fesbbook_app/index.html", context)

def contact(request):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo": pathInfo, "active": "../contact"}

    if(request.session.get("loggedInUser")):
        context["profile_image"] = getProfileImage(request)
    
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
        form.lastActivity = timezone.now
        
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

    if request.method == "GET":
        if request.GET.get("username", False):
            fullQuerry = fullQuerry & Q(username__contains=request.GET.get("username"))
        if request.GET.get("study"):
            fullQuerry = fullQuerry & Q(study = loggedInUser.study)
        if request.GET.get("year"):
            fullQuerry = fullQuerry & Q(year_of_enrollment = request.GET.get("year"))
            
    studentList = Student.objects.filter(fullQuerry).exclude(username = loggedInUser.username)

    paginator = Paginator(studentList, 10)
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
    
    baseURL = request.get_full_path()

    if "page" in request.get_full_path():
        baseURL = request.get_full_path().split("page")[0]
    if baseURL == "/studentList":
        baseURL += "?"
    elif not baseURL.endswith("?") and not baseURL.endswith("&"):
        baseURL += "&"
    
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "../studentList", "studentList": studentList, "items": items, "page_range": page_range, "baseURL": baseURL, "profile_image": getProfileImage(request), "range": range(2010, (datetime.datetime.now().year))}
    return render(request, "fesbbook_app/studentList.html", context)

def studentInfo(request, username):
    if request.session.get("loggedInUser") == None:
        return redirect("/")

    if username == request.session.get("loggedInUser"):
        return redirect("myProfile")

    studentInfo = Student.objects.get(username = username)
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "../studentList", "studentInfo": studentInfo, "profile_image": getProfileImage(request)}
    return render(request, "fesbbook_app/studentInfo.html", context)    

def myProfile(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")

    myInfo = Student.objects.get(username = request.session.get("loggedInUser"))
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "../myProfile", "studentInfo": myInfo, "profile_image": getProfileImage(request)}
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
        context = {"pathinfo" : pathInfo, "active": "../myProfile", "myInfo": myInfo, "myForm": myForm, "profile_image": getProfileImage(request)}
        return render(request, "fesbbook_app/editProfile.html", context)

def conversations(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")

    loggedInUser = Student.objects.get(username = request.session.get("loggedInUser"))

    myChatRooms = ChatRoom.objects.filter(Q(first_student = loggedInUser) | Q(second_student = loggedInUser)).all()

    lastMessages = []

    for currentChatRoom in myChatRooms:
        lastMessage = Message.objects.filter(chat_room=currentChatRoom).last()

        if lastMessage != None:
            lastMessage.unreadMessages = Message.objects.filter(Q(chat_room=currentChatRoom) & Q(receiver=loggedInUser)).count()
            lastMessages.append(lastMessage)

    lastMessages.sort(key=lambda x: x.date_sent, reverse=True)

    pathInfo = navbarPathInfo(request)

    context = {"pathinfo" : pathInfo, "active": "../conversation", "lastMessages": lastMessages, "profile_image": getProfileImage(request)}
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

    readMessages(request, loggedInUser, chatFriend)

    pathInfo = navbarPathInfo(request)
    allMessages = Message.objects.filter((Q(sender=loggedInUser) | Q(receiver=loggedInUser)) & (Q(sender=chatFriend) | Q(receiver=chatFriend)))
    allMessages = allMessages.order_by("date_sent").reverse()
    context = {"pathinfo" : pathInfo, "active": "../conversation", "title": username, "allMessages": allMessages, "profile_image": getProfileImage(request)}
    return render(request, "fesbbook_app/messages.html", context)

def readMessages(request, loggedInUser, chatFriend):
    myUnreadMessages = Message.objects.filter(Q(sender=chatFriend) & Q(receiver=loggedInUser) & Q(is_read=False))
    
    for message in myUnreadMessages:
        message.is_read = True
        message.save()

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
            context = {"pathinfo" : pathInfo, "active": "../myProfile", "password": new_password, "profile_image": getProfileImage(request)}
            return render(request, "fesbbook_app/newPassword.html", context)

    else:
        password = PasswordForm()
        password.data = {**password.data.dict(), 'loggedInUser': request.session.get("loggedInUser")}
        pathInfo = navbarPathInfo(request)
        context = {"pathinfo" : pathInfo, "active": "../myProfile", "password": password, "profile_image": getProfileImage(request)}
        return render(request, "fesbbook_app/newPassword.html", context)

def chatbot(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")
    
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo, "active": "../chatbot", "profile_image": getProfileImage(request)}
    return render(request, "fesbbook_app/chatbot.html", context)

def myFiles(request):
    if request.session.get("loggedInUser") == None:
        return redirect("/")

    url = "media/files/" + request.session.get("loggedInUser")
    myFiles = []
    for path, directories, files in os.walk(url):
        if files:
            print(files[0])
            fileInfo = {
                "name": files[0],
                "path": "../" + path.split("/", 1)[1].replace("\\", "/") + "/" + files[0],
                "date_sent": datetime.datetime.fromtimestamp(os.path.getmtime(path + "/" + files[0])).strftime("%#d. %#m. %Y. %#H:%M"),
                "file_icon": getFileIcon(files[0])
            }
            myFiles.append(fileInfo)

    myFiles = sorted(myFiles, key=lambda k: k["date_sent"], reverse=True)

    pathInfo = navbarPathInfo(request)
    context = {"pathinfo": pathInfo, "active": "../myFiles", "profile_image": getProfileImage(request), "myFiles": myFiles}
    return render(request, "fesbbook_app/myFiles.html", context)

def deleteProfile(request):
    loggedInUser = Student.objects.get(username=request.session.get("loggedInUser"))
    profile_image_url = "media" + loggedInUser.profile_image.url
    if not loggedInUser.profile_image == "profile_images/default_profile_image.png" and os.path.exists(profile_image_url):
        os.remove(profile_image_url)

    url = "media/files/" + request.session.get("loggedInUser")
    if os.path.exists(url):
        shutil.rmtree(url)

    loggedInUser.delete()

    del request.session["loggedInUser"]
    return redirect("/")

def getFileIcon(fileName):
    fileExtension = fileName.split(".")[-1]
    
    if(fileExtension == "pdf"):
        return "fas fa-file-pdf"
        
    elif(fileExtension == "doc" or fileExtension == "dot" or fileExtension == "wbk" or fileExtension == "docx" or fileExtension == "docm" or fileExtension == "dotx" or fileExtension == "dotm" or fileExtension == "docb"):
        return "fas fa-file-word"

    elif(fileExtension == "xls" or fileExtension == "xlt" or fileExtension == "xlm" or fileExtension == "xlsx" or fileExtension == "xlsm" or fileExtension == "xltx" or fileExtension == "xltm" or fileExtension == "xlsb" or fileExtension == "xla" or fileExtension == "xlam" or fileExtension == "xll" or fileExtension == "xlw"):
        return "fas fa-file-excel"

    elif(fileExtension == "ppt" or fileExtension == "pot" or fileExtension == "pps" or fileExtension == "pptx" or fileExtension == "pptm" or fileExtension == "potx" or fileExtension == "potm" or fileExtension == "ppam" or fileExtension == "ppsx" or fileExtension == "ppsm" or fileExtension == "sldx" or fileExtension == "sldm"):
        return "fas fa-file-powerpoint"

    elif(fileExtension == "jpg" or fileExtension == "jpeg" or fileExtension == "png" or fileExtension == "gif" or fileExtension == "tiff"):
        return "fas fa-file-image"

    elif(fileExtension == "csv"):
        return "fas fa-file-csv"

    elif(fileExtension == "zip" or fileExtension == "zipx" or fileExtension == "rar"):
        return "fas fa-file-archive"
    
    elif(fileExtension == "m4a" or fileExtension == "flac" or fileExtension == "mp3" or fileExtension == "wav" or fileExtension == "wma" or fileExtension == "aac"):
        return "fas fa-file-audio"
    
    elif(fileExtension == "mp4" or fileExtension == "mov" or fileExtension == "wmv" or fileExtension == "flv" or fileExtension == "avi" or fileExtension == "mkv"):
        return "fas fa-file-video"

    else:
        return "fas fa-file"

def navbarPathInfo(request):
    if request.session.get("loggedInUser") == None:
        return loggedOutNavbar
    else:
        return loggedInNavbar

def getProfileImage(request):
    return Student.objects.get(username = request.session.get("loggedInUser")).profile_image.url

def error_400_view(request, exception):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo }
    return render(request, "fesbbook_app/error_pages/404.html", context)

def error_403_view(request, exception):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo }
    return render(request, "fesbbook_app/error_pages/404.html", context)

def error_404_view(request, exception):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo }
    return render(request, "fesbbook_app/error_pages/404.html", context)

def error_500_view(request):
    pathInfo = navbarPathInfo(request)
    context = {"pathinfo" : pathInfo }
    return render(request, "fesbbook_app/error_pages/500.html", context)