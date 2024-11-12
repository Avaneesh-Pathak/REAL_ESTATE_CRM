from django.db import models
from django.contrib.auth.models import User 
from django.db.models.signals import post_save, pre_delete 
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.dispatch import receiver
from decimal import Decimal
from django.contrib import messages
from twilio.rest import Client
from django.conf import settings
from django.shortcuts import get_object_or_404

import logging
logger = logging.getLogger('app_errors')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_sms(to, message):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message_sent = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to='+9195485 82538'  # Use the `to` argument passed into the function
        )
        print(f"Message sent successfully with SID: {message_sent.sid}")
    except Exception as e:
        print(f"Error sending message: {e}")



class User(AbstractUser):
    is_organisor = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'User instance {self.pk} was {action}. Data: {data}')

    def delete(self, *args, **kwargs):
        # Collect the instance data before deletion
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'User instance {self.pk} was deleted. Data: {data}')
        
        # Call the parent delete method to actually delete the instance
        super().delete(*args, **kwargs)

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.IntegerField(blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Userprofile instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=UserProfile)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Userprofile instance  was Deleted. Data: {data}')



#New Addition
class LeadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Userprofile instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=LeadManager)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Userprofile instance  was Deleted. Data: {data}')
# New Addition Ended

class Lead(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    age = models.IntegerField(default=0)
    organisation = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING,null=True,blank=True)
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
    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Lead instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=Lead)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Lead instance  was Deleted. Data: {data}')



# File upload logging for follow-ups

def handle_upload_follow_ups(instance, filename):
    logger.info(f"Follow-up file uploaded for Lead ID: {instance.lead.pk}, File: {filename}")
    return f"lead_followups/lead_{instance.lead.pk}/{filename}"

# FollowUp Model with Logging
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

    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Userprofile instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=FollowUp)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'FollowUp instance  was Deleted. Data: {data}')

class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    parent_agent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_agents')
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Percentage of profit shared
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Total profit earned
    level = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.email} (Level {self.level})(Id {self.pk}) "

    def save(self, *args, **kwargs):
        # Get the parent agent
        parent_agent = self.parent_agent
        print(f"Parent agent: {parent_agent}")

        # Check if the parent agent exists and if commission percentage is valid
        if parent_agent:
            # Check if the parent agent's level is at maximum
            if parent_agent.level >= 5:
                print("Exceeding maximum level of agent.")  # You can add an error here if needed
                # You can raise an exception or handle it as per your business logic
                return  # Optionally, raise an exception or return

            # Set the new level based on the parent agent’s level
            self.level = parent_agent.level + 1
        else:
            self.level = 1  # Top-level agent if no parent agent is provided

        # Ensure that parent_agent is correctly assigned
        self.parent_agent = parent_agent
        print(f"Updated parent agent: {self.parent_agent}")
        print(f"Updated level: {self.level}")

        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Log the instance data (excluding internal attributes)
        action = "created" if is_new_instance else "updated"
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Agent instance {self.pk} was {action}. Data: {data}')

class Category(models.Model):
    name = models.CharField(max_length=30)  # New, Contacted, Converted, Unconverted
    organisation = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING,null=True,blank=True)

    def __str__(self):
        # Log whenever a Category instance is accessed
        logger.info(f"Category accessed: {self.name} (ID: {self.pk})")
        return self.name

    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Userprofile instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=Category)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Category instance  was Deleted. Data: {data}')



class Salary(models.Model):
    agent = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # Or your Agent model
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # New commission field
    payment_date = models.DateField()
    organisation = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.DO_NOTHING)
    property = models.ForeignKey('Property', null=True, blank=True, on_delete=models.DO_NOTHING)  # Link to Property model

    def total_compensation(self):
        """Calculate the total compensation including salary, bonus, and commission."""
        total = self.base_salary + (self.bonus or 0) + self.commission
        return total

    def __str__(self):
        # Log when the Salary instance is accessed
        logger.info(f"Salary accessed: Agent={self.agent.username}, Payment Date={self.payment_date}")
        return f"Salary for {self.agent.username} on {self.payment_date}"

    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Userprofile instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=Salary)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Salary instance  was Deleted. Data: {data}')

class Sale(models.Model):
    property = models.ForeignKey('Property', on_delete=models.DO_NOTHING)
    agent = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    sale_price = models.DecimalField(max_digits=15, decimal_places=2)
    sale_date = models.DateField()
    organisation = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Userprofile instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=Sale)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Sale instance  was Deleted. Data: {data}')

    def __str__(self):
        # Log when the Sale instance is accessed
        logger.info(f"Sale accessed: Agent={self.agent.username}, Sale Price=${self.sale_price}")
        return f"Sale by {self.agent.username} for ${self.sale_price}"

## Project
class Project(models.Model):
    project_name = models.CharField(max_length=255)
    block = models.CharField(max_length=2)
    kisans = models.ManyToManyField('Kisan', related_name='projects_kisan')
    dev_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    title = models.CharField(unique=True, max_length=255)
    lands = models.ManyToManyField('Kisan', related_name='projects_lands')
    type = models.CharField(max_length=255, null=True, blank=True)
    total_land_available_fr_plotting = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_development_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def create_composite_key(self):
        letters = f"{self.project_name[:]}".upper()
        bl = f"{self.block[:]}".upper()
        composite_key = f"{letters}-{bl}"
        logger.info(f"Composite key generated: {composite_key}")
        return composite_key

    def save(self, *args, **kwargs):
        self.title = self.create_composite_key()
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Project instance {self.pk} was {action}. Data: {data}')

@receiver(pre_delete, sender=Project)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
    print("hello")

        # Reset land_assigned status for all related lands (Kisan)
    for land in instance.lands.all():
        print(land)
        land.is_assigned = False
        land.save()
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Project instance  was Deleted. Data: {data}')

    def __str__(self):
        # Log access to the Project instance
        logger.info(f"Project accessed: Title={self.title}")
        return self.title

#TypeofPlot
class Typeplot(models.Model):
    type = models.CharField(max_length=200,unique=True)

    def __str__(self):
        return self.type    

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
    land = models.ForeignKey('Kisan', null=True, blank=True, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=7, blank=True)
    is_sold = models.BooleanField(default=False)
    is_in_emi = models.BooleanField(default=False)
    
    # Removed the redundant ForeignKey to Property itself
    related_property = models.ForeignKey('Property', null=True, blank=True, on_delete=models.DO_NOTHING) 
    PLOT_CHOICES = [
        ('Normal', 'Normal'),
        ('Corner', 'Corner'),
        ('Special', 'Special'),
    ]
    plot_type = models.CharField(max_length=50, choices=PLOT_CHOICES,default='Normal')

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
        is_new_instance = self.pk is None
        super().save(*args, **kwargs)  # Save first to get the ID

        # Generate and update title only if it's a new instance and title is empty
        if is_new_instance and not self.title:
            self.title = self.create_composite_key()
            self.__class__.objects.filter(pk=self.pk).update(title=self.title)

        action = "created" if is_new_instance else "updated"
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Property instance {self.pk} was {action}. Data: {data}')

@receiver(post_delete, sender=Property)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Property instance  was Deleted. Data: {data}')

class Bonus(models.Model):
    agent = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_awarded = models.DateField()

    def __str__(self):
        logger.info(f"Bonus awarded to {self.agent.username}: {self.bonus_amount}")
        return f"{self.agent.username} - Bonus of {self.bonus_amount}"
    
    def save(self, *args, **kwargs):
        # Log when a bonus is saved (either newly created or updated)
        action = "created" if self.pk is None else "updated"
        super().save(*args, **kwargs)
        logger.info(f"Bonus for agent {self.agent.username} was {action} with amount {self.bonus_amount} on {self.date_awarded}")
@receiver(post_delete, sender=Bonus)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Bonus instance  was Deleted. Data: {data}')


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
        # Calculate the area before saving and log the calculation
        logger.debug(f"Calculating area for length {self.length} and breadth {self.breadth}")
        self.area = self.length * self.breadth
        super().save(*args, **kwargs)
        logger.info(f"Area instance created with length {self.length}, breadth {self.breadth}, and calculated area {self.area}")
@receiver(post_delete, sender=Area)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Area instance  was Deleted. Data: {data}')

    def __str__(self):
        # Log whenever __str__ is called
        logger.info(f"Area object created for dimensions: Length {self.length}, Breadth {self.breadth}, Area {self.area}")
        return f"Property with length {self.length} and breadth {self.breadth}"

# EMI
class EmiPlan(models.Model):
    name = models.CharField(max_length=100)  # Name of the EMI plan
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Interest rate (e.g., 8.5%)
    tenure_months = models.IntegerField()  # Number of months for EMI
    minimum_downpayment = models.DecimalField(max_digits=10, decimal_places=2)  # Minimum down payment
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        logger.info(f"EMI Plan created: {self.name}")
        return self.name
    
    def save(self, *args, **kwargs):
        # Log when an EMI plan is saved
        action = "created" if self.pk is None else "updated"
        super().save(*args, **kwargs)
        logger.info(f"EMI Plan '{self.name}' was {action} with interest rate {self.interest_rate}% and tenure {self.tenure_months} months")

@receiver(post_delete, sender=EmiPlan)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'EmiPlan instance  was Deleted. Data: {data}')


# DAYBOOK
class Balance(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    carryover_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Add this field

    def __str__(self):
        logger.info(f"Balance created with amount: {self.amount} and carryover amount: {self.carryover_amount}")
        return f"Balance: {self.amount}"
    
    def save(self, *args, **kwargs):
        # Log when the balance is saved (either created or updated)
        action = "created" if self.pk is None else "updated"
        super().save(*args, **kwargs)
        logger.info(f"Balance {action} with amount: {self.amount} and carryover amount: {self.carryover_amount}")

@receiver(post_delete, sender=Balance)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Balance instance  was Deleted. Data: {data}')
    
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
    # Balance field to keep track of remaining balance
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    def __str__(self):
        # Log whenever __str__ is called (representing the Daybook entry)
        activity_display = self.custom_activity if self.activity == 'others' else self.activity
        logger.info(f"Daybook entry created: {self.date} - {activity_display} - Amount: {self.amount}")
        return f"{self.date} - {activity_display} - {self.amount}"

    def save(self, *args, **kwargs):
        # Calculate the new balance after the transaction
        previous_balance = self.__class__.objects.filter(id=self.id).first().current_balance if self.pk else 0
        if self.amount:  # If there's an amount for the transaction, update the balance
            self.current_balance = previous_balance + self.amount
        
        activity_display = self.custom_activity if self.activity == 'others' else self.activity
        action = "created" if self.pk is None else "updated"
        
        super().save(*args, **kwargs)
        
        # Log and send SMS after save
        logger.info(f"Daybook entry {action} with date: {self.date}, activity: {activity_display}, amount: {self.amount}, remaining balance: {self.current_balance}")



@receiver(post_delete, sender=Daybook)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Daybook instance  was Deleted. Data: {data}')
    # Prepare the deletion message
    message = f"Daybook Entry Deleted:\nDate: {instance.date}\nActivity: {instance.activity}\nAmount: {instance.amount}"
    if instance.remark:
        message += f"\nRemark: {instance.remark}"
    
    # Send SMS for deletion (replace with your actual phone number)
    my_number = '+918052513208'  # Replace with your actual phone number
    send_sms(to=my_number, message=message)

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
        logger.info(f"Promoter created: {self.name}, Email: {self.email}")
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
    Plot_price = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)#principal amount
    total_paidbycust = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)#principal amount
    payment_type = models.CharField(max_length=50, choices=[('custom', 'Custom Payment'), ('installment', 'Installments')])
    booking_amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode_of_payment = models.CharField(max_length=50, choices=[('cheque', 'Cheque'), ('rtgs', 'RTGS/NEFT'), ('cash', 'Cash')])
    payment_date = models.DateField()
    emi_tenure = models.IntegerField(blank=True, null=True)  # EMI tenure in months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Interest rate as a percentage
    emi_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=True)  # Calculated EMI amount
    remark = models.TextField(blank=True, null=True)
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    

    
    def update_property_status_if_paid(self):
        # Check if there are any pending EMI payments
        pending_emis = self.emi_payments.filter(status='Pending').count()
        if pending_emis == 0 and self.project:
            # All payments have been made
            property_obj = self.project
            property_obj.is_in_emi = False
            property_obj.is_sold = True
            property_obj.save()
            logger.info(f"Property status updated to sold: {property_obj.title}")
            # Send SMS when property status changes to sold
            # self.send_property_sold_sms(property_obj)
        else:
            logger.info(f"Property not yet fully paid; {pending_emis} EMI payments pending.")

    def __str__(self):
        logger.info(f"Plot Booking created: {self.name} on {self.booking_date}")
        return f"Plot Booking - {self.name} on {self.booking_date}"

    def save(self, *args, **kwargs):
        # Log when a plot booking is created or updated
        action = "created" if self.pk is None else "updated"
        super().save(*args, **kwargs)
        logger.info(f"PlotBooking {action}: {self.name} - {self.booking_date}")



@receiver(post_delete, sender=PlotBooking)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'PlotBooking instance  was Deleted. Data: {data}')
    # # Send SMS when a plot booking is deleted
    message = f"Plot booking was deleted:\nName: {instance.name}\nBooking Date: {instance.booking_date}"
    my_number = '+918052513208'  # Replace with the recipient's phone number
    send_sms(to=my_number, message=message)


class EMIPayment(models.Model):
    plot_booking = models.ForeignKey('PlotBooking', on_delete=models.DO_NOTHING, related_name='emi_payments')
    due_date = models.DateField()
    emi_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_for_agent = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid')], default='Pending')

    def remaining_amount(self):
        """Calculate the remaining amount to be paid."""
        remaining = self.emi_amount - self.amount_paid
        logger.debug(f"Remaining amount for EMI: {remaining} for {self.plot_booking}.")
        return remaining
    
    def interest_earned(self):
        """Calculate the remaining amount to be paid."""
        int_earn = self.emi_amount - self.amount_for_agent
        logger.debug(f"interest amount for EMI: {int_earn} for {self.plot_booking}.")
        return int_earn
    
    def agent_amount(self):
        """Calculate the remaining amount to be paid."""
        tenu = self.plot_booking.emi_tenure
        print(tenu)
        amount = self.plot_booking.Plot_price - self.plot_booking.booking_amount
        print(amount)
        agentamount = amount/tenu
        print(agentamount)
        # logger.debug(f"Remaining amount for EMI: {remaining} for {self.plot_booking}.")
        return agentamount

    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None
        print(self.amount_for_agent)
        self.amount_for_agent = self.agent_amount()
        print(self.amount_for_agent)

        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)

        # Determine the action
        action = "created" if is_new_instance else "updated"

        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'EMi Payment instance {self.pk} was {action}. Data: {data}')

    # def pay_emi(self, amount):
    #     """Pay the EMI with the specified amount."""
    #     remaining = self.remaining_amount()
        
    #     # Log the details of the payment attempt
    #     logger.info(f"Attempting to pay EMI: Current Amount Paid: {self.amount_paid}, Attempting to Pay: {amount}, Remaining: {remaining}")

    #     if amount <= 0:
    #         logger.warning(f"Invalid payment attempt: Amount must be greater than zero. Payment details: {amount}")
    #         return {'success': False, 'message': "Payment amount must be greater than zero."}
        
    #     if amount > remaining:
    #         logger.warning(f"Payment exceeds remaining EMI: Amount exceeds {remaining}. Payment details: {amount}")
    #         return {'success': False, 'message': f"Payment amount cannot exceed the remaining amount of {remaining}."}

    #     self.amount_paid += amount

    #     # Update the status based on the total amount paid
    #     if self.amount_paid >= self.emi_amount:
    #         self.amount_paid = self.emi_amount
    #         self.status = 'Paid'
    #     else:
    #         self.status = 'Pending'

    #     # Save the changes to the database
    #     self.save()

    #     # Check if all EMIs for this plot booking are paid
    #     self.plot_booking.update_property_status_if_paid()  # Update property status based on payment status
    #     logger.info(f"EMI payment processed: {amount} for {self.plot_booking}. Status: {self.status}")
    #     return {'success': True, 'message': "Payment processed successfully."}

    def __str__(self):
        logger.info(f"EMI Payment for Plot Booking: {self.plot_booking} - Due: {self.due_date}")
        return f"EMI Payment for {self.plot_booking} - Due: {self.due_date} - Status: {self.status}"

    class Meta:
        ordering = ['due_date']  # Order EMI payments by due date



@receiver(post_delete, sender=EMIPayment)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'EMIPayment instance  was Deleted. Data: {data}')


class Level(models.Model):
    level = models.CharField(max_length=222)
    interest = models.IntegerField()

    def __str__(self):
        logger.info(f"Level created: {self.level} with interest rate: {self.interest}")
        return self.level   

class Kisan(models.Model):

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    contact_number = models.IntegerField()
    address = models.TextField(max_length=50)
    is_assigned = models.BooleanField(default=False)
    khasra_number = models.IntegerField(unique=True)
    area_in_beegha = models.DecimalField(max_digits=20, decimal_places=3)
    land_costing = models.DecimalField(max_digits=12, decimal_places=3)
    development_costing = models.DecimalField(max_digits=12, decimal_places=3,default=0,null=True,blank=True)
    # Make these fields optional
    kisan_payment = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,default=0)
    land_address = models.TextField(max_length=50, null=True, blank=True)
    payment_to_kisan = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  
    basic_sales_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True) 
    is_sold = models.BooleanField(default=False)
    usable_land_total = models.FloatField(null=True, blank=True)
    

    def area_in_sqft(self):
        """Convert area from beegha to square feet."""
        convert_in_sqft = 27200
        sqft = self.area_in_beegha * convert_in_sqft
        logger.debug(f"Converted area from {self.area_in_beegha} beegha to {sqft} sqft.")
        return sqft
    
    def beegha_to_hectare(self):
        # 1 beegha = 0.25 hectares
        return self.area_in_beegha * Decimal('0.25') 
    
    def __str__(self) -> str:
        return f"Kisan: {self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Check if it's a new instance or an update
        is_new_instance = self.pk is None
        # Call the parent save method to save the instance to the database
        super().save(*args, **kwargs)
        # Determine the action
        action = "created" if is_new_instance else "updated"
        # Log the instance data in dictionary format (excluding internal attributes)
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        logger.info(f'Kisan Profile instance {self.pk} was {action}. Data: {data}')


@receiver(post_delete, sender=Kisan)
def log_userprofile_deletion(sender, instance, **kwargs):
        # Collect the instance data before deletion
    data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        
        # Log the deletion action with instance data in dictionary format
    logger.info(f'Kisan instance  was Deleted. Data: {data}')  







from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    Qty = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Bill(models.Model):
    bill_number = models.CharField(max_length=20, unique=True, blank=True)
    buyer_name = models.CharField(max_length=255)
    buyer_address = models.TextField()
    buyer_pan_number = models.CharField(max_length=20)
    buyer_state = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
 
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.bill_number:
            # Generate the bill number automatically (you can customize this logic)
            self.bill_number = f"INV-{Bill.objects.count() + 1}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill #{self.bill_number}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, related_name='items', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total_price based on rate, quantity, and tax
        self.total_price = (self.rate * self.quantity) + ((self.tax / 100) * (self.rate * self.quantity))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - Qty: {self.quantity}, Rate: {self.rate}, Tax: {self.tax}, Total: {self.total_price}"
