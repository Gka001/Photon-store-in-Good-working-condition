from django import forms

class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100, label='Full Name')
    address = forms.CharField(widget=forms.Textarea, label='Shipping Address')
    phone = forms.CharField(max_length=15, label='Phone Number')
