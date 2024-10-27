from django.db import models
from django.contrib.auth.models import User 
from django.db.models.signals import post_save , pre_save
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    is_organisor = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)


# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.IntegerField(blank=True,null=True)
    email = models.EmailField(null=True,blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username
    
#New Addition
class LeadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

# New Addition Ended

class Lead(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField(default=0)
    organisation = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    agent = models.ForeignKey("Agent", null=True, blank=True, on_delete=models.SET_NULL)
    category = models.ForeignKey("Category",related_name="leads" ,null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()   
    profile_picture = models.ImageField(null=True, blank=True, upload_to="profile_pictures/")
    converted_date = models.DateTimeField(null=True, blank=True) 
    objects = LeadManager()
# New Added profile picture, converted date and objects
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# New Added 

def handle_upload_follow_ups(instance, filename):
    return f"lead_followups/lead_{instance.lead.pk}/{filename}"


class FollowUp(models.Model):
    lead = models.ForeignKey(Lead, related_name="followups", on_delete=models.DO_NOTHING)
    date_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(null=True, blank=True, upload_to=handle_upload_follow_ups)

    # Add the status field
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('postponed', 'Postponed'),
        ('in-Progress', 'In-Progress'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.lead.first_name} {self.lead.last_name}"



class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    organisation = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    # New Addition Here
    parent_agent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_agents')
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # Percentage of profit shared default 10 for level 1
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Total profit earned
    level = models.IntegerField(default=1)
    # New Addition Ends
    def __str__(self):
        
        return f"{self.user.email} (Level {self.level})(Id {self.pk}) "

    # def save(self, *args, **kwargs):
    #     if not self.pk:
    #         if self.level==1: # shi haii naa..??🙄
    #             self.commission_percentage=10.00
    #         elif self.level ==2:
    #             self.commission_percentage=4.00
    #         elif self.level==3:
    #             self.commission_percentage=3.00
    #         elif self.level ==4:
    #             self.commission_percentage=2.00
    #         elif self.level ==5:
    #             self.commission_percentage=1.00
    #     super().save(*args, **kwargs) 

    # def distribute_commission(self, sale_amount):
    #     """Distribute commission to agents up to 5 levels above based on a predefined structure."""
    #     commission_structure = {
    #         1: 10,  # Level 1: 10%
    #         2: 4,   # Level 2: 4%
    #         3: 3,   # Level 3: 3%
    #         4: 2,   # Level 4: 2%
    #         5: 1    # Level 5: 1%
    #     }

    #     total_distribution = 0
    #     agent = self
    #     level = 1
        
    #     # Traverse up the chain and distribute commission up to 5 levels
    #     while agent and level <= 5:
    #         # Calculate commission for the current level agent
    #         commission_amount = (commission_structure[level] / 100) * sale_amount
    #         agent.total_profit += commission_amount  # Update the agent's total profit
    #         agent.save(update_fields=['total_profit'])  # Save the updated profit to the database
            
    #         # Move to the parent agent for the next level
    #         agent = agent.parent_agent
    #         level += 1
    #         total_distribution += commission_amount
        
    #     return total_distribution

class Category(models.Model):
    name = models.CharField(max_length=30)  # New, Contacted, Converted, Unconverted
    organisation = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name

def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        


post_save.connect(post_user_created_signal, sender=User)



class Salary(models.Model):
    agent = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # Or your Agent model
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_date = models.DateField()
    organisation = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.DO_NOTHING)

    
    def __str__(self):
        return f"Salary for {self.agent.username} on {self.payment_date}"


class Sale(models.Model):
    property = models.ForeignKey('Property', on_delete=models.DO_NOTHING)
    agent = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    sale_price = models.DecimalField(max_digits=15, decimal_places=2)
    sale_date = models.DateField()
    organisation = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        super().save(*args,**kwargs)

        if self.property:
            self.property.is_sold = True
            self.property.save()

    def __str__(self):
        return f"Sale by {self.agent.username} for ${self.sale_price}"


## Project
class  Project(models.Model):
    project_name = models.CharField(max_length=255)
    block = models.CharField(max_length=2)

    title = models.CharField(unique=True,max_length=255)
    
    def create_composite_key(self):
        letters = f"{self.project_name[:]}" # Ensure uppercase
        bl = f"{self.block[:]}" # Ensure uppercase
        # Format the number to be 3 digits  
        # Construct the composite key
        composite_key = f"{letters}-{bl}"
        return composite_key

    def save(self, *args, **kwargs):
        # Call the original save method
        super().save(*args, **kwargs)

    
        self.title = self.create_composite_key()
        # Update the instance in the database without calling save() again
        self.__class__.objects.filter(pk=self.pk).update(title=self.title)

    def __str__(self):
        return self.project_name
    
#TypeofPlot
class Typeplot(models.Model):
    type = models.CharField(max_length=200,unique=True)

    def __str__(self):
        return self.type    

from django.db import models

class Property(models.Model):
    id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    totalprice = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    area = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    breadth = models.IntegerField(null=True, blank=True)
    block = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=200, null=True, blank=True)
    agent = models.ForeignKey('Agent', null=True, blank=True, on_delete=models.SET_NULL)
    project_id = models.ForeignKey('Project', null=True, blank=True, on_delete=models.SET_NULL)
    organisation = models.ForeignKey('UserProfile', null=True, blank=True, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=7, blank=True)
    is_sold = models.BooleanField(default=False)
    # Removed the redundant ForeignKey to Property itself
    related_property = models.ForeignKey('Property', null=True, blank=True, on_delete=models.DO_NOTHING)
  # This line is not needed
   
    def if_sold(self):
        print(f"Checking if property {self.title} is sold")
        return self.is_sold  # Ensure this references the correct model

    def __str__(self):
        return self.title
    
    def create_composite_key(self):
        letters = "PRP"  # Ensure uppercase
        formatted_number = f"{self.id:03}"  # Pads with zeros if necessary
        composite_key = f"{letters}-{formatted_number}"
        return composite_key

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.title:
            self.title = self.create_composite_key()
            self.__class__.objects.filter(pk=self.pk).update(title=self.title)


class Bonus(models.Model):
    agent = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_awarded = models.DateField()

    def __str__(self):
        return f"{self.agent.username} - Bonus of {self.bonus_amount}"


# Area
class Area(models.Model):
    length = models.IntegerField(editable=True)
    breadth = models.IntegerField(editable=True)
    area = models.IntegerField(null=True,blank=True )

    class Meta:
        # Ensure that the combination of length and breadth is unique
        constraints = [
            models.UniqueConstraint(fields=['length', 'breadth'], name='unique_length_breadth')
        ]

    def save(self, *args, **kwargs):
        # Calculate the area before saving the model
        self.area = self.length * self.breadth
        super(Area, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return  f"Property with length {self.length} and breadth {self.breadth}"

# EMI
class EmiPlan(models.Model):
    name = models.CharField(max_length=100)  # Name of the EMI plan
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Interest rate (e.g., 8.5%)
    tenure_months = models.IntegerField()  # Number of months for EMI
    minimum_downpayment = models.DecimalField(max_digits=10, decimal_places=2)  # Minimum down payment
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# DAYBOOK


class Daybook(models.Model):
    ACTIVITY_CHOICES = [
        ('pantry', 'Pantry'),
        ('fuel', 'Fuel'),
        ('office_expense', 'Office Expense'),
        ('site_development', 'Site Development'),
        ('site_visit', 'Site Visit'),
        ('printing', 'Printing'),
        ('utility', 'Utility'),
        ('others', 'Others'),
    ]

    date = models.DateField(default=timezone.now)
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    custom_activity = models.CharField(max_length=100, blank=True, null=True)  # For "Others"
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.activity} - {self.amount}"





# PROMOTER MODEL

class Promoter(models.Model):
    # Personal Information
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    mobile_number = models.CharField(max_length=15)
    address = models.TextField()

    # Legal and Joining Information
    pan_no = models.CharField(max_length=15)
    id_card_number = models.CharField(max_length=20)
    joining_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage of joining

    def __str__(self):
        return self.name




# PLOT BOOKING

class PlotBooking(models.Model):
    booking_date = models.DateField()
    name = models.CharField(max_length=100)
    father_husband_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], null=True)
    custom_gender = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField()
    mobile_no = models.CharField(max_length=15)
    address = models.TextField()
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_no = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField()
    nominee_name = models.CharField(max_length=100, blank=True, null=True)
    # PLC Charges
    corner_plot_10 = models.BooleanField(default=False)
    corner_plot_5 = models.BooleanField(default=False)
    full_pay_discount = models.BooleanField(default=False)
    location = models.CharField(max_length=255)
    project = models.OneToOneField(Property, on_delete=models.DO_NOTHING, related_name='project', unique=True,null=True, blank=True)
    associate_detail = models.BooleanField(default=False)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='plot_bookings')  # Changed to lowercase
    Plot_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=50, choices=[('custom', 'Custom Payment'), ('installment', 'Installments')])
    booking_amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode_of_payment = models.CharField(max_length=50, choices=[('cheque', 'Cheque'), ('rtgs', 'RTGS/NEFT'), ('cash', 'Cash')])
    payment_date = models.DateField()
    emi_tenure = models.IntegerField(blank=True, null=True)  # EMI tenure in months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Interest rate as a percentage
    emi_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=True)  # Calculated EMI amount
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Plot Booking - {self.name} - {self.booking_date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Trigger commission distribution for the selected agent
        if self.agent:
            self.agent.distribute_commission(self.Plot_price)

class EMIPayment(models.Model):

    plot_booking = models.ForeignKey(PlotBooking, on_delete=models.DO_NOTHING, related_name='emi_payments')
    due_date = models.DateField()
    emi_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid')], default='Pending')

    def remaining_amount(self):
        return self.emi_amount - self.amount_paid

    def pay_emi(self, amount):
        """Pay the EMI with the specified amount."""
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        self.amount_paid += amount

        # Check if the payment meets or exceeds the EMI amount
        if self.amount_paid >= self.emi_amount:
            self.amount_paid = self.emi_amount
            self.status = 'Paid'
        else:
            self.status = 'Pending'  # Update to pending if not fully paid

        self.save()  # Save the changes to the database

    def __str__(self):
        return f"EMI Payment for {self.plot_booking} - Due: {self.due_date} - Status: {self.status}"

    class Meta:
        ordering = ['due_date']  # Order EMI payments by due date

class Level(models.Model):
    level = models.CharField(max_length=222)
    interest = models.IntegerField()

    def __str__(self):
        return  self.level
    

class Kisan(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    contact_number = models.IntegerField()
    address = models.TextField(max_length=50)

    khasra_number = models.IntegerField(unique=True)
    area_in_beegha = models.DecimalField(max_digits=20, decimal_places=3)
    land_costing = models.DecimalField(max_digits=12, decimal_places=3)
    development_costing = models.DecimalField(max_digits=12, decimal_places=3)
    
    # Make these fields optional
    kisan_payment = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    land_address = models.TextField(max_length=50, null=True, blank=True)

    payment_to_kisan = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  
    basic_sales_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  

    def __str__(self) -> str:
        return f"{self.first_name} with khasra no {self.khasra_number}"
    





 