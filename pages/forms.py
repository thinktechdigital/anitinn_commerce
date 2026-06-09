from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Address, Vendor, Product, Review, SupportTicket, Coupon, ReturnRequest, Category

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': '••••••••'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': '••••••••'
    }))
    role = forms.ChoiceField(choices=[('BUYER', 'Customer'), ('VENDOR', 'Vendor')], widget=forms.Select(attrs={
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
        category = forms.ModelChoiceField(
            queryset=Category.objects.all(),
            empty_label="Select a category"
        )

        class Meta:
            model = Product
            exclude = ['vendor']
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
        fields = [
            'store_name', 'description', 'logo_url', 'banner_url',
            'tin', 'registration_number', 'business_document', 'primary_brand_color', 'accent_brand_color',
            'payout_method', 'momo_number', 'momo_name',
            'bank_name', 'bank_account_number', 'bank_account_name',
            'self_shipping_mode', 'subscription_tier', 'status'
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'logo_url': forms.TextInput(attrs={'class': 'form-input'}),
            'banner_url': forms.TextInput(attrs={'class': 'form-input'}),
            'tin': forms.TextInput(attrs={'class': 'form-input'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-input'}),
            'business_document': forms.FileInput(attrs={'class': 'form-input'}),
            'primary_brand_color': forms.TextInput(attrs={'class': 'form-input'}),
            'accent_brand_color': forms.TextInput(attrs={'class': 'form-input'}),
            'payout_method': forms.Select(choices=[('MOMO', 'Mobile Money'), ('BANK', 'Bank Account'), ('CRYPTO', 'Cryptocurrency')], attrs={'class': 'form-input'}),
            'momo_number': forms.TextInput(attrs={'class': 'form-input'}),
            'momo_name': forms.TextInput(attrs={'class': 'form-input'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-input'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-input'}),
            'bank_account_name': forms.TextInput(attrs={'class': 'form-input'}),
            'self_shipping_mode': forms.CheckboxInput(attrs={'class': 'accent-royal-green'}),
            'subscription_tier': forms.TextInput(attrs={'class': 'form-input'}),
            'status': forms.Select(choices=[('ACTIVE', 'Active'), ('SUSPENDED', 'Suspended'), ('ARCHIVED', 'Archived'), ('DELETED', 'Deleted')], attrs={'class': 'form-input'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], attrs={'class': 'form-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Write your review here...'}),
        }


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['order', 'subject', 'priority', 'message']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-input'}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'What do you need help with?'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Share the details so support can respond quickly.'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['order'].queryset = user.orders.order_by('-created_at')
        self.fields['order'].required = False


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'description', 'discount_type', 'value', 'minimum_order_amount', 'active', 'starts_at', 'expires_at', 'usage_limit']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ACCRA10'}),
            'description': forms.TextInput(attrs={'class': 'form-input'}),
            'discount_type': forms.Select(attrs={'class': 'form-input'}),
            'value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'minimum_order_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'active': forms.CheckboxInput(attrs={'class': 'accent-royal-green'}),
            'starts_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['order', 'reason', 'details']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-input'}),
            'reason': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Damaged item, wrong item, or quality issue'}),
            'details': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['order'].queryset = user.orders.filter(status__in=['SHIPPED', 'DELIVERED']).order_by('-created_at')
