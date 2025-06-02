from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import PasswordInput, TextInput, FileInput
from .models import Product, Category
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.files.uploadedfile import UploadedFile


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ProductForm(forms.ModelForm):
    images = MultipleFileField(
        required=True,
        help_text='Upload up to 5 images. First image will be the primary image.',
        widget=MultipleFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'category']

    def clean_images(self):
        images = self.files.getlist('images')
        if not images:
            raise forms.ValidationError("At least one image is required.")
        if len(images) > 5:
            raise forms.ValidationError("Maximum 5 images allowed.")
        
        for image in images:
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError("All files must be images.")
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large ( > 5mb )")
        
        return images


class CreateUserForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'})
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'Date of Birth',
            'max': date.today().isoformat(),
            'min': (date.today() - relativedelta(years=110)).isoformat()
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'date_of_birth', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username already exists.')
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        email = self.cleaned_data.get('email', '')
        last_name = self.cleaned_data.get('last_name', '')

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('The two passwords do not match.')
            
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')

            if password1.isdigit() or password1.isalpha():
                raise forms.ValidationError('Password must contain both letters and numbers.')

            if last_name and last_name.lower() in password1.lower():
                raise forms.ValidationError('Password cannot contain your last name.')

            if email:
                email_name = email.split('@')[0]
                if email_name.lower() in password1.lower():
                    raise forms.ValidationError('Password cannot contain part of your email address.')

        return password2

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            max_age = date.today() - relativedelta(years=110)
            if dob < max_age:
                raise forms.ValidationError('Date of birth cannot be more than 110 years ago.')
            if dob > date.today():
                raise forms.ValidationError('Date of birth cannot be in the future.')
        return dob


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and not User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username does not exist.')
        
        if username and password:
            user = User.objects.filter(username=username).first()
            if user and not user.check_password(password):
                raise forms.ValidationError('The password is wrong, try again.')
        
        return super().clean()


class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new email'
        }),
        required=True
    )
    confirm_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new email'
        }),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        if email and confirm_email and email != confirm_email:
            raise forms.ValidationError("Email addresses must match!")
        return cleaned_data


class AccountInformationForm(forms.ModelForm):
    username = forms.CharField(min_length=4, validators=[
        RegexValidator(
            regex='^[a-zA-Z]',
            message='Username must start with a letter',
        ),
    ])
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'max': date.today().isoformat(),
            'min': (date.today() - relativedelta(years=100)).isoformat()
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            max_age = date.today() - relativedelta(years=100)
            if dob < max_age:
                raise forms.ValidationError('Date of birth cannot be more than 100 years ago.')
            if dob > date.today():
                raise forms.ValidationError('Date of birth cannot be in the future.')
        return dob