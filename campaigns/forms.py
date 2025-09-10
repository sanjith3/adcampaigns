from django import forms #type: ignore
from django.contrib.auth.forms import UserCreationForm #type: ignore
from django.contrib.auth.models import User #type: ignore
from .models import AdRecord


class AdRecordForm(forms.ModelForm):
    class Meta:
        model = AdRecord
        fields = ['ad_name', 'business_name', 'notes']
        widgets = {
            'ad_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PaymentDetailsForm(forms.ModelForm):
    class Meta:
        model = AdRecord
        fields = ['amount', 'upi_last_four']
        widgets = {
            'amount': forms.Select(attrs={'class': 'form-control'}),
            'upi_last_four': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '4',
                'pattern': '[0-9]{4}',
                'title': 'Enter last 4 digits of UPI ID'
            }),
        }


class AdminVerificationForm(forms.Form):
    full_upi_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter full UPI ID from payment gateway'
        })
    )

    def clean_full_upi_id(self):
        full_upi_id = self.cleaned_data.get('full_upi_id')
        if len(full_upi_id) < 4:
            raise forms.ValidationError("UPI ID must be at least 4 characters long")
        return full_upi_id


class ActivateAdForm(forms.ModelForm):
    class Meta:
        model = AdRecord
        fields = ['start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class AdminCreateUserForm(UserCreationForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        # Ensure created users are not admins by default
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user