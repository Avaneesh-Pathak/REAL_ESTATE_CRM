from django.db import models
from django.contrib.auth.models import User 
from django.db.models.signals import post_save , pre_save
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_organisor = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)


# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

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
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
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
    lead = models.ForeignKey(Lead, related_name="followups", on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(null=True, blank=True, upload_to=handle_upload_follow_ups)

    def __str__(self):
        return f"{self.lead.first_name} {self.lead.last_name}"






class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email


class Category(models.Model):
    name = models.CharField(max_length=30)  # New, Contacted, Converted, Unconverted
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        


post_save.connect(post_user_created_signal, sender=User)



class Salary(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE)  # Or your Agent model
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_date = models.DateField()
    organisation = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE)

    
    def __str__(self):
        return f"Salary for {self.agent.username} on {self.payment_date}"


class Sale(models.Model):
    property = models.ForeignKey('Property', on_delete=models.CASCADE)
    agent = models.ForeignKey(User, on_delete=models.CASCADE)
    sale_price = models.DecimalField(max_digits=15, decimal_places=2)
    sale_date = models.DateField()
    organisation = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Sale of {self.property.address} by {self.agent.username} for ${self.sale_price}"

class Property(models.Model):
    # project_name = models.CharField(max_length=255,default='Untitled Property')
    # block_code = models.CharField(max_length=1)
    # from_plot=models.IntegerField
    # to_plot=models.IntegerField
    title = models.CharField(max_length=255,default='Untitled Property')
    project_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    block = models.TextField(null=True, blank=True)
    agent = models.ForeignKey(Agent, null=True, blank=True, on_delete=models.SET_NULL)
    # Add any other fields necessary for the property model
    organisation = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
class Project_Name(models.Model):
    project_code= models.OneToOneField(User, on_delete=models.CASCADE)



class Bonus(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_awarded = models.DateField()

    def __str__(self):
        return f"{self.agent.username} - Bonus of {self.bonus_amount}"


# PROJECT


class Project(models.Model):
    name = models.CharField(max_length=100)
    block_code = models.CharField(max_length=10,default='NA')

    def __str__(self):
        return self.name

class Plot(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    plot_no = models.CharField(max_length=10,default=0)
    status = models.CharField(max_length=10, choices=[('Available', 'Available'), ('Booked', 'Booked'), ('Hold', 'Hold'), ('Sold Out', 'Sold Out')], default='Available')
    buyer_name = models.CharField(max_length=100, null=True, blank=True)
    booking_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.project.name} - {self.plot_no}"
    

# EMI
from django.db import models

class EmiPlan(models.Model):
    name = models.CharField(max_length=100)  # Name of the EMI plan
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Interest rate (e.g., 8.5%)
    tenure_months = models.IntegerField()  # Number of months for EMI
    minimum_downpayment = models.DecimalField(max_digits=10, decimal_places=2)  # Minimum down payment
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# DAYBOOK

from django.db import models
from django.utils import timezone

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
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.activity} - {self.amount}"
