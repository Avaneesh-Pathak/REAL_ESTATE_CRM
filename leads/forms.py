from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from .models import Lead, Agent, Category, FollowUp, Sale, Salary,Property,Promoter

User = get_user_model()



class LeadModelForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            'first_name',
            'last_name',
            'age',
            'agent',
            'description',
            'phone_number',
            'email',
            'profile_picture'            
        )
    def clean_first_name(self):
        data = self.cleaned_data["first_name"]
        return data
    def clean(self):
        pass


class LeadForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    age = forms.IntegerField(min_value=0)


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)
        field_classes = {'username': UsernameField}



class AssignAgentForm(forms.Form):
    agent = forms.ModelChoiceField(queryset=Agent.objects.none())

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        agents = Agent.objects.filter(organisation=request.user.userprofile)
        super(AssignAgentForm, self).__init__(*args, **kwargs)
        self.fields["agent"].queryset = agents


class LeadCategoryUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            'category',
        )

class CategoryModelForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            'name',
        )


class FollowUpModelForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = (
            'notes',
            'file'
        )


class SalaryForm(forms.ModelForm):
    class Meta:
        model = Salary
        fields = ['agent', 'base_salary', 'bonus', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={
                'type': 'date',  # Use HTML5 date input
                'class': 'form-control',
                'placeholder': 'DD-MM-YYYY',  # Optional placeholder
            }),
        }



class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['property', 'agent', 'sale_price', 'sale_date']
    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.fields['sale_date'].widget = forms.TextInput(attrs={
            'type': 'date',  # or you can set it to 'text' if you want to use datepicker
            'class': 'form-control',
            'placeholder': 'DD-MM-YYYY'  # Optional placeholder
        })



class PropertyModelForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['title', 'address', 'price', 'description', 'agent', 'organisation']

# PROJECT

from django import forms
from .models import Project, Plot


class ProjectForm(forms.Form):
    name = forms.CharField(max_length=100, label="Project Name")
    block_code = forms.CharField(max_length=10, label="Block Code")
    start_plot = forms.IntegerField(label="Start Plot Number")
    end_plot = forms.IntegerField(label="End Plot Number")



    def save(self, project, commit=True):
        block = super().save(commit=False)
        block.project = project
        if commit:
            block.save()
            # Create plots for this block
            for plot_num in range(self.cleaned_data['from_plot'], self.cleaned_data['to_plot'] + 1):
                Plot.objects.create(block=block, plot_number=plot_num)
        return block

# EMI




from django import forms

class EmiCalculationForm(forms.Form):
    total_amount = forms.DecimalField(label='Total Amount', max_digits=10, decimal_places=2)
    down_payment = forms.DecimalField(label='Down Payment', max_digits=10, decimal_places=2)
    
    TENURE_CHOICES = [
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '1 Year'),
        (24, '2 Years'),
        ('other', 'Other (Enter months)'),
    ]
    
    tenure = forms.ChoiceField(choices=TENURE_CHOICES, label='Select Tenure')
    custom_tenure = forms.IntegerField(label='Custom Tenure (in months)', required=False)
    interest_rate = forms.DecimalField(label='Interest Rate (%)', max_digits=5, decimal_places=2, required=True)

# DAYBOOK

from .models import Daybook

class DaybookEntryForm(forms.ModelForm):
    class Meta:
        model = Daybook
        fields = ['date', 'activity', 'custom_activity', 'amount', 'remark']
    
    def clean(self):
        cleaned_data = super().clean()
        activity = cleaned_data.get('activity')
        custom_activity = cleaned_data.get('custom_activity')

        if activity == 'others' and not custom_activity:
            raise forms.ValidationError("Please enter the custom activity.")

        return cleaned_data
    
# PROMOTER FORM




class PromoterForm(forms.ModelForm):
    class Meta:
        model = Promoter  # Use the model from models.py
        fields = [
            'name', 'email', 'mobile_number', 'address',
            'pan_no', 'id_card_number', 'joining_percentage'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'pan_no': forms.TextInput(attrs={'class': 'form-control'}),
            'id_card_number': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }