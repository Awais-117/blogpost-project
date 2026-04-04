from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import Profile





class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def clean(self):
        cleaned_data = super().clean()

        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        # if first_name:
        #     base_username = slugify(f"{first_name}{last_name or ''}")
        #     username = base_username
        #     counter = 1
        
        
        if not first_name:
            raise forms.ValidationError("First name is required.")

        base_username = slugify(f"{first_name}{last_name or ''}")

        if not base_username:
            base_username = slugify(first_name)

        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

            self.cleaned_data["username"] = username

        return cleaned_data

    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     user.username = self.cleaned_data["username"]
    #     user.email = self.cleaned_data["email"]
    #     user.first_name = self.cleaned_data["first_name"]
    #     user.last_name = self.cleaned_data["last_name"]
    
    
    def save(self, commit=True):

        user = super().save(commit=False)

        email = self.cleaned_data["email"]

        user.username = email
        user.email = email

        if commit:
            user.save()

        return user
        # if commit:
        #     user.save()

        # return user
    
    
# class ProfileForm(forms.ModelForm):

#     # 1️⃣ Profile photo
#     profile_image = forms.ImageField(label="Profile photo", required=False)

#     # 2️⃣ Name
#     first_name = forms.CharField(label="First name", max_length=30)
#     last_name = forms.CharField(label="Last name", max_length=30, required=False)

#     # 3️⃣ Other profile fields
#     city = forms.CharField(max_length=100)
#     study = forms.CharField(max_length=100)
#     bio = forms.CharField(widget=forms.Textarea, required=False)

#     class Meta:
#         model = Profile
#         fields = []   # 🔥 THIS IS THE KEY

        
       
class ProfileForm(forms.ModelForm):

    # # 1️⃣ Profile photo
    # profile_image = forms.ImageField(label="Profile photo", required=False)

    # 2️⃣ Name (User model)
    # first_name = forms.CharField(label="First name", max_length=30)
    # last_name = forms.CharField(label="Last name", max_length=30, required=False)

    # 3️⃣ Profile fields
    # city = forms.CharField(max_length=100, required=False)
    # study = forms.CharField(max_length=100, required=False)
    # bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Profile
        fields = ["profile_image", "city", "study", "bio"]
        
        