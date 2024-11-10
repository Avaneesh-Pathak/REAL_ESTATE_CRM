from django import forms
from django.utils import timezone
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Lead, Agent, Category, FollowUp, Sale, Salary,Property,Promoter, Daybook,PlotBooking,Agent,Kisan,UserProfile

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'contact_number', 'profile_picture']  # Add other fields if needed

    username = forms.CharField(max_length=150)  # Include username in the form
    email = forms.EmailField()  # Include email in the form

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

class SearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=100)

    
            
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
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'accept': 'image/*'})
        }
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
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
        # widgets = {
        #     'username': forms.TextInput(attrs={'class': 'login__input'}),
        #     'email': forms.EmailInput(attrs={'class': 'login__input'}),
        #     'password': forms.PasswordInput(attrs={'class': 'login__input'}),
        # }



class AssignAgentForm(forms.Form):
    agent = forms.ModelChoiceField(queryset=Agent.objects.all())
    print(agent)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        agents = Agent.objects.all()
        print(agents)
        super(AssignAgentForm, self).__init__(*args, **kwargs)
        self.fields["agent"].queryset = agents
        self.fields['agent'].widget.attrs.update({'class': 'form-control'})


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
            'file',
            'status'
        )
        labels = {
                    'notes': 'Follow-Up Notes',
                    'file': 'Upload File (optional)',
                    'status': 'Status',
                }


class SalaryForm(forms.ModelForm):
    class Meta:
        model = Salary
        fields = ['payment_date']
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

    def __init__(self, *args, **kwargs):
        self.total_land = kwargs.pop('total_land', None)  # Pass available land to the form
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        num_properties = cleaned_data.get('num_properties')
        length = cleaned_data.get('length')
        breadth = cleaned_data.get('breadth')

        # Calculate area for custom dimensions if provided
        if length and breadth:
            area = length * breadth
        else:
            # You can define your own logic to get the area based on the selected dimension
            area = 0

        # Check if total area exceeds available land
        if area * num_properties > self.total_land:
            raise forms.ValidationError(f'You can only create properties for a maximum of {self.total_land} sqft of land available.')

        return cleaned_data

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.now().date()  # Set current date as the initial value

    def clean_date(self):
        date = self.cleaned_data.get('date')
        today = timezone.now().date()
        if date != today:
            raise forms.ValidationError("Please enter today's date.")
        return date

class BalanceUpdateForm(forms.Form):
    ACTION_CHOICES = [
        ('add', 'Add'),
        ('deduct', 'Deduct'),
    ]

    action = forms.ChoiceField(choices=ACTION_CHOICES, required=True)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)

    
      
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
    if tenure < 0 or interest_rate < 0:
        return 0  # No EMI if tenure is zero or interest rate is negative

    # Convert interest rate from percentage to a decimal
    monthly_interest_rate = interest_rate / (12 * 100)
    
    # Calculate EMI using the formula
    emi = (principal - booking_amount) * monthly_interest_rate * ((1 + monthly_interest_rate) ** tenure) / \
          (((1 + monthly_interest_rate) ** tenure) - 1)
    
    return round(emi, 2)  # Round to two decimal places



class PlotBookingForm(forms.ModelForm):
    agent = forms.ModelChoiceField(queryset=Agent.objects.all(), required=False)
    class Meta:
        model = PlotBooking
        fields = [
            'booking_date', 'name', 'father_husband_name', 'gender', 'custom_gender', 'dob', 'mobile_no',
            'address', 'bank_name', 'account_no', 'email', 'nominee_name', 'corner_plot_10', 'corner_plot_5',
            'full_pay_discount', 'location', 'project', 'agent', 'Plot_price',
            'payment_type', 'booking_amount', 'mode_of_payment', 'payment_date', 'remark','emi_tenure', 'interest_rate'
        ]
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'project': forms.Select(attrs={'id': 'project-select'}),
            # 'booking_amount': forms.IntegerField(attrs={'id': 'id_booking_amount'}),
            'payment_type': forms.Select(attrs={'id': 'id_payment_type'}),
            'payment_date':forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args,project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # If updating an existing instance
            # Set the fields to be read-only during updates
            self.fields['project'].widget.attrs['readonly'] = True
            self.fields['Plot_price'].widget.attrs['readonly'] = True
            self.fields['booking_amount'].widget.attrs['readonly'] = True
            self.fields['payment_type'].widget.attrs['readonly'] = True
            self.fields['agent'].widget.attrs['readonly'] = True
            
            # Optionally, add 'disabled' to prevent submission of these fields
            self.fields['project'].disabled = True
            self.fields['Plot_price'].disabled = True
            self.fields['booking_amount'].disabled = True
            self.fields['payment_type'].disabled = True
            self.fields['agent'].disabled = True
        self.fields['project'].required = True  # Set the field as required
        self.fields['booking_date'].initial = date.today()

        # Define PLC choices and add plc_charge field
        PLC_CHOICES = [
            ('corner_plot_10', 'Corner Plot 10% Increase'),
            ('corner_plot_5', 'Corner Plot 5% Increase'),
            ('full_pay_discount', 'Full Payment 5% Discount')
        ]
        
        self.fields['plc_charge'] = forms.ChoiceField(
            choices=PLC_CHOICES,
            widget=forms.RadioSelect,
            label="PLC Charge",
            required=False
        )

        self.fields['final_price'] = forms.DecimalField(label='Final Price', required=False, initial=0.0, widget=forms.TextInput(attrs={'readonly': 'readonly'}))

        self.fields['agent'].queryset = Agent.objects.all()
        self.fields['project'].queryset = Property.objects.all()

        if project:
            try:
                property_instance = Property.objects.get(project=project)
                self.initial['Plot_price'] = property_instance.totalprice  # Set the initial price
            except Property.DoesNotExist:
                self.initial['Plot_price'] = 0


        # Ensure only one of the corner plot or full pay options can be selected
        for field in ['corner_plot_10', 'corner_plot_5', 'full_pay_discount']:
            self.fields[field].widget.attrs.update({'onclick': 'limitSelection(this)'})

    # Adding clean method to validate and calculate EMI
    def clean(self):
        cleaned_data = super().clean()
        plot_price = cleaned_data.get('plot_price', 0)  # Use 'Plot_price' here to reference the correct field
        booking_amount = cleaned_data.get('booking_amount', 0)
        
         # Handle percentage-based adjustments
        plc_charge = cleaned_data.get('plc_charge')

        # Apply percentage-based increases or discounts on the plot price based on PLC charge selection
        if plc_charge == 'corner_plot_10':
            discount = booking_amount * Decimal('0.10')  # 10% increase
            final_price = booking_amount + discount
        elif plc_charge == 'corner_plot_5':
            discount = booking_amount * Decimal('0.05')  # 5% increase
            final_price = booking_amount + discount
        elif plc_charge == 'full_pay_discount':
            discount = booking_amount * Decimal('0.05')  # 5% discount
            final_price = booking_amount - discount
        else:
            final_price = booking_amount  # No adjustment if no PLC charge selected

        # Set the final price in cleaned_data for later use
        cleaned_data['final_price'] = final_price

        # Calculate EMI if installment is selected
        interest_rate = cleaned_data.get('interest_rate')
        emi_tenure = cleaned_data.get('emi_tenure')
        payment_type = cleaned_data.get('payment_type')
        if payment_type == 'installment':
            emi_amount = calculate_emi(plot_price, booking_amount, emi_tenure, interest_rate)
            cleaned_data['emi_amount'] = emi_amount  # Save calculated EMI

        return cleaned_data
    

class KisanForm(forms.ModelForm):
    
    class Meta:
        model = Kisan
        fields = [
            'first_name', 'last_name', 'contact_number', 'address',
            'khasra_number', 'area_in_beegha', 'land_costing',
            'land_address'
        ]
    def __init__(self, *args, **kwargs):
        super(KisanForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm'
            })