from django.db import models
from django.core.validators import RegexValidator
from django import forms
from django.db.models import Q
import datetime
from django.utils import timezone

# Create your models here.

YEAR_CHOICES = [(r,r) for r in range(2010, datetime.date.today().year)]
GENDER_CHOICES = [("M","M"), ("Ž", "Ž")]

def current_year():
    return datetime.date.today().year

class Study(models.Model):
    study_code = models.PositiveIntegerField(validators=[RegexValidator(r'^\d{100,999}$')], primary_key=True)
    study_name = models.CharField(max_length=50)
    def __str__(self):
        return (str(self.study_code) + " " + self.study_name)

class Student(models.Model):
    first_name = models.CharField(max_length=50, default=None)
    last_name = models.CharField(max_length=50, default=None)
    username = models.CharField(max_length=50, unique=True, default=None)
    password = models.CharField(max_length=50, default=None)
    email = models.EmailField(max_length=50, unique=True, default=None)
    profile_image = models.ImageField(blank=True, null=True)
    year_of_enrollment = models.IntegerField(choices=YEAR_CHOICES , default=current_year)
    birthday = models.DateField(default=datetime.date.today)
    study = models.ForeignKey(Study, on_delete=models.CASCADE, default=None)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    isActive = models.BooleanField(default=False)
    lastActivity = models.DateTimeField(auto_now=True)

class ChatRoomManager(models.Manager):
    def get_or_new(self, loggedInUser, chatFriend):
        if loggedInUser == chatFriend:
            return None

        querry1 = Q(first_student__username = loggedInUser) & Q(second_student__username = chatFriend)
        querry2 = Q(first_student__username = chatFriend) & Q(second_student__username = loggedInUser)

        qs = self.get_queryset().filter(querry1 | querry2).distinct()

        if qs.count() >= 1:
            return qs.order_by("id").first(), False

        else:
            student1 = Student.objects.get(username=loggedInUser)
            student2 = Student.objects.get(username=chatFriend)

            if loggedInUser != chatFriend:
                obj = self.model(
                    first_student=student1,
                    second_student=student2
                )
                obj.save()
                return obj, True

            return None, False


class ChatRoom(models.Model):
    first_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="first_student")
    second_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="second_student")
    objects = ChatRoomManager()

class Message(models.Model):
    message = models.CharField(max_length=500, default=None, blank=True, null=True)
    sender = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="receiver")
    date_sent = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="chat_room", default=None)


        