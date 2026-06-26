from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ContactMessage, Inquiry, Property


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ("listing_type", "title", "description", "price", "address", "city", "state", "zip_code", "image", "brochure", "sold")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ("phone", "message")
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "Best contact number"}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "I'm interested in this property. Please contact me."}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Tell us how we can help."}),
        }
