# from django.contrib import admin

# # Register your models here.
# from .models import User, Lead, Agent,UserProfile, Category

# admin.site.register(Category)
# admin.site.register(User)
# admin.site.register(UserProfile)
# admin.site.register(Lead)
# admin.site.register(Agent)

from django.contrib import admin

from .models import User, Lead, Agent, UserProfile, Category, FollowUp, Salary, Sale,Property



class LeadAdmin(admin.ModelAdmin):
    # fields = (
    #     'first_name',
    #     'last_name',
    # )

    list_display = ['first_name', 'last_name', 'age', 'email']
    list_display_links = ['first_name']
    list_editable = ['last_name']
    list_filter = ['agent']
    search_fields = ['first_name', 'last_name', 'email']

# Define the admin class for the Property model
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'agent']  # Fields to display in the list
    list_filter = [ 'agent']  # Add filters for category and agent
    search_fields = ['title', 'description']

admin.site.register(Salary)
admin.site.register(Sale)
admin.site.register(Category)
admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Lead, LeadAdmin)
admin.site.register(Agent)
admin.site.register(FollowUp)
admin.site.register(Property, PropertyAdmin)