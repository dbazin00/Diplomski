from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("contact", views.contact, name="contact"),
    path("login", views.login, name="login"),
    path("registration", views.registration, name="registration"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("studentList", views.studentList, name="studentList"),
    path("myProfile", views.myProfile, name="myProfile"),
    path("studentList/<str:username>", views.studentInfo, name="studentInfo"),
    path("editProfile", views.editProfile, name="editProfile"),
    path("newPassword", views.newPassword, name="newPassword"),
    path("conversation", views.conversations, name="conversations"),
    path("conversation/<str:username>", views.messages, name="messages"),
    path("chatbot", views.chatbot, name="chatbot"),
    path("myFiles", views.myFiles, name="myFiles"),
    path("deleteProfile", views.deleteProfile, name="deleteProfile"),
]