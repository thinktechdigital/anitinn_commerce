from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Address, Vendor, Product, Review

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': '••••••••'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': '••••••••'
    }))
    role = forms.ChoiceField(choices=[('BUYER', 'Buyer'), ('VENDOR', 'Vendor')], widget=forms.Select(attrs={
        'class': 'form-input'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'johndoe'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'john@example.com'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'johndoe'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': '••••••••'
    }))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'birthday', 'avatar_url', 'hub']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'birthday': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'avatar_url': forms.TextInput(attrs={'class': 'form-input'}),
            'hub': forms.TextInput(attrs={'class': 'form-input'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_type', 'street_address', 'city', 'region', 'country', 'is_default']
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-input'}),
            'street_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'No. 45 Independence Ave'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Accra'}),
            'region': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Greater Accra'}),
            'country': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ghana'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'accent-royal-green'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'compare_at_price', 'image_url', 'stock', 'status']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Xiaomi Monitor 27"'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'compare_at_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'image_url': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
        }


class VendorSettingsForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['store_name', 'description', 'logo_url', 'banner_url']
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'logo_url': forms.TextInput(attrs={'class': 'form-input'}),
            'banner_url': forms.TextInput(attrs={'class': 'form-input'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], attrs={'class': 'form-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Write your review here...'}),
        }
