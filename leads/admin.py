from django.contrib import admin
from .models import (User, Lead, Agent, UserProfile, Category, FollowUp, Salary, Sale,Project,Area,Typeplot,PlotBooking,Kisan,EMIPayment,
                     Property, Bonus, EmiPlan, Daybook, Promoter,Bill,BillItem)


admin.site.site_header = "Mateshwari Infrasolutions Pvt. Ltd."
admin.site.site_title = "Real Estate Management System"
admin.site.index_title = "Welcome to Admin Pannel"

class LeadAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'age', 'email']
    list_display_links = ['first_name']
    list_editable = ['last_name']
    list_filter = ['agent']
    search_fields = ['first_name', 'last_name', 'email']


class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'agent']
    list_filter = ['agent']
    search_fields = ['title', 'description']


# Admin class for Bonus model
class BonusAdmin(admin.ModelAdmin):
    list_display = ['agent', 'bonus_amount', 'date_awarded']
    search_fields = ['agent__username']
    list_filter = ['date_awarded']

# Admin class for EmiPlan model
class EmiPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'interest_rate', 'tenure_months', 'minimum_downpayment', 'created_at']
    list_filter = ['tenure_months', 'interest_rate']
    search_fields = ['name']

#Admin class for project model
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['project_name','block']
    # list_filter = ['project_name','block']

# #Admin class for level model
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level','interest']
    

# Admin class for Daybook model
class DaybookAdmin(admin.ModelAdmin):
    list_display = ['date', 'activity', 'amount', 'remark']
    list_filter = ['activity', 'date']
    search_fields = ['custom_activity', 'remark']


# Admin class for Promoter model
class PromoterAdmin(admin.ModelAdmin):
    list_display = ['name','mobile_number', 'department', 'status', 'joining_date', 'payment_date', 'salary', 'get_next_payment_date']
    list_filter = ['department', 'status', 'joining_date', 'payment_date']
    search_fields = ['name', 'email', 'mobile_number', 'department']
    ordering = ['name']
    date_hierarchy = 'joining_date'

    fieldsets = (
        ("Personal Information", {
            'fields': ('name', 'email', 'mobile_number', 'address')
        }),
        ("Employment Details", {
            'fields': ('department', 'joining_date', 'salary', 'payment_date', 'status')
        }),
    )


# Register models with admin
admin.site.register(Salary)
admin.site.register(Sale)
admin.site.register(Category)
admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Agent)
admin.site.register(Typeplot)
admin.site.register(Project)
admin.site.register(PlotBooking)
admin.site.register(FollowUp)
admin.site.register(Lead, LeadAdmin)
admin.site.register(Area)
admin.site.register(EMIPayment)
admin.site.register(BillItem)
admin.site.register(Bill)
admin.site.register(Kisan)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Bonus, BonusAdmin)
admin.site.register(EmiPlan, EmiPlanAdmin)
admin.site.register(Daybook, DaybookAdmin)
admin.site.register(Promoter, PromoterAdmin)