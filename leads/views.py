import logging
import datetime
from datetime import timedelta,date
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View, generic
from django.views.generic import ListView, UpdateView, DeleteView

from leads.models import Lead, Agent, Category, FollowUp, Promoter, PlotBooking, Project, EMIPayment, Area, Typeplot
from agents.mixins import OrganisorAndLoginRequiredMixin
from .models import Property, Sale, Salary, Bonus, Kisan, UserProfile, Daybook
from .forms import (
    LeadForm, 
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
)



logger = logging.getLogger(__name__)


# CRUD+L - Create, Retrieve, Update and Delete + List


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

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
        total_lead_count = Lead.objects.filter(organisation=user.userprofile).count()

        recent_buyers = PlotBooking.objects.order_by('-booking_date')[:5]  # Use the appropriate field for your criteria
        

        # Sales Report
        sales_data = Sale.objects.values('sale_date').annotate(
            total_sale_price=Sum('sale_price'),
            properties_sold=Count('id')
        ).order_by('sale_date')

        labels = [sale['sale_date'].strftime("%Y-%m-%d") for sale in sales_data]  # Format dates
        data = [sale['properties_sold'] for sale in sales_data]

        # Calculate total sales amount and total costs
        total_sales = Sale.objects.aggregate(total=Sum('sale_price'))['total'] or 0
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
            organisation=user.userprofile,
            date_added__gte=thirty_days_ago
        ).count()

        converted_category = Category.objects.filter(name="Converted").first()
        converted_in_past30 = Lead.objects.filter(
            organisation=user.userprofile,
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

    
class LeadListView(LoginRequiredMixin,generic.ListView):
    
    template_name = "leads/lead_list.html"
    context_object_name = "leads"

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.filter(
                organisation=user.userprofile, 
                agent__isnull=False
            )
        else:
            # Check if the user has an associated agent
            if hasattr(user, 'agent'):
                queryset = Lead.objects.filter(
                    organisation=user.agent.organisation, 
                    agent__isnull=False
                )
                # Filter for the agent that is logged in
                queryset = queryset.filter(agent__user=user)
            else:
                queryset = Lead.objects.none()  # Return an empty queryset if no agent exists

        return queryset
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(LeadListView, self).get_context_data(**kwargs)
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile,agent__isnull=True)
            
            context.update ({
                "unassigned_leads": queryset
                })   
           
        return context
    

def lead_list(request):
    leads = Lead.objects.all()
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
    form = LeadModelForm()
    if request.method == "POST":
        form = LeadModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/leads")
    context = {
        "form": form
    }
    return render(request, "leads/lead_create.html", context)


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
        return Property.objects.all()

class PropertyDetailView(LoginRequiredMixin, generic.DetailView):
    model = Property
    template_name = 'property/property_detail.html'  # Update with your template path
    context_object_name = 'property'

    def get_queryset(self):
        return Property.objects.filter(agent__user=self.request.user)

# Function-based view to display properties
def properties_view(request):
    properties = Property.objects.all()  # Fetch all properties
    context = {
        'properties': properties,
    }
    return render(request, 'leads/properties_list.html', context)  # Ensure this path is correct

        

class ProjectCreateView(LoginRequiredMixin, View):
    model = Project,Area
    template_name = 'property/create_project.html'


    def get(self, request):
        # Render the initial form for number of properties and common attributes
        return render(request, self.template_name)

    
    def post(self, request):
        # Get the number of properties to create and common attributes
        project_name = request.POST.get('project_name', )
        block = request.POST.get('block', '')
        try:
            # Assuming you have a Project model
            Project.objects.create(
                project_name=project_name,
                block=block,  # Example size, modify as needed
            ) 
            messages.success(request, 'Project created successfully!')
        except IntegrityError:
            # Catch the unique constraint error and send a message to the user
            messages.error(request, 'A project with this name already exists!')
        

        return redirect(self.get_success_url())

        
    def get_success_url(self):
        return reverse('leads:property-create')
    
class PropertyCreateView(LoginRequiredMixin, View):
    template_name = 'property/property_create.html'

    def get(self, request):
        projects = Project.objects.all()
        areas = Area.objects.all()
        types = Typeplot.objects.all()
        # Render the initial form for number of properties and common attributes
        return render(request, self.template_name,{'projects':  projects,'areas':areas,'types':types})


    def post(self, request):
        # Get the number of properties to create and common attributes
        num_properties = int(request.POST.get('num_properties', 1))
        price = int(request.POST.get('price', ''))
        type = request.POST.get('type', '')
        dimension = request.POST.get('dimension', '')
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
        key = int(request.POST.get('project_id', ''))
                # Fetch the Project instance using `get_object_or_404`
        project = get_object_or_404(Project, id=key)
        tp = (l*b*price)

        # Create the properties in the database
        for _ in range(num_properties):
            Property.objects.create(
                project_id = project , # Example size, modify as needed
                price=price , # Example price, modify as needed
                type=type,  # Example price, modify as needed
                area=area,  # Example price, modify as needed
                breadth=b,  # Example price, modify as needed
                length=l,  # Example price, modify as needed
                totalprice=tp,  # Example price, modify as needed
            )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('leads:property_list')  # Redirect to property list after creation  # Redirect to property list after successful update

def select_properties_view(request):
    projects = Project.objects.all()
    properties = Property.objects.all()

    if request.method == 'POST':
        selected_ids = request.POST.getlist('properties')  # Get list of selected IDs
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

    template_name = 'property/property_update.html'  # Update with your template 

    def get(self, request, ids):
        property_ids = ids.split(',')  # Convert the comma-separated string back to a list
        properties = Property.objects.filter(id__in=property_ids)  # Fetch selected properties
        return render(request, self.template_name, {'properties': properties})

    def post(self, request, ids):
        property_ids = ids.split(',')  # Convert the comma-separated string back to a list
        project_name = request.POST.get('project_name', '')
        price = request.POST.get('price', '')
        block = request.POST.get('block', '')
        print(project_name)
        print(block)
        print(price)

        for prop_id in property_ids:
            property_instance = Property.objects.get(id=prop_id)
            # Update the instance based on the form data (make sure to handle input correctly)
            property_instance.project_name = project_name
            property_instance.price = float(price)
            property_instance.block = block 
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

class DaybookListView(LoginRequiredMixin, View):
    template_name = 'Daybook/daybook_list.html'

    def get(self, request, *args, **kwargs):
        # Get today's date
        today = timezone.now().date()

        # Calculate today's expenses
        todays_expenses = Daybook.objects.filter(date=today)
        total_todays_expenses = sum(expense.amount for expense in todays_expenses)

        # Get current balance (replace with your actual current balance logic)
        current_balance = 25000
        updated_balance = current_balance - total_todays_expenses
        

        context = {
            'expenses': todays_expenses,
            'total_balance': updated_balance,
            'todays_expense': total_todays_expenses,
        }
        return render(request, self.template_name, context)

def daybook_create(request):
    if request.method == 'POST':
        form = DaybookEntryForm(request.POST)  # Update to use the new form name
        if form.is_valid():
            form.save()
            return redirect('leads:daybook_list')  # Redirect to the daybook list after saving
    else:
        form = DaybookEntryForm()  # Update to use the new form name
    return render(request, 'Daybook/daybook_form.html', {'form': form})


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
        
        return render(request, self.template_name, {'form': form, 'agents': agents})

    def post(self, request, *args, **kwargs):
        form = PlotBookingForm(request.POST)
        agents = Agent.objects.all()

        if form.is_valid():
            
            # Retrieve EMI amount and tenure from the form
            emi_amount = form.cleaned_data.get('emi_amount')
            Plot_price = form.cleaned_data.get('Plot_price')
            tenure = form.cleaned_data.get('emi_tenure')
            project = form.cleaned_data.get('project')
            agent = form.cleaned_data.get('agent')
            print(agent)
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

                Salary.objects.create(
                    agent = agent.user,
                    base_salary=base_salary,
                    bonus = 0,
                    payment_date=date.today()  # Adds the current date to payment_date
                )
                agent=agent.parent_agent


            prop =  Property.objects.get(title=project)
            print(prop.is_sold)
            prop.is_sold=True
            prop.save()
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
        buyers = PlotBooking.objects.select_related('agent').all()
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

def pay_emi(request, emi_id):
    emi_payment = get_object_or_404(EMIPayment, id=emi_id)

    if request.method == 'POST':
        amount_paid = request.POST.get('amount_paid', 0)
        emi_payment.pay_emi(Decimal(amount_paid))  # Update the EMI payment

        return redirect('leads:buyers_list')  # Redirect after updating

    return render(request, 'plot_registration/pay_emi.html', {'emi_payment': emi_payment})


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

#KISAN FORM

class KisanForm(forms.ModelForm):
    class Meta:
        model = Kisan
        fields = [
            'first_name', 'last_name', 'contact_number', 'address',
            'khasra_number', 'area_in_beegha', 'land_costing',
            'development_costing', 'kisan_payment', 'land_address',
            'payment_to_kisan', 'basic_sales_price'
        ]

    def clean(self):
        cleaned_data = super().clean()
        kisan_payment = cleaned_data.get("kisan_payment")
        land_address = cleaned_data.get("land_address")

        # Example validation logic
        if kisan_payment is None and land_address is None:
            raise forms.ValidationError("At least one of 'Kisan Payment' or 'Land Address' must be provided.")

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

        return render(request, 'kisan/kisan_update.html', {'form': form, 'kisan': kisan if pk else None})
    except Exception as e:
        print(f"Error occurred: {e}")
        return render(request, 'kisan/kisan_update.html', {'form': form, 'error': str(e)})


# View for listing Kisan

class KisanListView(LoginRequiredMixin,ListView):
    model = Kisan
    template_name = 'kisan/kisan_list.html'
    context_object_name = 'kisans'


class KisanUpdateView(UpdateView):

    model = Kisan
    fields = [
        'first_name', 'last_name', 'contact_number', 'address',
        'khasra_number', 'area_in_beegha', 'land_costing', 'development_costing',
        'kisan_payment', 'land_address', 'payment_to_kisan', 'basic_sales_price'
    ]
    template_name = 'kisan/kisan_update.html'  # Updated template name
    success_url = reverse_lazy('leads:kisan_list')

# View for deleting Kisan

class KisanDeleteView(DeleteView):
    model = Kisan
    template_name = 'kisan/kisan_confirm_delete.html'
    success_url = reverse_lazy('leads:kisan_list')
