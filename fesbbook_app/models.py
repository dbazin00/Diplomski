from django.db import models
from django.core.validators import RegexValidator
from django import forms
import datetime

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
    profile_image = models.ImageField(blank=True, null=True, upload_to="profile_images")
    year_of_enrollment = models.IntegerField(choices=YEAR_CHOICES , default=current_year)
    birthday = models.DateField(default=datetime.date.today)
    study = models.ForeignKey(Study, on_delete=models.CASCADE, default=None)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    isActive = models.BooleanField(default=False)
    