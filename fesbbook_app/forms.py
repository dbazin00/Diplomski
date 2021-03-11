from django import forms
from .models import Student
from django.core.validators import validate_email

INVALID_USERNAMES = ["None"]

class StudentForm(forms.ModelForm):
    password_confirm = forms.CharField(max_length=50, label="Potvrda lozinke", widget=forms.PasswordInput())

    class Meta:
        model = Student

        fields = "__all__"
        # fields = ("first_name", "last_name", "username", "password", "email", "year_of_enrollment", "birthday", "gender", "study")
        labels = {
            "first_name": "Ime",
            "last_name": "Prezime",
            "username": "Korisničko ime",
            "password": "Lozinka",
            "email": "E-mail",
            "year_of_enrollment": "Godina upisa",
            "birthday": "Datum rođenja",
            "gender": "Spol",
            "study": "Studij"
        }
        widgets = {
            "password": forms.PasswordInput(),
            "password_confirm": forms.PasswordInput(),
            "birthday": forms.DateInput(attrs={"type": "date"}),
            "gender": forms.RadioSelect()
        }

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.fields["study"].empty_label = "Odaberite studij"

    def clean(self):
        username = self.cleaned_data.get("username")
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")

        if Student.objects.filter(username=username).exists() or username in INVALID_USERNAMES:
            self.add_error("username", "Neispravno korisničko ime")
            
        if validate_email(email) != None:
            self.add_error("email", "Neispravna e-mail adresa")

        if password != password_confirm:
            self.add_error("password", "Lozinka nije potvrđena")
        return self.cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50, label="Korisničko ime")
    password = forms.CharField(max_length=50, label="Lozinka", widget=forms.PasswordInput(attrs={"type": "password"}))

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        student = Student.objects.all()
        if not student.filter(username=self.cleaned_data.get("username")).exists():
            self.add_error("username", "Neispravno korisničko ime")
        else:
            if student.get(username=self.cleaned_data.get("username")).password != self.cleaned_data.get("password"):
                self.add_error("password", "Neispravna lozinka")
        return self.cleaned_data
