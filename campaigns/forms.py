from django import forms
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