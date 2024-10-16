from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from .models import Lead, Agent, Category, FollowUp, Sale, Salary,Property,Promoter, Daybook,PlotBooking

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
        fields = ['title', 'project_name', 'price', 'block', 'agent', 'organisation']

# PROJECT


# EMI

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


# PLOT REGISTRATION
from decimal import Decimal


def calculate_emi(principal, booking_amount, tenure, interest_rate):
    # Handle cases where tenure or interest_rate is None or zero
    if tenure <= 0 or interest_rate < 0:
        return 0  # No EMI if tenure is zero or interest rate is negative

    # Convert interest rate from percentage to a decimal
    monthly_interest_rate = interest_rate / (12 * 100)
    
    # Calculate EMI using the formula
    emi = (principal - booking_amount) * monthly_interest_rate * ((1 + monthly_interest_rate) ** tenure) / \
          (((1 + monthly_interest_rate) ** tenure) - 1)
    
    return round(emi, 2)  # Round to two decimal places



class PlotBookingForm(forms.ModelForm):
    class Meta:
        model = PlotBooking
        fields = [
            'booking_date', 'name', 'father_husband_name', 'gender', 'custom_gender', 'dob', 'mobile_no',
            'address', 'bank_name', 'account_no', 'email', 'nominee_name', 'corner_plot_10', 'corner_plot_5',
            'full_pay_discount', 'location', 'project', 'associate_detail', 'promoter', 'Plot_price',
            'payment_type', 'booking_amount', 'mode_of_payment', 'payment_date', 'remark','emi_tenure', 'interest_rate'
        ]
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'payment_date':forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['promoter'].queryset = Promoter.objects.all()
        self.fields['project'].queryset = Property.objects.all()

        # Ensure only one of the corner plot or full pay options can be selected
        for field in ['corner_plot_10', 'corner_plot_5', 'full_pay_discount']:
            self.fields[field].widget.attrs.update({'onclick': 'limitSelection(this)'})

    # Adding clean method to validate and calculate EMI
    def clean(self):
        cleaned_data = super().clean()
        plot_price = cleaned_data.get('plot_price', 0)
        booking_amount = cleaned_data.get('booking_amount', 0)
        emi_tenure = cleaned_data.get('emi_tenure')
        interest_rate = cleaned_data.get('interest_rate')
        
        # Handle percentage-based adjustments
        corner_plot_10 = cleaned_data.get('corner_plot_10')
        corner_plot_5 = cleaned_data.get('corner_plot_5')
        full_pay_discount = cleaned_data.get('full_pay_discount')

        # Apply percentage-based increases or discounts on the plot price
        if corner_plot_10:
            plot_price *= Decimal('1.10')  # 10% increase for corner plot (10)
        elif corner_plot_5:
            plot_price *= Decimal('1.05')   # 5% increase for corner plot (5)
        elif full_pay_discount:
            plot_price *= Decimal('0.95')   # 5% discount for full payment

        # Calculate EMI if installment is selected
        payment_type = cleaned_data.get('payment_type')
        if payment_type == 'installment':
            emi_amount = calculate_emi(plot_price, booking_amount, emi_tenure, interest_rate)
            cleaned_data['emi_amount'] = emi_amount  # Save calculated EMI

        return cleaned_data
