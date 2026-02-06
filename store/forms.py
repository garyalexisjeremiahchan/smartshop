from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    """Form for submitting product reviews"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default rating to 5 stars if not already set
        if not self.instance.pk and 'rating' not in self.data:
            self.fields['rating'].initial = 5
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[
                    (5, '★★★★★'),
                    (4, '★★★★☆'),
                    (3, '★★★☆☆'),
                    (2, '★★☆☆☆'),
                    (1, '★☆☆☆☆'),
                ],
                attrs={'class': 'form-select'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Summary of your review'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this product'
            }),
        }


class CheckoutForm(forms.Form):
    """Form for checkout process"""
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    address_line1 = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'})
    )
    address_line2 = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2 (Optional)'})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )
    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'})
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'})
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Order notes (Optional)'
        })
    )
