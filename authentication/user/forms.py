from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from allauth.account.forms import SignupForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class CustomSignupForm(SignupForm):
    email = forms.EmailField(widget=forms.TextInput(
        attrs={'type': 'email',
               'placeholder': ('E-mail address ')}))
    '''
    first_name = forms.CharField(
        label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )
    '''

    def save(self, request):

        # Ensure you call the parent class's save.
        # .save() returns a User object.
        user = super(CustomSignupForm, self).save(request)

        #user.phone_number = request.POST['phone_number']
        user.save()

        # Add your own processing here.

        # You must return the original result.
        return user
