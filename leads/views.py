import logging
import datetime
from leads.models import models
from datetime import timedelta , date
from decimal import Decimal, InvalidOperation
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import F, Value, ExpressionWrapper, DecimalField
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View, generic
from django.views.generic import ListView, UpdateView, DeleteView

from leads.models import Lead, Agent, Category, FollowUp, Promoter, PlotBooking, Project, EMIPayment, Area, Typeplot
from agents.mixins import OrganisorAndLoginRequiredMixin
from leads.models import Property, Sale, Salary, Bonus, Kisan, UserProfile, Daybook,EMIPayment,Balance
from leads.forms import (
    LeadModelForm, 
    CustomUserCreationForm, 
    AssignAgentForm, 
    LeadCategoryUpdateForm,
    CategoryModelForm,
    FollowUpModelForm,
    SalaryForm,
    SaleForm,
    UserProfileForm,
    PromoterForm,
    PlotBookingForm,
    KisanForm,
    DaybookEntryForm,
    BalanceUpdateForm,
)




logger = logging.getLogger(__name__)


# CRUD+L - Create, Retrieve, Update and Delete + List



class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        # Save the new user
        user = form.save()
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("login")

def search_view(request):
    query = request.GET.get('q', '')

    # Searching in Property model (fields that exist)
    property_results = Property.objects.filter(
        Q(title__icontains=query) |
        Q(project_name__icontains=query) |
        Q(type__icontains=query)
    )

    # Searching in Agent model (existing fields)
    agent_results = Agent.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query) |
        Q(user__username__icontains=query)
    )

    # Searching in PlotBooking model (updated to use the correct field)
    plotbooking_results = PlotBooking.objects.filter(
        Q(name__icontains=query) |
        Q(project__title__icontains=query)  # Use project to access Property title
    )

    # Searching in Sale model
    sale_results = Sale.objects.filter(
        Q(property__title__icontains=query) |  # Assuming Property has a 'title' field
        Q(agent__username__icontains=query) |  # Searching by agent's username
        Q(sale_price__icontains=query) |       # Searching by sale price
        Q(sale_date__icontains=query)         # Searching by sale date
    )
    # Searching in Salary model
    salary_result = Salary.objects.filter(
        Q(agent__username__icontains=query) |
        Q(base_salary__icontains=query) |
        Q(bonus__icontains=query) |
        Q(payment_date__icontains=query)
    )

    kisan_results = Kisan.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(contact_number__icontains=query) |
        Q(khasra_number__icontains=query) |
        Q(address__icontains=query) |
        Q(land_address__icontains=query)
    )

    # Searching in UserProfile model (existing fields)
    userprofile_results = UserProfile.objects.filter(
        Q(full_name__icontains=query) |
        Q(email__icontains=query)
    )

   # Debugging output to check results
    print(f"Query: {query}")
    print(f"Property Results: {[str(prop) for prop in property_results]}")
    print(f"Agent Results: {[str(agent) for agent in agent_results]}")
    print(f"Plot Booking Results: {[str(booking) for booking in plotbooking_results]}")
    print(f"User Profile Results: {[str(profile) for profile in userprofile_results]}")
    print(f"Sales Result: {[str(sale) for sale in sale_results]}")
    print(f"Salary Result: {[str(salary) for salary in salary_result]}")


    context = {
        'query': query,
        'property_results': property_results,
        'agent_results': agent_results,
        'plotbooking_results': plotbooking_results,
        'userprofile_results': userprofile_results,
        'sale_results':sale_results,
        'salary_result':salary_result,
        "kisan_results": kisan_results
    }
    return render(request, 'leads/search_result.html', context) 


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated: 
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

def landing_page(request):
    return render(request, "landing.html")

@login_required
def user_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Redirect to a success page
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'leads/profile.html', {'form': form})

def update_profile(request):
    user_profile = request.user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            # Update the username and email in the User model if they have changed
            request.user.username = form.cleaned_data.get('username')
            request.user.email = form.cleaned_data.get('email')
            request.user.save()  # Save the User model changes
            return redirect('dashboard')  # Redirect to the profile URL name
    else:
        form = UserProfileForm(instance=user_profile)

    context = {
        'form': form,
        'user_profile': user_profile,
    }
    return render(request, 'leads/profile.html', context)

class DashboardView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        user = self.request.user

        # Total leads
        total_lead_count = Lead.objects.all().count()

        recent_buyers = PlotBooking.objects.order_by('-booking_date')[:5]  # Use the appropriate field for your criteria
        

        # Sales Report
        sales_data = PlotBooking.objects.values('booking_date').annotate(
            total_sale_price=Sum('Plot_price'),
            properties_sold=Count('id')
        ).order_by('booking_date')

        labels = [sale['booking_date'].strftime("%Y-%m-%d") for sale in sales_data]  # Format dates
        data = [sale['properties_sold'] for sale in sales_data]

        # Calculate total sales amount and total costs
        total_sales = PlotBooking.objects.aggregate(total=Sum('Plot_price'))['total'] or 0
        total_land_cost = Kisan.objects.aggregate(total=Sum('land_costing'))['total'] or 0
        total_development_cost = Kisan.objects.aggregate(total=Sum('development_costing'))['total'] or 0

        # Prepare profit data for the graph
        profit_data = []
        for sale in sales_data:
            profit = sale['total_sale_price'] - total_land_cost - total_development_cost
            profit_data.append(float(profit))  # Convert Decimal to float for JavaScript compatibility
 
        # Calculate total profit
        total_cost = total_land_cost + total_development_cost
        total_profit = total_sales - total_cost

        # Calculate total salary distributed
        total_salary_distributed = Salary.objects.filter(payment_date__gte=timezone.now().date() - timedelta(days=30)).aggregate(total=Sum('base_salary'))['total'] or 0

        # Salary distribution data for pie chart
        
        salary_distribution = [
            float(total_salary_distributed),  # Convert to float
            float(total_profit - total_salary_distributed),]  # Convert to float
        salaryDistribution_labels = ['Salary Distributed', 'Remaining Profit']

        # Debugging
        print("Labels:", labels)
        print("Total cost:" , total_cost)
        print("Sales Data:", sales_data)
        print("Total Sales:", total_sales)
        print("Total Land Cost:", total_land_cost)
        print("Total Development Cost:", total_development_cost)
        print("Profit Data:", profit_data)
        print("Total Profit:", total_profit)
        print("Total salary_distribution:", salary_distribution)
        print("Salary Distribution Data:", salary_distribution)
        print("Salary Distribution Labels:", salaryDistribution_labels)


        # Leads in last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        total_in_past30 = Lead.objects.filter(
            date_added__gte=thirty_days_ago
        ).count()

        converted_category = Category.objects.filter(name="Converted").first()
        converted_in_past30 = Lead.objects.filter(
            category=converted_category,
            converted_date__gte=thirty_days_ago
        ).count()

        context.update({
            'labels': labels,
            'data': data,
            'recent_buyers': recent_buyers,
            'profit_labels': labels,  # Reuse the same labels for profit
            'profit_data': profit_data,
            'total_lead_count': total_lead_count,
            'total_in_past30': total_in_past30,
            'converted_in_past30': converted_in_past30,
            'total_sales': total_sales,
            'total_cost': total_cost,
            'total_profit': total_profit,
            
            'salary_distribution': salary_distribution,
            'salaryDistribution_labels': salaryDistribution_labels,
            
        })
        return context

import logging
logger = logging.getLogger('app_errors')
logger.info("This is an informational message.")
    
class LeadListView(LoginRequiredMixin,generic.ListView):
    
    template_name = "leads/lead_list.html"
    context_object_name = "leads"

    def get_queryset(self):
        # Use logging in models or views


        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.filter(
                # organisation=user.userprofile, 
                agent__isnull=False
            ).select_related('agent')
        else:
            # Check if the user has an associated agent
            if hasattr(user, 'agent'):
                queryset = Lead.objects.filter(
                    # organisation=user.agent.organisation, 
                    # agent=user.agent
                ).select_related('agent')
            else:
                queryset = Lead.objects.none()
                 # Return an empty queryset if no agent exists

        return queryset
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(LeadListView, self).get_context_data(**kwargs)
        if user.is_organisor:
            queryset = Lead.objects.filter(agent__isnull=True)
            
            context["unassigned_leads"] = queryset  
           
        return context
    

def lead_list(request):
    leads = Lead.objects.select_related('agent').all()
    context = {
        "leads":leads
    }
    return render(request,"leads/lead_list.html",context)

def user_profile_view(request, user_id):
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    return render(request, 'leads/lead_detail.html', {
        'user_profile': user_profile  # Pass the specific user profile to the template
    })

class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            # filter for the agent that is logged in
            queryset = queryset.filter(agent__user=user)
        return queryset


def lead_detail(request, pk):
    lead = Lead.objects.get(id=pk)
    context = {
        "lead": lead
    }
    return render(request, "leads/lead_detail.html", context)


class LeadCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/lead_create.html"
    form_class = LeadModelForm

    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        lead = form.save(commit=False)
        lead.organisation = self.request.user.userprofile
        lead.save()
        # send_mail(
        #     subject="A lead has been created",
        #     message="Go to the site to see the new lead",
        #     from_email="test@test.com",
        #     recipient_list=["test2@test.com"]
        # )
        messages.success(self.request, "You have successfully created a lead")
        return super(LeadCreateView, self).form_valid(form)

 
def lead_create(request):
    if request.method == "POST":
        form = LeadModelForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('leads:lead-list')
    else:
        form = LeadModelForm()
    return render(request, 'leads/lead_form.html', {'form': form})


class LeadUpdateView(OrganisorAndLoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_update.html"
    form_class = LeadModelForm

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        return Lead.objects.filter(organisation=user.userprofile)

    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        form.save()
        messages.info(self.request, "You have successfully updated this lead")
        return super(LeadUpdateView, self).form_valid(form)


def lead_update(request, pk):
    lead = Lead.objects.get(id=pk)
    form = LeadModelForm(instance=lead)
    if request.method == "POST":
        form = LeadModelForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect("/leads")
    context = {
        "form": form,
        "lead": lead
    }
    return render(request, "leads/lead_update.html", context)


class LeadDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/lead_delete.html"

    def get_success_url(self):
        return reverse("leads:lead-list")

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        return Lead.objects.filter(organisation=user.userprofile)


def lead_delete(request, pk):
    lead = Lead.objects.get(id=pk)
    lead.delete()
    return redirect("/leads")


class AssignAgentView(OrganisorAndLoginRequiredMixin, generic.FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs
        
    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)


class CategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        user = self.request.user

        if user.is_organisor:
            queryset = Lead.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Lead.objects.filter(
                organisation=user.agent.organisation
            )

        context.update({
            "unassigned_lead_count": queryset.filter(category__isnull=True).count()
        })
        return context

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset
 

class CategoryCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/category_create.html"
    form_class = CategoryModelForm

    def get_success_url(self):
        return reverse("leads:category-list")

    def form_valid(self, form):
        category = form.save(commit=False)
        category.organisation = self.request.user.userprofile
        category.save()
        return super(CategoryCreateView, self).form_valid(form)


class CategoryUpdateView(OrganisorAndLoginRequiredMixin, generic.UpdateView):
    template_name = "leads/category_update.html"
    form_class = CategoryModelForm

    def get_success_url(self):
        return reverse("leads:category-list")

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset


class CategoryDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/category_delete.html"

    def get_success_url(self):
        return reverse("leads:category-list")

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset


class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            # filter for the agent that is logged in
            queryset = queryset.filter(agent__user=user)
        return queryset

    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.get_object().id})

    def form_valid(self, form):
        lead_before_update = self.get_object()
        instance = form.save(commit=False)
        converted_category = Category.objects.get(name="Converted")
        if form.cleaned_data["category"] == converted_category:
            # update the date at which this lead was converted
            if lead_before_update.category != converted_category:
                # this lead has now been converted
                instance.converted_date = datetime.datetime.now()
        instance.save()
        return super(LeadCategoryUpdateView, self).form_valid(form)


class FollowUpCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "leads/followup_create.html"
    form_class = FollowUpModelForm

    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super(FollowUpCreateView, self).get_context_data(**kwargs)
        context.update({
            "lead": Lead.objects.get(pk=self.kwargs["pk"])
        })
        return context

    def form_valid(self, form):
        lead = Lead.objects.get(pk=self.kwargs["pk"])
        followup = form.save(commit=False)
        followup.lead = lead
        followup.save()
        return super(FollowUpCreateView, self).form_valid(form)

class FollowupList(LoginRequiredMixin,generic.ListView):
    
    template_name = "leads/followup_list.html"
    context_object_name = "followups"
    

    def get_queryset(self):
        user = self.request.user
        # Define the initial queryset based on user type
        if user.is_organisor:
            return FollowUp.objects.filter(lead__organisation=user.userprofile)
        else:
            return FollowUp.objects.filter(
                lead__organisation=user.agent.organisation,
                lead__agent__user=user
            )
    

def followup_list(request,lead_id):
    followups = FollowUp.objects.all(lead_id=lead_id)
    context = {
        "followups":followups
    }
    print(followups)
    return render(request,"leads/followup_list.html",context)

class FollowUpUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/followup_update.html"
    form_class = FollowUpModelForm

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = FollowUp.objects.filter(lead__organisation=user.userprofile)
        else:
            queryset = FollowUp.objects.filter(lead__organisation=user.agent.organisation)
            # filter for the agent that is logged in
            queryset = queryset.filter(lead__agent__user=user)
        return queryset

    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.get_object().lead.id})


class FollowUpDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/followup_delete.html"

    def get_success_url(self):
        followup = FollowUp.objects.get(id=self.kwargs["pk"])
        return reverse("leads:lead-detail", kwargs={"pk": followup.lead.pk})

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = FollowUp.objects.filter(lead__organisation=user.userprofile)
        else:
            queryset = FollowUp.objects.filter(lead__organisation=user.agent.organisation)
            # filter for the agent that is logged in
            queryset = queryset.filter(lead__agent__user=user)
        return queryset

class LeadJsonView(generic.View):

    def get(self, request, *args, **kwargs):
        
        qs = list(Lead.objects.all().values(
            "first_name", 
            "last_name", 
            "age")
        )

        return JsonResponse({
            "qs": qs,
        })
    

def create_salary(request):
    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            form.save()
            
            messages.success(request, "Salary Info Added.")
            return redirect('leads:salary_list')  # Redirect to a salary list view
    else:
        form = SalaryForm()
    return render(request, 'salary/create_salary.html', {'form': form})

def manage_salary(request, salary_id=None):
    if salary_id:  # Check if we are updating an existing salary
        salary = get_object_or_404(Salary, id=salary_id)
    else:
        salary = None

    if request.method == 'POST':
        if 'delete' in request.POST:  # Check if delete button was pressed
            salary.delete()  # Delete the salary instance
            messages.success(request, "Salary deleted successfully.")
            return redirect('leads:salary_list')  # Redirect after deletion
        else:
            form = SalaryForm(request.POST, instance=salary)  # Bind the form to the instance if updating
            if form.is_valid():
                form.save()  # Save the salary instance
                messages.success(request, "Salary updated successfully.")
                return redirect('leads:salary_list')  # Redirect after saving
    else:
        form = SalaryForm(instance=salary)  # Create form with instance if updating

    return render(request, 'salary/manage_salary.html', {'form': form, 'salary': salary})

def create_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sale added successfully.")
            return redirect('leads:sale_list')  # Redirect to a sale list view
    else:
        form = SaleForm()  # Instantiate an empty form
    return render(request, 'sale/create_sale.html', {'form': form})

def manage_sale(request, sale_id=None):
    # If sale_id is provided, fetch the sale; otherwise, it's a new sale
    sale = get_object_or_404(Sale, id=sale_id) if sale_id else None

    if request.method == 'POST':
        if 'delete' in request.POST:  # Check if the delete button was pressed
            if sale:  # Ensure the sale exists
                sale.delete()  # Delete the sale instance
                messages.success(request, "Sale deleted successfully.")
                return redirect('leads:sale_list')  # Redirect after deletion
        else:  # If not a delete request, process form submission
            form = SaleForm(request.POST, instance=sale)  # Bind form to instance if updating
            if form.is_valid():
                form.save()  # Save the sale instance
                messages.success(request, "Sale updated successfully.")
                return redirect('leads:sale_list')  # Redirect after saving
    else:
        form = SaleForm(instance=sale) if sale else SaleForm()  # Create form with instance if updating

    return render(request, 'sale/manage_sale.html', {'form': form, 'sale': sale})

  

class PropertyListView(LoginRequiredMixin, ListView):
    model = Property
    template_name = 'property/property_list.html'  # Update with your template path
    context_object_name = 'properties'

    def get_queryset(self):
        properties = Property.objects.all()
        for property in properties:
            print(f"Property ID: {property.id}, Title: {property.title}, is_in_emi: {property.is_in_emi}")
        return properties
        
    
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        
        # Fetch all properties
        properties = Property.objects.all()

        # Fetch all projects and add them to context
        context['projects'] = Project.objects.all()

        # Calculate total Kisan land
        total_kisan_land = Kisan.objects.aggregate(total_land=Sum('usable_land_total')).get('total_land', 0)
        total_land = total_kisan_land or 0  # Default to 0 if None
        print(total_land)

        # Calculate total area used in properties
        total_area_used = sum(property.area for property in properties if property.area)
        print(total_area_used)
        # Calculate available land
        available_land = Decimal(total_land) - Decimal(total_area_used)

        # Add available land information to context
        context['total_land'] = total_land  # Correctly setting values in context
        context['available_land'] = available_land
        return context


class PropertyDetailView(generic.DetailView):
    model = Property
    template_name = 'property/property_detail.html'
    context_object_name = 'property'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property = self.get_object()

        cost_p_sqft = property.price
        # Fetch related PlotBooking for the specific property
        plot_booking = PlotBooking.objects.filter(project=property).first()
        salarys = Salary.objects.filter(property = property)
        print(salarys)
        tot_sal = sum(salary.base_salary for salary in salarys)

        # Initialize variables for overall calculations
        total_area_in_beegha = 0
        total_land_cost = 0
        total_development_cost = 0
        total_plot_price = 0

        # Calculate overall land costs and development costs from Kisan data
        idr = property.project_id
        print(idr)
        ids = idr.id
        projectused = Project.objects.get(id= ids) 
        lands = projectused.lands.all()
        print(lands)
        total_land_cost = sum( land.land_costing for land in lands)
        print(total_land_cost)
        total_development_cost = projectused.dev_cost*projectused.total_land_available_fr_plotting

        kisan_data = Kisan.objects.filter(is_assigned=True) # Only Used land taken

        total_cost = total_land_cost+total_development_cost
        total_land = projectused.total_land_available_fr_plotting
        cost_psqft = (total_cost/total_land)
        cost_for_land = cost_psqft*(property.area)
        
        for kisan in kisan_data:
            total_area_in_beegha += kisan.area_in_beegha

        buyer_data = PlotBooking.objects.all()
        total_plot_price = sum(plotbooking.Plot_price for plotbooking in buyer_data)
        print(total_plot_price)

        final_pr = property.totalprice - cost_for_land - tot_sal 

#Update context with all relevant details
        context.update({
            'property': property,
            'total_plot_price_of_prop': cost_for_land,
            'total_plot_price_of_pro': property.totalprice,
            'plot_booking': plot_booking,
            'total_land_cost': total_land_cost,
            'total_development_cost': total_development_cost,
            'agent': salarys,
            'tot_sal': tot_sal,
            'final_pr': final_pr,
            'profit_per_sqft': cost_p_sqft - cost_psqft ,
            'cost_per_sqft':cost_psqft ,
            'total_profit_per_sqft':property.totalprice - cost_for_land,
        })

        return context
        
        

# Function-based view to display properties
def properties_view(request):
    properties = Property.objects.all()  # Fetch all properties
    context = {
        'properties': properties,
    }
    return render(request, 'leads/properties_list.html', context)  # Ensure this path is correct

        

class ProjectCreateView(LoginRequiredMixin, View):
    model = Project,Area,Kisan
    template_name = 'property/create_project.html'


    def get(self, request):
        available_lands = Kisan.objects.filter(is_assigned=False)
        # Render the initial form for number of properties and common attributes
        return render(request, self.template_name, {'available_lands': available_lands})


    def post(self, request):
        # Get the number of properties to create and common attributes
        project_name = request.POST.get('project_name', )
        block = request.POST.get('block', '')
        dev_cost = int(request.POST.get('dev_cost', ''))
        selected_land_ids = request.POST.getlist('lands')  # List of selected Kisan IDs
        projectTypeSelect = request.POST.get('projectTypeSelect')  # List of selected project type

        if not selected_land_ids:
            messages.error(request, 'Please select at least one land plot for the project.')
            return redirect('leads:property-create')  # Replace with your create project URL name

        # Calculate total area and costs for selected lands
        selected_lands = Kisan.objects.filter(id__in=selected_land_ids, is_assigned=False)
        if not selected_lands.exists():
            messages.error(request, 'Selected lands are not available.')
            return redirect('leads:property-create')
        
        # Aggregate costs
        total_area = sum(land.area_in_beegha for land in selected_lands)
        print(total_area)
        # total_development_cost = sum(land.development_costing for land in selected_lands)
        area = float(total_area*27200)
        if projectTypeSelect == "Flat":
            tarea= area*0.6
        else:
            tarea= area*0.7

        try:
            # Assuming you have a Project model
            project=Project.objects.create(
                project_name=project_name,
                block=block,  # Example size, modify as needed
                dev_cost=dev_cost,  # Example size, modify as needed
                type =projectTypeSelect,
                total_land_available_fr_plotting = tarea
            )
            project.lands.set(selected_lands)  # Link selected lands to the project
            selected_lands.update(is_assigned=True)  # Mark lands as assigned

            messages.success(request, 'Project created successfully!')
        except IntegrityError:
            # Catch the unique constraint error and send a message to the user
            messages.error(request, 'A project with this name already exists!')
        

        return redirect(self.get_success_url())

        
    def get_success_url(self):
        return reverse('leads:property-create')
    

from leads.forms import PropertyModelForm   
  
class PropertyCreateView(LoginRequiredMixin, View):
    template_name = 'property/property_create.html'

    # In the get method, calculate available land and add it to the context
    def get(self, request):
        projects = Project.objects.all()
        areas = Area.objects.all()
        types = Typeplot.objects.all()
        properties = Property.objects.all()
        # Passing the choices to the template
        plot_choices = Property.PLOT_CHOICES

        for project in projects:
            project.total_land_area = Property.objects.filter(project_id=project).aggregate(total_area=Sum('area'))['total_area'] or 0
            tla = project.total_land_area
            project.total_land_available = project.total_land_available_fr_plotting - tla
            project.cost_per_sqft = project.dev_cost
            kisan_lands = project.lands.all()
            # total_area = sum(land.area_in_beegha*27200 for land in kisan_lands)
            total_land_cost =  sum(land.land_costing for land in kisan_lands)
            project.land_cost_per_sqft = total_land_cost/project.total_land_available + project.dev_cost

        # Pass available_land in context
        return render(request, self.template_name, {
            'projects': projects,
            'areas': areas,
            'types': types, # New addition
            'properties': properties, # New addition
            "plot_choices": plot_choices,     
            })


    def post(self, request):
        # Get the number of properties to create and common attributes
        num_properties = int(request.POST.get('num_properties', 1))
        price = int(request.POST.get('price', ''))
        type = request.POST.get('type', '')
        ptype = request.POST.get('plot_type', '')
        dimension = request.POST.get('dimension', '')
        key = int(request.POST.get('project_id', ''))
        # Fetch the Project instance using `get_object_or_404`
        project = Project.objects.get(id=key)
        project.total_land = Property.objects.filter(project_id=project).aggregate(total_area=Sum('area'))['total_area'] or 0
        tla = project.total_land
        project.total_land_available = project.total_land_available_fr_plotting - tla
        available_land =  project.total_land_available



        form = PropertyModelForm(request.POST, total_land=available_land)

        # Split the string using '*' as the separator
        if dimension == 'others':
            l = int(request.POST.get('length'))
            b = int(request.POST.get('breadth'))
            area = float(l) * float(b)
            Area.objects.create(
            length = l,
            breadth = b
            )

        else:
            len, bre = dimension.split('*')
            l = int(len)
            b = int(bre)
            area = l* b

        if type == 'others':
            newtype = request.POST.get('new_type')
            Typeplot.objects.create(
                type = newtype
            )
            type = newtype

        
        tp = (l*b*price)
        project_nam= project.project_name
        blocks = project.block
#
        total_area_needed = area * num_properties
            
        if total_area_needed > available_land:
            error_message = f"Only {available_land} sqft of land is available. Cannot create {total_area_needed} sqft of property."
            print(error_message)
            return render(request, self.template_name, {'projects': Project.objects.all(), 'areas': Area.objects.all(), 'types': Typeplot.objects.all(), 'error_message': error_message, 'form': form})

        # Create the properties in the database
        for _ in range(num_properties):
            Property.objects.create(
                project_id = project , # Example size, modify as needed
                project_name = project_nam ,
                block = blocks ,
                plot_type = ptype ,
                price=price , # Example price, modify as needed
                type=type,  # Example price, modify as needed
                area=area,  # Example price, modify as needed
                breadth=b,  # Example price, modify as needed
                length=l,  # Example price, modify as needed
                totalprice=tp,  # Example price, modify as needed
            )

        return redirect(self.get_success_url())
        

    def get_success_url(self):
        return reverse('leads:property_list')  # Redirect to property list after creation  # Redirect to property list after successful update  # Redirect to property list after creation  # Redirect to property list after successful update

def select_properties_view(request):
    projects = Project.objects.all()
    properties = Property.objects.all()

    if request.method == 'POST':
        selected_ids = request.POST.getlist('properties')  # Get list of selected IDs
        print (selected_ids)  # Print selected IDs for debugging
        x= 0 
        if selected_ids:
            test  = selected_ids[0]
            prop = Property.objects.get(id=test)
            pr_id = prop.project_id

            for prop_id in selected_ids:
                property_in = Property.objects.get(id=prop_id)
                property_title = property_in.project_id
                if  property_title == pr_id:
                    x = 1
                else:
                    x = 0
                    break
        else:
            # message to raise when no property selected
            error_message = "Select at least one property to update."
            print(error_message)
            return render(request, 'property/select_properties.html', {'projects': projects,'properties': properties,
                'error_message': error_message})
    
        if x==0:
            error_message = "You have selected multiple properties from Different Project"
            print(error_message)
            return render(request, 'property/select_properties.html', {
            'projects': projects,
            'properties': properties,
            'error_message':error_message
            })
        else:
            # Redirect to the update view with the selected IDs
            return redirect('leads:property-update', ids=','.join(selected_ids))  # Join IDs as a comma-separated string


    return render(request, 'property/select_properties.html', {
        'projects': projects,
        'properties': properties
    })

def get_properties_by_project(request, project_id):
    properties = Property.objects.filter(project_id=project_id)  # Correct usage
    properties_data = [{'id': prop.id, 'project_name': prop.property_name} for prop in properties]

    return JsonResponse({'properties': properties_data})

# View to edit selected properties
class PropertyUpdateView(LoginRequiredMixin,View):
    template_name = 'property/property_update.html'

    def get_project_and_properties(self, ids):
        # Split the comma-separated list of property IDs
        property_ids = ids.split(',')
        properties = Property.objects.filter(id__in=property_ids)
        plot_choices = Property.PLOT_CHOICES
        if not properties.exists():
            return None, None  # Handle if no properties are found
        
        # Assume the first property's project ID is relevant for all properties
        project_id = properties[0].project_id.id
        project = Project.objects.get(id=project_id)

        # Calculate total land area and available land
        project.total_land_area = Property.objects.filter(project_id=project).aggregate(total_area=Sum('area'))['total_area'] or 0
        area_in_selected_properties = sum(prop.area for prop in properties)
        project.available_land = project.total_land_available_fr_plotting - project.total_land_area + area_in_selected_properties

        return project, properties

    def get(self, request, ids):
        plot_choices = Property.PLOT_CHOICES
        project, properties = self.get_project_and_properties(ids)
        if project is None or properties is None:
            return redirect('error_page')  # Redirect to an error page if data is missing

        return render(request, self.template_name, {'properties': properties, 'project': project,'plot_choices':plot_choices})

    def post(self, request, ids):
        # Retrieve project and properties using helper method
        project, properties = self.get_project_and_properties(ids)
        if project is None or properties is None:
            return redirect('error_page')

        # Get form values
        count = len(properties)
        length = int(request.POST.get('project_name', ''))
        price = request.POST.get('price', '')
        breadth = int(request.POST.get('block', ''))
        update_type = request.POST.get('plot_type', '')
        # Calculate required area
        required_area = length * breadth * count

        # Check if available land is sufficient
        if required_area > project.available_land:
            return self.get(request, ids)  # Re-render `get` view if there's not enough land

        # Update properties if sufficient land is available
        for property_instance in properties:
            property_instance.length = length
            property_instance.price = float(price)
            property_instance.breadth = breadth
            property_instance.area = breadth*length
            property_instance.plot_type = update_type
            property_instance.save()

        return redirect(self.get_success_url())









    def get_success_url(self):
        return reverse('leads:property_list')

   
class PropertyDeleteView(LoginRequiredMixin,View):
    def post(self, request, ids):
        property_ids = ids.split(',')  # Convert the comma-separated string back to a list

        for prop_id in property_ids:
            property_instance = get_object_or_404(Property, id=prop_id)
            property_instance.delete()  # Delete the property

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('leads:property_list')


class SaleListView(LoginRequiredMixin,ListView):
    model = Sale
    template_name = 'sale/sale_list.html'  # Update with your template path
    context_object_name = 'sales'

class SalaryListView(LoginRequiredMixin,ListView):
    model = Salary
    template_name = 'salary/salary_list.html'  # Update with your template path
    context_object_name = 'salaries'

    def get_queryset(self):
        # Annotate the queryset with the total compensation calculation
        queryset =  Salary.objects.annotate(
            total_compensation=ExpressionWrapper(
                F('base_salary') + Value(0) + F('bonus') + F('commission'),  # Adjusted for potential None values
                output_field=DecimalField()
            )
        )
   

        payment_date = self.request.GET.get('payment_date')
        if payment_date:
            # Filter salaries based on the selected payment date
            queryset = queryset.filter(payment_date=payment_date)

        # Ensure that only agents with salaries on that date are shown
        return queryset.order_by('-payment_date', '-id') # Show the latest payments first
    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('salary/salary_list.html', context)
            
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)



class BonusInfoView(LoginRequiredMixin,ListView):
    model = Bonus
    template_name = 'leads/bonus_info.html'  # Update with your template path
    context_object_name = 'bonuses'




# EMI

def calculate_emi(request):
    emi = None  # Initialize emi variable
    error_message = None  # Initialize error message variable
    if request.method == "POST":
        try:
            # Retrieve input values and convert to Decimal
            total_amount = Decimal(request.POST.get('total_amount', '0'))  # Default to 0 if not provided
            down_payment = Decimal(request.POST.get('down_payment', '0'))  # Default to 0 if not provided
            interest_rate = Decimal(request.POST.get('interest_rate', '0'))  # Default to 0 if not provided
            tenure = request.POST.get('tenure', '0')

            # Validate input values
            if total_amount < 0 or down_payment < 0 or interest_rate < 0:
                error_message = "Please provide valid positive numbers for Total Amount, Down Payment, and Interest Rate."
            else:
                # Custom tenure handling
                if tenure == 'other':
                    custom_tenure = request.POST.get('custom_tenure', '0')
                    if custom_tenure:
                        custom_tenure = Decimal(custom_tenure)
                        if custom_tenure <= 0:
                            error_message = "Please enter a valid number of months."
                        else:
                            tenure = custom_tenure
                    else:
                        error_message = "Please enter a custom number of months."
                else:
                    tenure = Decimal(tenure)

                # Calculate loan amount
                loan_amount = total_amount - down_payment

                # Check if loan amount is positive
                if loan_amount < 0:
                    error_message = "Loan amount must be positive (Total Amount should be greater than Down Payment)."
                else:
                    # Convert interest rate from percentage to a decimal
                    monthly_interest_rate = interest_rate / Decimal(100) / Decimal(12)

                    # EMI calculation using the formula
                    if monthly_interest_rate > 0:
                        emi = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** tenure) / \
                              ((1 + monthly_interest_rate) ** tenure - 1)
                    else:
                        emi = loan_amount / tenure  # In case interest rate is 0, simple division

                    # Set precision for Decimal calculations
                    emi = emi.quantize(Decimal('0.001'))  # Round to three decimal places

        except InvalidOperation as e:
            error_message = f"Error in calculation: {str(e)}"
        except ValueError as e:
            error_message = f"Value error: {str(e)}"
        except ZeroDivisionError as e:
            error_message = "Error: Division by zero."

    return render(request, 'EMI/emi_calculation.html', {'emi': emi, 'error_message': error_message})

# DAYBOOK
class DaybookCreateView(LoginRequiredMixin, View):
    template_name = 'Daybook/daybook_form.html'

    def get(self, request, *args, **kwargs):
        form = DaybookEntryForm()
        return render(request, self.template_name, {'form': form, 'today': timezone.now().date()})

    def post(self, request, *args, **kwargs):
        form = DaybookEntryForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            print("expenese is", expense)
            balance = Balance.objects.first()
            print("balance is", balance)
            
            # Check if balance is available
            if balance:
                if balance.amount >= expense.amount:
                    # Deduct from balance as it's within the daily limit
                    balance.amount -= expense.amount
                else:
                    # If expense exceeds the daily limit, return an error message
                    messages.error(request, "Daily limit reached. Expense exceeds available balance.")
                    return render(request, self.template_name, {'form': form, 'today': timezone.now().date()})
            else:
                # No balance record exists, create one with negative amount if overspending
                Balance.objects.create(amount=-expense.amount)

            # Save the expense and update balance
            expense.save()
            balance.save()

            return redirect('leads:daybook_list')
        return render(request, self.template_name, {'form': form, 'today': timezone.now().date()})

class DaybookListView(LoginRequiredMixin, View):
    template_name = 'Daybook/daybook_list.html'

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        
        # Fetch today's and total expenses
        todays_expenses = Daybook.objects.filter(date=today)
        print("todays expense is ",todays_expenses)
        total_todays_expenses = sum(expense.amount for expense in todays_expenses)
        print("total expens of today",total_todays_expenses)
        total_expenses = Daybook.objects.aggregate(total_amount=models.Sum('amount'))['total_amount'] or 0
        print("total expense is",total_expenses)
        # Retrieve current balance and carryover amount
        current_balance_record = Balance.objects.first()
        print("current balance record",current_balance_record)
        current_balance = current_balance_record.amount if current_balance_record else 0
        print("current balance",current_balance)
        carryover_amount = current_balance_record.carryover_amount if current_balance_record else 0
        print("carryover amount is ",carryover_amount)


        # Calculate carryover for next day
        remaining_balance = current_balance - total_todays_expenses
        if remaining_balance > 0:
            carryover_amount += remaining_balance
            print("remaining carryover is ",carryover_amount)
        else:
            carryover_amount = max(0, carryover_amount + remaining_balance)
            print("remaining carryover 2 is ",carryover_amount)

        context = {
            'expenses': todays_expenses,
            'total_balance': current_balance,
            'carryover_amount': carryover_amount,
            'todays_expense': total_todays_expenses,
            'total_expenses': total_expenses,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if 'reset_expenses' in request.POST:
            Daybook.objects.all().delete()
            Balance.objects.all().delete()
            return redirect('leads:daybook_list')


class BalanceUpdateView(LoginRequiredMixin, View):
    template_name = 'Daybook/update_balance.html'

    def get(self, request, *args, **kwargs):
        form = BalanceUpdateForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = BalanceUpdateForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            action = form.cleaned_data['action']
            balance, created = Balance.objects.get_or_create(pk=1)

            if action == 'add':
                balance.amount += amount
                print("Add",balance.amount)
            elif action == 'deduct':
                balance.amount = max(0, balance.amount - amount)
                print("deduct",balance.amount)

            balance.save()
            return redirect('leads:daybook_list')
        return render(request, self.template_name, {'form': form})

# PROMOTER 

class PromoterListView(LoginRequiredMixin, ListView):
    model = Promoter
    template_name = 'promoter/promoter_list.html'
    context_object_name = 'promoters'

def update_delete_promoter(request, promoter_id):
    promoter = get_object_or_404(Promoter, id=promoter_id)

    if request.method == 'POST':
        if 'update' in request.POST:  # Handle update request
            form = PromoterForm(request.POST, instance=promoter)
            if form.is_valid():
                form.save()
                return redirect('leads:promoter_list')  # Ensure this redirects to the correct URL
        elif 'delete' in request.POST:  # Handle delete request
            promoter.delete()
            return redirect('leads:promoter_list')  # Ensure this redirects to the correct URL

    else:
        form = PromoterForm(instance=promoter)

    return render(request, 'promoter/update_delete_promoter.html', {'form': form, 'promoter': promoter})

def add_promoter(request):
    if request.method == 'POST':
        form = PromoterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leads:promoter_list')  # Redirect to the promoter list after adding
    else:
        form = PromoterForm()

    return render(request, 'promoter/add_promoter.html', {'form': form})



# PLOT REGISTRATION

class PlotRegistrationView(LoginRequiredMixin, View):
    template_name = 'plot_registration/plot_registration.html'

    def get(self, request, *args, **kwargs):
        form = PlotBookingForm()
        agents = Agent.objects.all()
        properties = list(Property.objects.values('id', 'totalprice', 'project_name'))  # Fetch only necessary fields
        print("get")
        properties = [
        {
            'id': prop['id'],
            'price': str(prop['totalprice']),  # Convert Decimal to string
            'project_name': prop['project_name']
        }
        for prop in properties
]

        
        return render(request, self.template_name, {'form': form, 'agents': agents,'properties':properties})

    def post(self, request, *args, **kwargs):
        form = PlotBookingForm(request.POST)
        agents = Agent.objects.all()
        print("post")
        

        if form.is_valid():
            print("help")
            # Retrieve EMI amount and tenure from the form
            emi_amount = form.cleaned_data.get('emi_amount')
            tenure = form.cleaned_data.get('emi_tenure')
            project = form.cleaned_data.get('project')
            Property_inst = Property.objects.get(id = project.id)
            Plot_price = Property_inst.totalprice
            form.instance.Plot_price = Property_inst.totalprice  
            form.save()
            agent = form.cleaned_data.get('agent')
            payment_type = form.cleaned_data.get('payment_type')  # Get the payment type
            print(agent)
            if agent:
                agent_level = agent.level
                print(agent_level)
                for i in range(1,agent_level+1):
                    if i == 1:
                        base_salary = int(Plot_price)/10
                    elif i == 2:
                        base_salary = int(Plot_price)/25
                    elif i == 3:
                        base_salary = int(Plot_price)*3/100
                    elif i == 4:
                        base_salary = int(Plot_price)/50
                    elif i == 5:
                        base_salary = int(Plot_price)/100

                    prop = Property.objects.get(title=project)
                    Salary.objects.create(
                        agent = agent.user,
                        base_salary=base_salary,
                        bonus = 0,
                        payment_date=date.today(),  # Adds the current date to payment_date
                        property=prop
                    )
                    print(property)
                    agent=agent.parent_agent


            prop =  Property.objects.get(title=project)
            print(prop)
            print(prop.is_sold)
            prop.is_sold=True
            # Check if the payment type is "installment" and set is_in_emi accordingly
            if payment_type == 'installment':
                print(payment_type)
                prop.is_in_emi = True
            else:
                prop.is_in_emi = False
            prop.save()  # Save the updated property
            
            print(prop.is_sold)
            plot_booking = form.save()
            # Ensure emi_amount is a Decimal and tenure is an integer
            if emi_amount is not None and tenure is not None and tenure > 0:
                monthly_emi = emi_amount / tenure  # EMI per month
                
                # Generate EMI payment records
                for month in range(tenure):
                    due_date = plot_booking.payment_date + timedelta(days=30 * month)
                    EMIPayment.objects.create(
                        plot_booking=plot_booking,
                        due_date=due_date,
                        emi_amount=monthly_emi  # Store calculated EMI
                    )
            elif emi_amount is None and tenure is None:
                # Handle missing or invalid EMI amount or tenure
                form.add_error(None, 'Invalid EMI amount or tenure.')

            return redirect('plot_registration/buyers_list')  # Ensure this matches your URL configuration
        else:
            print(form.errors)
            messages.error(request, 'A buyer with this project already exists!')

            #return redirect('plot_registration/buyers_list.html')
            return render(request, self.template_name, {'form': form, 'agents': agents})

def load_properties(request):
    project_name = request.GET.get('property.title')
    properties = Property.objects.filter(project_name_id=project_name).values('id', 'property.title')
    return JsonResponse(list(properties), safe=False)

class BuyersListView(LoginRequiredMixin, View):
    template_name = 'plot_registration/buyers_list.html'

    def get(self, request, *args, **kwargs):
        buyers = PlotBooking.objects.select_related('agent').all().order_by('-booking_date')
        return render(request, self.template_name, {'buyers': buyers})


def generate_receipt_number():
 
    # Generate a unique receipt number using the current date and time
    current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
  
    return f"REC-{current_time}"  # Receipt number with prefix 'REC-'


def buyer_print_view(request, buyer_id):
    # Fetch the buyer instance or return a 404 error if not found
    buyer = get_object_or_404(PlotBooking, id=buyer_id)
   
    # Generate a unique receipt number
    receipt_number = generate_receipt_number()
    
    # Prepare the context for rendering the template
    context = {
        'buyer': buyer,
        'receipt_date': timezone.now(),  # Get the current date and time
        'receipt_number': receipt_number,  # Add the generated receipt number to the context
    }
    
    # Render the template with the context
    return render(request, 'plot_registration/buyer_print_template.html', context)

@login_required
def update_delete_buyer(request, id):
    plot_booking = get_object_or_404(PlotBooking, id=id)
    print(plot_booking.project)
    pdid = plot_booking.project
    pd =  Property.objects.get(title=pdid)


    if request.method == 'POST':
        if 'update' in request.POST:
            form = PlotBookingForm(request.POST, instance=plot_booking)
            if form.is_valid():
                print(form.is_valid())
                form.save()
                pd.is_sold=False
                pd.save()
                project = form.cleaned_data.get('project')
                agent = form.cleaned_data.get('agent')
                print(agent)
                prop =  Property.objects.get(title=project)
                print(prop.is_sold)
                prop.is_sold=True
                prop.save()
                print(prop.is_sold)
                return redirect('leads:buyers_list')  # Redirect after updating
            else:
                messages.error(request, 'A buyer with this project already exists!')

        elif 'delete' in request.POST:
            plot_booking.delete()
            pd.is_sold=False
            pd.save()
            return redirect('leads:buyers_list')  # Redirect after deleting
    else:
        form = PlotBookingForm(instance=plot_booking)  # Pre-fill the form with the existing data

    agents = Agent.objects.all()
    return render(request, 'plot_registration/update_delete_buyer.html', {'form': form, 'agents': agents})

def buyer_detail_view(request, buyer_id):
    buyer = get_object_or_404(PlotBooking, id=buyer_id)
    emi_payments = buyer.emi_payments.all()  # Fetch EMI payments linked to this buyer

    context = {
        'buyer': buyer,
        'emi_payments': emi_payments,  # Pass the EMI payments to the template
    }
    return render(request, 'plot_registration/buyer_detail.html', context)

def mark_as_paid(request, payment_id):
    payment = get_object_or_404(EMIPayment, id=payment_id)  # Fetch the EMI payment record
    if payment.status == 'Pending':
        payment.pay_emi(payment.emi_amount)  # Pay the full EMI amount
    return redirect('leads:buyer_detail', buyer_id=payment.plot_booking.id)

def pay_emi(request, payment_id):
    if request.method == 'POST':
        payment = get_object_or_404(EMIPayment, id=payment_id)

        if payment.status == 'Pending':
            payment.status = 'Paid'
            payment.save()
            plotbooking = payment.plot_booking
            x = False 
            p = EMIPayment.objects.filter(plot_booking = plotbooking)
            for allemi in p:
                if allemi.status == "Paid":
                    x = True
                else:
                    x= False
                    break

            if x == True:
                prop_paid = plotbooking.project
                print(prop_paid.is_in_emi)
                prop_paid.is_in_emi = False
                prop_paid.save()
                print(prop_paid.is_in_emi)

                print(prop_paid)
            
            return JsonResponse({'status': 'success', 'message': 'Payment marked as paid.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


class GetProjectPriceView(View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        try:
            # Fetch properties related to the selected project
            properties = Property.objects.filter(project_id=project_id)
            if properties.exists():
                # Assuming you want the price of the first property; adjust if needed
                total_price = properties.first().totalprice
                return JsonResponse({'price': total_price})
            else:
                return JsonResponse({'error': 'No properties found for this project.'})
        except Exception as e:
            return JsonResponse({'error': str(e)})

# View for creating Kisan

def kisan_view(request, pk=None):
    try:
        if pk:  # Editing an existing Kisan
            kisan = Kisan.objects.get(pk=pk)
            form = KisanForm(request.POST or None, instance=kisan)
            if request.method == 'POST':
                if form.is_valid():
                    form.save()
                    return redirect('kisan_list')  # Redirect to the Kisan list
        else:  # Creating a new Kisan
            form = KisanForm(request.POST or None)
            if request.method == 'POST':
                if form.is_valid():
                    print("save")
                    form.save()
                    return redirect('leads:kisan_list')  # Redirect to the Kisan list

        return render(request, 'kisan/kisan_form.html', {'form': form, 'kisan': kisan if pk else None})
    except Exception as e:
        print(f"Error occurred: {e}")
        return render(request, 'kisan/kisan_update.html', {'form': form, 'error': str(e)})


# View for listing Kisan

class KisanListView(LoginRequiredMixin, ListView):
    model = Kisan
    template_name = 'kisan/kisan_list.html'
    context_object_name = 'kisans'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate total available land
        total_available_land = (
            Kisan.objects.filter(is_sold=False)
            .aggregate(total_area=Sum('area_in_beegha'))
            .get('total_area', 0)
        )
        total_available_land = total_available_land or 0  # Default to 0 if None

        # Total land in sqft
        total_land_in_sqft = total_available_land * 27200
        context['total_land_in_sqft'] = total_land_in_sqft

        # Calculate usable land based on land type
        usable_land_total = 0
        for kisan in Kisan.objects.filter(is_sold=False):
            area_in_beegha = kisan.area_in_beegha  # Get the area in beegha
            area_in_sqft = area_in_beegha * 27200  # Convert beegha to sqft
            land_type = kisan.land_type.lower()  # Ensure it is in lowercase for comparison

            # Determine development percentage based on land type
            if land_type in ['plot', 'rowhouse']:
                development_percentage = Decimal('0.30')  # 30% for plot or rowhouse
            elif land_type == 'flat':
                development_percentage = Decimal('0.40')  # 40% for flat
            else:
                development_percentage = Decimal('0')  # No development if land type is different

            # Calculate usable land
            usable_land = area_in_sqft * (1 - development_percentage)
            print(usable_land)
            usable_land_total += usable_land
            print(usable_land_total)
            print(f"Area in sqft: {area_in_sqft}, Development Percentage: {development_percentage}")
            print(f"Processing record ID: {kisan.id}")

            kisan.usable_land_total = usable_land
            kisan.save() 


        context['usable_land_total'] = usable_land_total

        return context

class KisanUpdateView(UpdateView):

    model = Kisan
    fields = [
        'first_name', 'last_name', 'contact_number', 'address',
        'khasra_number', 'area_in_beegha', 'land_costing', 'development_costing',
        'kisan_payment', 'land_address', 'payment_to_kisan', 'basic_sales_price','land_type'
    ]
    template_name = 'kisan/kisan_update.html'  # Updated template name
    success_url = reverse_lazy('leads:kisan_list')

# View for deleting Kisan

class KisanDeleteView(DeleteView):
    model = Kisan
    template_name = 'kisan/kisan_confirm_delete.html'
    success_url = reverse_lazy('leads:kisan_list')

import csv
from django.http import HttpResponse
from .models import Property  # or any model you want to export

def export_properties_to_csv(request):
    # Define the HTTP response as a CSV file
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="properties.csv"'
    
    # Create a CSV writer
    writer = csv.writer(response)
    
    # Write the header row for the CSV file
    writer.writerow(['Title', 'Project Name', 'Block', 'Price per Sq Ft', 'Area', 'Plot Price', 'Type', 'Status'])
    
    # Fetch data from the model
    properties = Property.objects.all()  # Adjust your queryset as needed
    
    # Write data rows
    for property in properties:
        writer.writerow([
            property.title,
            property.project_name,
            property.block,
            property.price,
            property.area,
            property.totalprice,  # Assuming this is the plot price field
            property.type,
            'Sold' if property.is_sold else 'Available' if not property.is_in_emi else 'In Emi'
        ])
    
    return response

def export_buyers_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="buyers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Mobile','Email','Property',  'Address', 'Booking Date', 'Agent Name'])  # Adjust columns as needed
    
    buyers = PlotBooking.objects.all()  # Adjust your queryset as needed

    for buyer in buyers:
        writer.writerow([
            buyer.id,
            buyer.name,
            buyer.mobile_no,
            buyer.email,
            buyer.project,
            buyer.address,
            buyer.booking_date,
            buyer.agent,
           
            # buyer.plot_id,  # Adjust field name based on your Buyer model
            # buyer.agent if buyer.agent else 'N/A'
        ])
    
    return response

from .models import Salary  # Replace with your Salary model

def export_salaries_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="salaries.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Agent Name', 'Commision', 'Payment Date', 'Property ID'])  # Adjust columns as needed
    
    salaries = Salary.objects.all()  # Adjust your queryset as needed

    for salary in salaries:
        writer.writerow([
            salary.agent,  # Assuming agent has a user relation with username
            salary.base_salary,
            # salary.bonus,
            salary.payment_date,
            salary.property.title if salary.property else 'N/A'
        ])
    
    return response



from .models import Kisan  # Replace with your Kisan model

def export_kisans_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="kisans.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'First Name','Last Name', 'Contact','Khasra Number', 'Area in Beegha','Land Cost'])  # Adjust columns as needed
    
    kisans = Kisan.objects.all()  # Adjust your queryset as needed

    for kisan in kisans:
        writer.writerow([
            kisan.id,
            kisan.first_name,
            kisan.last_name,
            kisan.contact_number,
            kisan.khasra_number,
            kisan.area_in_beegha,
            kisan.land_costing
        ])
    
    return response



