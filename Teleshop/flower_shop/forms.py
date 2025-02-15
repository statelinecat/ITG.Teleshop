from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User
from django.contrib.auth import authenticate

from .models import Review, Order

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(request=self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Неверный email или пароль.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("Этот аккаунт неактивен.")
        return self.cleaned_data

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User
from django.contrib.auth import authenticate
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
import uuid  # Для генерации уникального username


class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']  # Убираем username
        widgets = {
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        # Генерируем уникальное значение для username
        user.username = str(uuid.uuid4())  # Используем UUID для генерации уникального username

        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Убираем упоминания о username, так как его больше нет в форме
        self.fields['password1'].error_messages = {
            'password_too_similar': 'Пароль слишком похож на email.',
            'password_too_short': 'Пароль должен содержать не менее 8 символов.',
            'password_common': 'Пароль слишком простой.',
        }