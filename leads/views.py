import logging
import datetime
from django.utils.dateparse import parse_date
from django import forms
from leads.models import models
from datetime import timedelta , date
from django.views.generic import TemplateView
from django.core.files import File
from django.views.decorators.csrf import csrf_protect
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.shortcuts import render, redirect
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
from django.db.models import Sum
from django.utils.timezone import now
from django.http import HttpResponse
from weasyprint import HTML
from datetime import timedelta
from leads.models import Lead, Agent, Category, FollowUp, Promoter, PlotBooking, Project, EMIPayment, Area, Typeplot,send_sms
from agents.mixins import OrganisorAndLoginRequiredMixin ,AgentAndLoginRequiredMixin
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

# views.py
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login

@csrf_protect
def custom_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            print("login")
            # Redirect to the dashboard or desired page after successful login
            return redirect(reverse_lazy('dashboard'))  # Replace 'dashboard' with your actual URL name
        else:
            # Handle invalid login
            return render(request, 'registration/login.html', {'error': 'Invalid username or password'})
    
    # Render the login template for GET requests
    return render(request, 'registration/login.html')


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
    template_name = "registration/login.html"

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
    user_profile = request.user

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



class ExpenseFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    
class DashboardView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch the current date and start of the month
        today = now().date()

        # Fetch date range from the request
        request = self.request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        selected_project_id = self.request.GET.get('project_id')

        # Parse dates safely
        if start_date:
            start_date = parse_date(str(start_date))
        if end_date:
            end_date = parse_date(str(end_date))

        # Default date range to current month if no dates provided
        if not start_date:
            start_date = today.replace(day=1)
        if not end_date:
            end_date = today

        # Calculate monthly expenses for the selected date range
        monthly_expenses = Daybook.objects.filter(date__range=(start_date, end_date)).aggregate(
            total_amount=Sum('amount')
        )['total_amount'] or 0

        # Calculate total salaries distributed in the selected date range
        total_salaries = (
            Salary.objects.filter(payment_date__range=(start_date, end_date))
            .aggregate(total=Sum('base_salary'))['total']
            or 0
        )
        # Calculate total promoter salaries
        total_promoter_salaries = (
            Promoter.objects.filter(joining_date__range=(start_date, end_date))
            .aggregate(total_salary=Sum('salary'))['total_salary']
            or 0
        )

        # Calculate total agent commissions in the selected date range
        total_agent_commissions = (
            Salary.objects.filter(payment_date__range=(start_date, end_date))
            .aggregate(total_commissions=Sum('commission'))['total_commissions']
            or 0
        )

        
    
        # Calculate total land and development costs
        total_land_cost = Kisan.objects.filter(date_added__range=(start_date, end_date)).aggregate(
            total=Sum('land_costing')
        )['total'] or 0
        total_development_cost = Project.objects.filter(date_added__range=(start_date, end_date)).aggregate(
            total=Sum('dev_cost')
        )['total'] or 0
       

        # Calculate total sales (earned revenue)
        total_sales = PlotBooking.objects.aggregate(total=Sum('Plot_price'))['total'] or 0
        total_cost = total_development_cost + total_land_cost
        # Calculate total profit
        total_expenses = (
            total_salaries +
            total_agent_commissions +
            total_land_cost +
            total_development_cost +
            monthly_expenses +
            total_promoter_salaries
        )
        grand_total_profit = total_sales - total_expenses
        
        # Sales Report - Data for graph
        sales_data = PlotBooking.objects.values('booking_date').annotate(
            total_sale_price=Sum('Plot_price'),
            properties_sold=Count('id')
        ).order_by('booking_date')

        labels = [sale['booking_date'].strftime("%Y-%m-%d") for sale in sales_data]
        data = [sale['properties_sold'] for sale in sales_data]

        # Prepare profit data for the graph
        profit_data = []
        for sale in sales_data:
            profit = sale['total_sale_price'] - total_land_cost - total_development_cost
            profit_data.append(float(profit))

        # Total salary distributed in the last 30 days
        total_salary_distributed = Salary.objects.filter(payment_date__gte=today - timedelta(days=30)).aggregate(
            total=Sum('base_salary')
        )['total'] or 0

        # Salary distribution data for pie chart
        salary_distribution = [
            float(total_salary_distributed),
            float(grand_total_profit - total_salary_distributed),
        ]
        salaryDistribution_labels = ['Salary Distributed', 'Remaining Profit']

        # Total leads and recent buyers
        total_lead_count  = Lead.objects.filter(date_added__range=(start_date, end_date)).count()
        recent_buyers = PlotBooking.objects.order_by('-booking_date')[:5]

        # Leads and converted leads in the last 30 days
        thirty_days_ago = today - timedelta(days=30)
        total_in_past30 = Lead.objects.filter(date_added__gte=thirty_days_ago).count()

        remaining_profit = grand_total_profit - total_salary_distributed

        converted_category = Category.objects.filter(name="Converted").first()
        converted_in_past30 = Lead.objects.filter(
            category=converted_category,
            converted_date__gte=thirty_days_ago
        ).count()

        projects = Project.objects.all()
        total_projects = Project.objects.count()
        # If a specific project is selected, calculate project-related data
        project_data = {}
        if selected_project_id:
            selected_project = projects.filter(id=selected_project_id).first()

            if selected_project:
                total_properties = Property.objects.filter(project_id=selected_project).count()
                total_sold = Property.objects.filter(project_id=selected_project, is_sold=True).count()
                total_emi = Property.objects.filter(project_id=selected_project, is_in_emi=True).count()
                available_plots = Property.objects.filter(project_id=selected_project, is_sold=False).count()

                project_data = {
                    "selected_project": selected_project,
                    "total_properties": total_properties,
                    "total_sold": total_sold,
                    "total_emi": total_emi,
                    "available_plots": available_plots,
                    
                }


        # Update context with all the data
        context.update({
            'labels': labels,
            'data': data,
            'profit_labels': labels,
            'total_salaries': total_salaries,
            'total_projects': total_projects,
            'profit_data': profit_data,
            'total_lead_count': total_lead_count,
            'total_in_past30': total_in_past30,
            'converted_in_past30': converted_in_past30,
            'total_sales': total_sales,
            'total_cost': total_cost,
            'total_land_cost': total_land_cost,
            'total_development_cost': total_development_cost,
            'total_expenses': total_expenses,
            'total_profit': grand_total_profit,
            'monthly_expenses': monthly_expenses,
            'grand_total_profit': grand_total_profit,
            'salary_distribution': salary_distribution,
            'salaryDistribution_labels': salaryDistribution_labels,
            'recent_buyers': recent_buyers,
            'remaining_profit': remaining_profit,
            "projects": projects,
            "project_data": project_data,
            "selected_project_id": selected_project_id,
            "total_promoter_salaries":total_promoter_salaries
        })

        return context




    
class LeadListView(AgentAndLoginRequiredMixin,generic.ListView):
    
    template_name = "leads/lead_list.html"
    context_object_name = "leads"    

    context_object_name = "leads"
    def get_queryset(self):
        # Use logging in models or views


        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.all()
            # queryset = Lead.objects.filter(
                # organisation=user.userprofile, 
                # agent__isnull=False
            # ).select_related('agent')
        else:
            # Check if the user has an associated agent
            if hasattr(user, 'agent'):
                queryset = Lead.objects.filter(
                    # organisation=user.agent.organisation, 
                    agent=user.agent
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
            queryset = Lead.objects.all()
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


class LeadCreateView(OrganisorAndLoginRequiredMixin,AgentAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/lead_create.html"
    form_class = LeadModelForm

    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        lead = form.save(commit=False)
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
        return Lead.objects.all()

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


class AssignAgentView(generic.FormView):  # Temporarily remove mixin
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({"request": self.request})
        print("Form kwargs:", kwargs)  # Debugging
        return kwargs

    def get_success_url(self):
        print("Redirecting to lead list")  # Debugging
        return "/leads/"  # Temporarily hard-coded

    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        print("Assigning agent:", agent)
        print("Lead:", lead)
        lead.agent = agent
        lead.save()
        messages.info(self.request, "You have successfully Assigned the agent")

        return super().form_valid(form)


class CategoryListView(AgentAndLoginRequiredMixin, generic.ListView):
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        user = self.request.user

        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.all()

        context.update({
            "unassigned_lead_count": queryset.filter(category__isnull=True).count()
        })
        return context

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.all()
        else:
            queryset = Category.objects.all()
        queryset = queryset.annotate(lead_count=Count('leads'))
        return queryset


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.all()            
        else:
            queryset = Category.objects.all()
        return queryset
 

class CategoryCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/category_create.html"
    form_class = CategoryModelForm

    def get_success_url(self):
        return reverse("leads:category-list")

    def form_valid(self, form):
        category = form.save(commit=False)
        # category.organisation = self.request.user.userprofile
        # category.save()
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
            queryset = Category.objects.all()
        else:
            queryset = Category.objects.all()
        return queryset


class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.all()
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
            return FollowUp.objects.all()
        else:
            return FollowUp.objects.all()
    

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
            queryset = FollowUp.objects.all()
        else:
            queryset = FollowUp.objects.all()
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
        emipayments = EMIPayment.objects.filter(plot_booking = plot_booking ,status = 'Paid')
        # totalemipaid = emipayments.plot_booking.all()
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
        # if plot_booking:
            # totalmoneypaidbycust = plot_booking.total_paidbycust + sum(emi.emi_amount for emi in emipayments)
            # fprforbuyer = totalmoneypaidbycust - cost_for_land  - tot_sal 

#Update context with all relevant details
        context.update({
            'property': property,
            'total_plot_price_of_prop': cost_for_land,
            'total_plot_price_of_pro': property.totalprice,
            'plot_booking': plot_booking,
            'total_land_cost': total_land_cost,
            'total_development_cost': total_development_cost,
            # 'totalmoneypaidbycust': totalmoneypaidbycust,
            # 'fprforbuyer': fprforbuyer,
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
            project.total_land_area_used = Property.objects.filter(project_id=project).aggregate(total_area=Sum('area'))['total_area'] or 0
            tla = project.total_land_area_used
            project.total_land_available = project.total_land_available_fr_plotting - tla
            project.cost_per_sqft = project.dev_cost
            kisan_lands = project.lands.all()
            # total_area = sum(land.area_in_beegha*27200 for land in kisan_lands)
            total_land_cost =  sum(land.land_costing for land in kisan_lands)
            print(project.dev_cost)
            project.land_cost_per_sqft = (total_land_cost/project.total_land_available_fr_plotting) + project.dev_cost

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
    properties = Property.objects.filter(is_sold = False,is_in_emi = False)

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Include extra context if it exists
        if hasattr(self, 'extra_context'):
            context.update(self.extra_context)
        return context


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
        price = float(request.POST.get('price', ''))
        breadth = int(request.POST.get('block', ''))
        update_type = request.POST.get('plot_type', '')
        # Calculate required area
        tp = length*breadth*price
        required_area = length * breadth * count

        # Check if available land is sufficient
        if required_area > project.available_land:
            error_message = f"Only {project.available_land} sqft of land is available. Cannot create {required_area} sqft of property."
            print(error_message)
        
        # Set the extra context to pass the error message
            self.extra_context = {'error_message': error_message}
            return self.get(request, ids)  # Call `get` without passing `error_message` as an argument
        # Update properties if sufficient land is available
        for property_instance in properties:
            property_instance.length = length
            property_instance.price = float(price)
            property_instance.breadth = breadth
            property_instance.area = breadth*length
            property_instance.plot_type = update_type
            property_instance.totalprice=tp  # Example price, modify as needed

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

from django.db.models import F, Value, DecimalField, ExpressionWrapper
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic.list import ListView

class SalaryListView(AgentAndLoginRequiredMixin, ListView):
    model = Salary
    template_name = 'salary/salary_list.html'  # Update with your template path
    context_object_name = 'salaries'

    def get_queryset(self):
        # Start with a base queryset depending on the user type
        if self.request.user.is_organisor:
            queryset = Salary.objects.all()
        else:
            queryset = Salary.objects.filter(agent=self.request.user)

        # Annotate the queryset with the total compensation calculation
        queryset = queryset.annotate(
            total_compensation=ExpressionWrapper(
                F('base_salary') + Value(0) + F('bonus') + F('commission'),
                output_field=DecimalField()
            )
        )

        # Apply filtering by start date and end date if provided
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        payment_date = self.request.GET.get('payment_date')

        if payment_date:
            queryset = queryset.filter(payment_date=payment_date)


        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)  # Filter by start date
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)  # Filter by end date

        if not payment_date:
            queryset = queryset.order_by('-payment_date', '-id')  # Show all records, latest first

        return queryset

    def render_to_response(self, context, **response_kwargs):
        # If the request is an Ajax request, return the partial HTML response
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
class DaybookCreateView(OrganisorAndLoginRequiredMixin, View):
    template_name = 'Daybook/daybook_form.html'

    def get(self, request, *args, **kwargs):
        form = DaybookEntryForm()
        return render(request, self.template_name, {'form': form, 'today': timezone.now().date()})

    def post(self, request, *args, **kwargs):
        form = DaybookEntryForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            print("expenese is", expense)
            # balance = Balance.objects.first()
            balance, created = Balance.objects.get_or_create(defaults={'amount': 0})  # Set an initial amount if created
            print("balance is", balance)
            balance, created = Balance.objects.get_or_create(defaults={'amount': 0})  # Create Balance if not existing
            
            # Check if balance is available
            if balance:
                if balance.amount >= expense.amount:
                    # Deduct from balance as it's within the daily limit
                    balance.amount -= expense.amount
                    action_message = "added"
                else:
                    # If expense exceeds the daily limit, return an error message
                    messages.error(request, "Daily limit reached. Expense exceeds available balance.")
                    return render(request, self.template_name, {'form': form, 'today': timezone.now().date()})
            else:
                # No balance record exists, create one with negative amount if overspending
                Balance.objects.create(amount=-expense.amount)
                action_message = "added"

            # Save the expense and update balance
            expense.save()
            balance.save()
            # Create the message for SMS
            remaining_balance = balance.amount  # Get the remaining balance after expense is deducted
            message = f"Daybook Entry {action_message}:\nDate: {expense.date}\nActivity: {expense.activity}\nAmount: {expense.amount}\nRemaining Balance: {remaining_balance}"

            if expense.remark:
                message += f"\nRemark: {expense.remark}"

            # Send SMS (replace with your actual phone number)
            my_number = '+919548582538'  # Replace with your actual phone number
            send_sms(to=my_number, message=message)

            # Success message for adding the expense
            messages.success(request, f"Expense of {expense.amount} has been successfully added.")

            return redirect('leads:daybook_list')
        return render(request, self.template_name, {'form': form, 'today': timezone.now().date()})

class DaybookListView(OrganisorAndLoginRequiredMixin, View):
    template_name = 'Daybook/daybook_list.html'

    def get(self, request, *args, **kwargs):
        # Get today's date
        today = timezone.now().date()

        # Get start and end date from the GET parameters for filtering
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Initialize the queryset with all daybook entries
        daybook_entries = Daybook.objects.all()

        # Apply filtering based on start and end date if provided
        if start_date:
            daybook_entries = daybook_entries.filter(date__gte=start_date)  # filter greater than or equal to start_date
        if end_date:
            daybook_entries = daybook_entries.filter(date__lte=end_date)  # filter less than or equal to end_date
        
        # Check if we need to show all expenses or just today's expenses
        show_all = request.GET.get('show_all') == 'true'

        if show_all:
            expenses_to_display = daybook_entries  # Show all filtered expenses
        else:
            # Filter only today's expenses
            expenses_to_display = daybook_entries.filter(date=today)

        # Calculate today's expenses
        todays_expenses = daybook_entries.filter(date=today)
        total_todays_expenses = sum(expense.amount for expense in todays_expenses)

        # Total expenses for the filtered date range
        total_expenses = daybook_entries.aggregate(total_amount=models.Sum('amount'))['total_amount'] or 0

        # Retrieve current balance and carryover amount
        current_balance_record = Balance.objects.first()
        current_balance = current_balance_record.amount if current_balance_record else 0
        carryover_amount = current_balance_record.carryover_amount if current_balance_record else 0

        # Calculate carryover for next day
        remaining_balance = current_balance - total_todays_expenses
        if remaining_balance > 0:
            carryover_amount += remaining_balance
        else:
            carryover_amount = max(0, carryover_amount + remaining_balance)

        context = {
            'expenses': expenses_to_display,  # Pass the expenses to display (all or today's)
            'total_balance': current_balance,
            'carryover_amount': carryover_amount,
            'todays_expense': total_todays_expenses,
            'total_expenses': total_expenses,
            'start_date': start_date,
            'end_date': end_date,
            'show_all': show_all  # Pass the status of the show_all flag
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if 'reset_expenses' in request.POST:
            Daybook.objects.all().delete()
            Balance.objects.all().delete()
            return redirect('leads:daybook_list')


def export_daybook_to_csv(request):
    # Get the start_date and end_date from the request's GET parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Start building the response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="daybook.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Activity', 'Custom Activity', 'Amount', 'Remark'])  # Adjust columns as needed
    
    # Start with all daybook entries
    daybook_entries = Daybook.objects.all()

    # Filter based on the provided date range
    if start_date:
        daybook_entries = daybook_entries.filter(date__gte=start_date)  # Greater than or equal to start_date
    if end_date:
        daybook_entries = daybook_entries.filter(date__lte=end_date)  # Less than or equal to end_date

    # Write the daybook data rows
    for entry in daybook_entries:
        writer.writerow([
            entry.date,  # Date of the entry
            entry.activity,  # Activity type
            entry.custom_activity or '',  # Custom activity for 'Others'
            entry.amount,  # Amount of the expense
            entry.remark or '',  # Remark, empty if not provided
        ])
    
    return response



class BalanceUpdateView(OrganisorAndLoginRequiredMixin, View):
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
                action_message = "added"
                print("Add",balance.amount)
            elif action == 'deduct':
                balance.amount = max(0, balance.amount - amount)
                action_message = "deducted"
                print("deduct",balance.amount)

            balance.save()
            # Create the message content with remaining balance
            message = f"Balance has been {action_message} by {amount}. Current balance: {balance.amount}"

            # Send SMS to the specified phone number (replace with the actual number)
            my_number = '+918052513208'  # Replace with your actual phone number
            send_sms(to=my_number, message=message)
            return redirect('leads:daybook_list')
        return render(request, self.template_name, {'form': form})

# PROMOTER 
class PromoterListView(LoginRequiredMixin, ListView):
    model = Promoter
    template_name = 'promoter/promoter_list.html'
    context_object_name = 'promoters'
    ordering = ['name']
    def get_queryset(self):
            queryset = super().get_queryset()

            # Get the 'start_date' and 'end_date' from request parameters
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')

            if start_date:
                queryset = queryset.filter(joining_date__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(joining_date__lte=end_date)

            return queryset

    def get(self, request, *args, **kwargs):
        if 'download' in request.GET:  # Check for 'download' query parameter
            return self.download_csv(request)
        return super().get(request, *args, **kwargs)

    def download_csv(self, request):
        # Get the filtered queryset
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        promoters = self.get_queryset()

        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Employee.csv"'

        writer = csv.writer(response)
        writer.writerow([ 'Name', 'Email', 'Mobile Number', 'Joining Date','Salary', 'Payment Date', 'Department', 'Status'])

        for promoter in promoters:
            writer.writerow([ promoter.name, promoter.email, promoter.mobile_number, promoter.joining_date,promoter.salary, promoter.payment_date, promoter.department, promoter.status])

        return response

# Update/Delete Promoter View
def update_delete_promoter(request, promoter_id):
    promoter = get_object_or_404(Promoter, id=promoter_id)

    if request.method == 'POST':
        if 'update' in request.POST:  # Handle update request
            # Bind the form to the submitted data
            form = PromoterForm(request.POST, instance=promoter)
            if form.is_valid():
                # If the form is valid, save the updated promoter
                updated_promoter = form.save(commit=False)
                
                # Preserve the original joining date if it's not provided in the form
                if not updated_promoter.joining_date:
                    updated_promoter.joining_date = promoter.joining_date
                
                # Calculate the next payment date based on the updated information
                updated_promoter.payment_date = updated_promoter.calculate_next_payment_date()  # Optional logic
                updated_promoter.save()  # Save changes to the database
                return redirect('leads:promoter_list')  # Redirect to the promoter list
            else:
                print(form.errors)  # Print errors to debug in the console

        elif 'delete' in request.POST:  # Handle delete request
            try:
                promoter.delete()
                return redirect('leads:promoter_list')  # Redirect to the promoter list
            except Exception as e:
                print(f"Error deleting promoter: {str(e)}")  # Log the error

    else:
        # Populate the form with the promoter's current details
        form = PromoterForm(instance=promoter)

    # Render the page with the form and promoter details
    return render(request, 'promoter/update_delete_promoter.html', {'form': form, 'promoter': promoter})



def add_promoter(request):
    if request.method == 'POST':
        form = PromoterForm(request.POST)
        if form.is_valid():
            promoter = form.save(commit=False)
            promoter.payment_date = promoter.calculate_next_payment_date()  # Ensure the payment_date logic is applied
            promoter.save()
            return redirect('leads:promoter_list')  # Redirect to the promoter list
    else:
        form = PromoterForm()

    return render(request, 'promoter/add_promoter.html', {'form': form})

def calculate_emi(plot_price, interest_rate, tenure):
    if interest_rate is not None and tenure > 0:
        monthly_interest_rate = interest_rate / (12 * 100)  # Convert annual interest rate to monthly
        emi = (plot_price * monthly_interest_rate * (1 + monthly_interest_rate)**tenure) / ((1 + monthly_interest_rate)**tenure - 1)
        print("EMI IS :",emi)
        return emi
    else:
        # If no interest, EMI is simply the plot price divided by tenure
        return plot_price / tenure
    

# PLOT REGISTRATION
class PlotRegistrationView(OrganisorAndLoginRequiredMixin, View):
    template_name = 'plot_registration/plot_registration.html'

    def get(self, request, *args, **kwargs):
        form = PlotBookingForm()
        agents = Agent.objects.all()
        # properties = list(Property.objects.values('id', 'totalprice', 'project_name'))  # Fetch only necessary fields
        properties = list(Property.objects.filter(is_in_emi=False, is_sold=False).values('id', 'totalprice', 'project_name'))

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
        properties = list(Property.objects.filter(is_in_emi=False, is_sold=False).values('id', 'totalprice', 'project_name'))

        print("get")
        properties = [
        {
            'id': prop['id'],
            'price': str(prop['totalprice']),  # Convert Decimal to string
            'project_name': prop['project_name']
        }
        for prop in properties
]
   
        print("post")
        

        if form.is_valid():
            # Retrieve EMI amount and tenure from the form
            project = form.cleaned_data.get('project')
            interest_rate = form.cleaned_data.get('interest_rate')
            payment_type = form.cleaned_data.get('payment_type')
            Property_inst = Property.objects.get(id = project.id)
            print(payment_type)
            if payment_type == 'installment':
                booking_amount = form.cleaned_data.get('booking_amount')
                emi_amount = form.cleaned_data.get('emi-amount')
                tenure = form.cleaned_data.get('emi_tenure')
                print(tenure,"tenure")

            elif payment_type == 'full':
                emi_amount = None
                tenure = None
                booking_amount = Property_inst.totalprice

            elif payment_type == 'custom':
                emi_amount = None
                tenure = None
                booking_amount = form.cleaned_data.get('booking_amount')
                
            print(booking_amount)

            form.instance.Plot_price = Property_inst.totalprice 
            form.instance.total_paid = booking_amount
            form.instance.total_paidbycust = booking_amount
            form.instance.booking_amount = booking_amount
            plot_price = Property_inst.totalprice
            form.save()


            Plot_price = plot_price - booking_amount
            # Calculate EMI with interest rate if applicable
            if emi_amount is None and tenure and Plot_price:
                emi_amount = calculate_emi(Plot_price, interest_rate, tenure)
            
            # Save EMI details
            if emi_amount is not None:
                form.instance.emi_amount = emi_amount  # Save EMI amount
            agent = form.cleaned_data.get('agent')
            payment_type = form.cleaned_data.get('payment_type')  # Get the payment type
            if agent:
                agent_level = agent.level
                print(agent_level)
                for i in range(1,agent_level+1):
                    if i == 1:
                        base_salary = int(booking_amount)/10
                    elif i == 2:
                        base_salary = int(booking_amount)/25
                    elif i == 3:
                        base_salary = int(booking_amount)*3/100
                    elif i == 4:
                        base_salary = int(booking_amount)/50
                    elif i == 5:
                        base_salary = int(booking_amount)/100

                    prop = Property.objects.get(title=project)
                    Salary.objects.create(
                        agent = agent.user,
                        base_salary=base_salary,
                        bonus = 0,
                        payment_date=date.today(),  # Adds the current date to payment_date
                        property=prop
                    )
                    # print(property)
                    agent=agent.parent_agent


            prop =  Property.objects.get(title=project)
            prop.is_sold=True
            # Check if the payment type is "installment" and set is_in_emi accordingly
            if payment_type == 'installment' or payment_type == 'custom':
                if Property_inst.totalprice - booking_amount <= 0:
                    prop.is_in_emi = False
                else:
                    prop.is_in_emi = True
            prop.save()  # Save the updated property
            plot_booking = form.save()
            monthly_emi = None
            # Ensure emi_amount is a Decimal and tenure is an integer
            # if emi_amount is not None and tenure is not None and tenure > 0:
            if tenure and emi_amount:
                monthly_emi = emi_amount
                # Generate EMI payment records
                payment_date = plot_booking.payment_date
                print("Plot registration paymentdate",payment_date)
                # Calculate the 1st of the next month
                next_month = (payment_date.month % 12) + 1
                print(next)
                year = payment_date.year + (payment_date.month // 12)
                print(year)
                first_due_date = payment_date.replace(day=1, month=next_month, year=year)
                print(first_due_date)
                # Generate EMI payment records
                for month in range(tenure):
                    due_date = first_due_date.replace(month=(first_due_date.month + month - 1) % 12 + 1, year=first_due_date.year + (first_due_date.month + month - 1) // 12 )
                    print("plotregistration due date",due_date)
                    EMIPayment.objects.create(
                        plot_booking=plot_booking,
                        due_date=due_date,
                        amount_for_agent = (plot_price- booking_amount)/tenure ,
                        emi_amount=monthly_emi  # Store calculated EMI
                    )
            elif emi_amount is None and tenure is None:
                # Handle missing or invalid EMI amount or tenure
                form.add_error(None, 'Invalid EMI amount or tenure.')
            print("monthy emi is",monthly_emi)


            # Prepare the message content
            agent = form.cleaned_data.get('agent')
            emi_start_date = plot_booking.payment_date  # Use the payment date or define as needed
            emi_start_date_formatted = emi_start_date.strftime('%Y-%m-%d')
            if agent is not None:
                
                # Now you can safely access agent.user.username
                message = f"""
                Plot Booking Details:

                Buyer Name: {plot_booking.name}
                Mobile No: {plot_booking.mobile_no}
                Email: {plot_booking.email}

                Plot Details:
                Project Title: {plot_booking.project.title if plot_booking.project else 'N/A'}
                Plot Price: {plot_booking.Plot_price} INR

                Payment Details:
                Payment Type: {plot_booking.payment_type}
                Booking Amount: {plot_booking.booking_amount} INR
                Mode of Payment: {plot_booking.mode_of_payment}
                EMI Tenure: {plot_booking.emi_tenure} months (if applicable)
                Interest Rate: {plot_booking.interest_rate}%
                {'EMI Amount: {:.2f} INR'.format(monthly_emi) if monthly_emi else 'EMI Amount: N/A'}
                EMI Start Date: {emi_start_date_formatted}
                

                Agent Details:
                Agent Name: {agent.user.username}
                Agent Commission: ₹{base_salary} (Commission for this booking)

                Thank you for your booking. Our team will contact you soon to complete the process.
                """
            else:
                # Handle the case where no agent is selected
                message = f"""
                Plot Booking Details:

                Buyer Name: {plot_booking.name}
                Mobile No: {plot_booking.mobile_no}
                Email: {plot_booking.email}

                Plot Details:
                Project Title: {plot_booking.project.title if plot_booking.project else 'N/A'}
                Plot Price: {plot_booking.Plot_price} INR

                Payment Details:
                Payment Type: {plot_booking.payment_type}
                Booking Amount: {plot_booking.booking_amount} INR
                Mode of Payment: {plot_booking.mode_of_payment}
                EMI Tenure: {plot_booking.emi_tenure} months (if applicable)
                Interest Rate: {plot_booking.interest_rate}%
                {'EMI Amount: {:.2f} INR'.format(monthly_emi) if monthly_emi else 'EMI Amount: N/A'}
                EMI Start Date: {emi_start_date_formatted}


                Agent Details:
                No agent selected.

                Thank you for your booking. Our team will contact you soon to complete the process.
                """


#             # Send SMS to your number (replace with your actual number)
            my_number = '+918052513208'  # Replace with your actual phone number
            send_sms(to=my_number, message=message)
            return redirect('plot_registration/buyers_list')  # Ensure this matches your URL configuration
        else:
            print(form.errors)
            messages.error(request, 'A buyer with this project already exists!')

            #return redirect('plot_registration/buyers_list.html')
            return render(request, self.template_name, {'form': form, 'agents': agents,'properties':properties})

def load_properties(request):
    project_name = request.GET.get('property.title')
    properties = Property.objects.filter(project_name_id=project_name).values('id', 'property.title')
    return JsonResponse(list(properties), safe=False)



from datetime import timedelta, date
from dateutil import parser
from django.utils import timezone
from django.shortcuts import render
from django.views import View
from .models import PlotBooking

class BuyersListView(OrganisorAndLoginRequiredMixin, View):
    template_name = 'plot_registration/buyers_list.html'

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        last_month = today - timedelta(days=30)

        # Handle missing start_date and end_date
        start_date = request.GET.get('start_date', last_month)
        end_date = request.GET.get('end_date', today)

        # Convert to proper date format if the values are passed as strings
        try:
            start_date = self.convert_to_date(start_date)
            end_date = self.convert_to_date(end_date)
        except ValueError:
            # Handle invalid date format or fallback to defaults
            start_date = last_month
            end_date = today

        # Get buyers filtered by the date range
        buyers = PlotBooking.objects.filter(booking_date__range=[start_date, end_date]).order_by('-booking_date')

        # Handle showing all buyers
        show_all = request.GET.get('show_all') == 'true'
        if show_all:
            buyers = PlotBooking.objects.all().order_by('-booking_date')

        context = {
            'buyers': buyers,
            'start_date': start_date,
            'end_date': end_date,
            'show_all': show_all
        }
        return render(request, self.template_name, context)

    def convert_to_date(self, date_str):
        """
        Convert date string to a datetime.date object using dateutil.parser.
        """
        # Check if the input is already a date object, return it directly
        if isinstance(date_str, date):
            return date_str
        
        # If the input is a string, parse it
        return parser.parse(date_str).date()

    


from dateutil import parser
import csv
from django.http import HttpResponse
from .models import PlotBooking  # Make sure to import your model

def convert_to_date(date_str):
    """
    Convert date string to a datetime.date object using dateutil.parser.
    """
    return parser.parse(date_str).date()

def export_buyers_to_csv(request):
    # Get the start_date and end_date from the GET parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Convert start_date and end_date to the correct format if necessary
    try:
        # Ensure start_date and end_date are in the proper format
        if start_date:
            start_date = convert_to_date(start_date)
        if end_date:
            end_date = convert_to_date(end_date)
    except ValueError:
        return HttpResponse("Invalid date format", status=400)

    # Start building the response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="buyers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Mobile', 'Email', 'Property', 'Address', 'Booking Date', 'Agent Name'])

    # Filter the buyers based on the selected date range
    buyers = PlotBooking.objects.all()  # Default to all
    if start_date and end_date:
        buyers = buyers.filter(booking_date__range=[start_date, end_date])

    # Write the buyers data rows
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
        ])
    
    return response

def convert_to_date(date_str):
        """
        Convert date string to a datetime.date object using dateutil.parser.
        """
        return parser.parse(date_str).date()



import datetime
import random
import string
def generate_receipt_number():
    # Generate a unique receipt number using the current date and time
    # current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    # Generate a random alphanumeric string of length 10
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # Combine both parts to create the final receipt number
    receipt_number = f"REC-{random_string}"

    return receipt_number


# Function to generate and save receipt PDF
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.storage import FileSystemStorage

# Function to generate and save receipt PDF
def generate_receipt_pdf(booking, receipt_number, gst_amount, other_charges, total_amount):
    # Generate a unique receipt number if not passed
    if not receipt_number:
        receipt_number = generate_receipt_number()

    # Calculate GST and total amount if not passed
    if not gst_amount:
        gst_value = (booking.gst_amount / 100) * booking.Plot_price
    if not total_amount:
        total_amount = booking.Plot_price + gst_value + booking.other_charges

    # Create a file buffer for the PDF
    buffer = BytesIO()

    # Set up the PDF canvas
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, f"Registration Receipt - {receipt_number}")
    c.drawString(100, 730, f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(100, 710, f"Buyer: {booking.name}")
    c.drawString(100, 690, f"Property: {booking.project.title}")
    c.drawString(100, 670, f"Plot Price: ₹{booking.Plot_price}")
    c.drawString(100, 610, f"Total Amount: ₹{total_amount:.2f}")
    
    c.save()

    # Move the buffer cursor to the beginning
    buffer.seek(0)

    # Save PDF file to 'receipts' directory and attach it to booking's receipt field
    file_name = f"receipt_{booking.id}.pdf"
    booking.receipt.save(file_name, File(buffer), save=True)

    # Close the buffer
    buffer.close()
    
    return file_name



def buyer_print_view(request, buyer_id):
    # Fetch the buyer instance or return a 404 error if not found
    buyer = get_object_or_404(PlotBooking, id=buyer_id)
   
    # Generate a unique receipt number
    receipt_number = generate_receipt_number()

    # Initialize gst_amount and other_charges
    gst_amount = 0
    other_charges = 0
    total_amount = buyer.Plot_price  # Start with the plot price

    # Check if the form is submitted
    if request.method == 'POST':
        # Fetch gst_amount and other_charges from form data
        gst_amount = Decimal(request.POST.get('gst_amount', 0))
        other_charges = Decimal(request.POST.get('other_charges', 0))
        plot_price = buyer.Plot_price
        gst_amount = (plot_price * gst_amount) / 100
        
        # Calculate the total amount
        total_amount = plot_price + gst_amount + other_charges
        # Generate and save the receipt PDF
        receipt_file = generate_receipt_pdf(buyer, receipt_number, gst_amount, other_charges, total_amount)

        # Update the buyer instance with the receipt file (optional if you want to store it in the model)
        buyer.receipt = receipt_file  # Assuming 'receipt' is a FileField in the PlotBooking model
        buyer.save()

    # Prepare the context for rendering the template
    context = {
        'buyer': buyer,
        'receipt_date': timezone.now(),          # Get the current date and time
        'receipt_number': receipt_number,        # Add the generated receipt number
        'gst_amount': gst_amount,                # Pass GST amount to template
        'other_charges': other_charges,          # Pass other charges to template
        'total_amount': total_amount,
        # 'receipt_file': receipt_file,            # Pass calculated total amount to template
    }
    
    # Render the template with the context
    return render(request, 'plot_registration/buyer_print_template.html', context)

@login_required
def update_delete_buyer(request, id):
    plot_booking = get_object_or_404(PlotBooking, id=id)
    # print(plot_booking.project)
    pdid = plot_booking.project
    pd =  Property.objects.get(title=pdid)
    


    if request.method == 'POST':
        if 'update' in request.POST:
            form = PlotBookingForm(request.POST, instance=plot_booking)
            if form.is_valid():
                form.save()
                pd.is_sold=False
                pd.save()
                project = form.cleaned_data.get('project')
                agent = form.cleaned_data.get('agent')               
                prop =  Property.objects.get(title=project)               
                prop.is_sold=True
                prop.save()                
                # Check for upcoming EMI payment dates and send reminders
                today = timezone.now()
                upcoming_emi = EMIPayment.objects.filter(plot_booking=plot_booking, status='Pending', due_date__lte=today + timedelta(days=5))
                if upcoming_emi.exists():
                    for emi in upcoming_emi:
                        # Send reminder SMS for EMI due in the next 5 days
                        message = f"Reminder: EMI payment for plot booking {plot_booking.project.title} is due on {emi.due_date}. Please make the payment."
                        my_number = '+918052513208'
                        send_sms(to=my_number, message=message)
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
    emipayments = buyer.emi_payments.filter(status = 'Paid')
    emip_ayments = buyer.emi_payments.filter(status = 'Pending')
    total_amount_paid  = buyer.total_paidbycust + sum(emi_payment.emi_amount for emi_payment  in emipayments )
    restamount  = buyer.Plot_price - buyer.total_paid
    total_interest_earned = sum(emi_payment.emi_amount for emi_payment  in emipayments ) - sum(emi_payment.amount_for_agent for emi_payment  in emipayments )

    if request.method == 'POST':  

        custom_amount = Decimal(request.POST.get('custom_amount'))  # Get the custom EMI amount from the form
        interest_rate = Decimal(request.POST.get('interest_rate'))  # Get the custom EMI amount from the form
        emi_tenure = int(request.POST.get('emi_tenure'))  # Get the custom EMI amount from the form
        emi_payment = buyer.emi_payments.filter(status='Pending')
        emi_payment.delete()
        plotprice = buyer.Plot_price - buyer.total_paid - custom_amount
        buyer.total_paid = (buyer.total_paid  + custom_amount)
        buyer.total_paidbycust = (buyer.total_paidbycust  + custom_amount)
        buyer.save()
        if  emi_tenure>0 and interest_rate>0:
            print(custom_amount)
            # plotprice = buyer.Plot_price - buyer.total_paid - custom_amount
            buyer.emi_tenure = emi_tenure
            # buyer.total_paid = (buyer.total_paid  + custom_amount)
            # buyer.total_paidbycust = (buyer.total_paidbycust  + custom_amount)
            buyer.save()
            print("dfghjhgfds",plotprice)
            # Generate EMI payment records
            payment_date = buyer.payment_date
            
            # Calculate the 1st of the next month
            next_month = (payment_date.month % 12) + 1
            year = payment_date.year + (payment_date.month // 12)
            first_due_date = payment_date.replace(day=1, month=next_month, year=year)
            new_emi = calculate_emi(plotprice, interest_rate, emi_tenure)
            for month in range(emi_tenure):
                due_date = first_due_date.replace(month=(first_due_date.month + month - 1) % 12 + 1,year=first_due_date.year + (first_due_date.month + month - 1) // 12)
                EMIPayment.objects.create(
                    plot_booking=buyer,
                    amount_for_agent = (buyer.Plot_price- buyer.total_paid)/emi_tenure ,
                    due_date=due_date,
                    emi_amount=new_emi  # Store calculated EMI
                )
            emipaymentcreated = buyer.emi_payments.filter(status = 'Pending')
            amtfagent = plotprice/emi_tenure
            emipaymentcreated.update(amount_for_agent = amtfagent)
        agent = buyer.agent
        print(agent)
        if (buyer.Plot_price -buyer.total_paid)<=0:
            prop =  Property.objects.get(title=buyer.project)
            prop.is_in_emi = False
            prop.save()

        if agent and custom_amount>=0:
            agent_level = agent.level
            print(agent_level)
            for i in range(1,agent_level+1):
                if i == 1:
                    base_salary = (custom_amount)/10
                elif i == 2:
                    base_salary = (custom_amount)/25
                elif i == 3:
                    base_salary = (custom_amount)*3/100
                elif i == 4:
                    base_salary = (custom_amount)/50
                elif i == 5:
                    base_salary = (custom_amount)/100
                print(buyer.project)
                print(agent.user)
                salary = Salary.objects.get(property = buyer.project,agent = agent.user)
                salary.base_salary += base_salary
                salary.save()

        return redirect('leads:buyers_list')

    context = {
        'buyer': buyer,
        'emi_payments': emi_payments,  # Pass the EMI payments to the template
        'restamount': restamount,  # Pass the EMI payments to the template
        'total_amount_paid': total_amount_paid,  # Pass the EMI payments to the template
        'total_interest_earned': total_interest_earned,  # Pass the EMI payments to the template
    }
    return render(request, 'plot_registration/buyer_detail.html', context)

# def mark_as_paid(request, payment_id):
#     payment = get_object_or_404(EMIPayment, id=payment_id)  # Fetch the EMI payment record
#     if payment.status == 'Pending':
#         payment.pay_emi(payment.emi_amount)  # Pay the full EMI amount
#     return redirect('leads:buyer_detail', buyer_id=payment.plot_booking.id)

def pay_emi(request, payment_id):
    if request.method == 'POST':
        payment = get_object_or_404(EMIPayment, id=payment_id)

        if payment.status == 'Pending':
            payment.status = 'Paid'
            plotbooking = payment.plot_booking
            plotbooking.total_paid = plotbooking.total_paid + payment.amount_for_agent
            plotbooking.save()
            payment.save()
            if (plotbooking.Plot_price -plotbooking.total_paid)<=0:
                prop =  Property.objects.get(title=plotbooking.project)
                prop.is_in_emi = False
                prop.save()

                print("emi payment gvcdghnbvcdg",plotbooking)
            agent = plotbooking.agent
            print(agent)
            if agent:
                agent_level = agent.level
                print(agent_level)
                for i in range(1,agent_level+1):
                    if i == 1:
                        base_salary = (payment.amount_for_agent)/10
                    elif i == 2:
                        base_salary = (payment.amount_for_agent)/25
                    elif i == 3:
                        base_salary = (payment.amount_for_agent)*3/100
                    elif i == 4:
                        base_salary = (payment.amount_for_agent)/50
                    elif i == 5:
                        base_salary = (payment.amount_for_agent)/100

                    salary = Salary.objects.get(property = payment.plot_booking.project,agent = agent.user)
                    salary.base_salary += base_salary
                    salary.save()
                    print(base_salary)
                    print(agent)
                    print(salary)

                    # prop = Property.objects.get(title=project)
                    # Salary.objects.create(
                    #     agent = agent.user,
                    #     base_salary=base_salary,
                    #     bonus = 0,
                    #     payment_date=date.today(),  # Adds the current date to payment_date
                    #     property=prop
                    # )
                    # print(property)
                    agent=agent.parent_agent


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
                # Send SMS notification when all EMI is paid
                message = f"EMI for plot booking {plotbooking.project.title} is fully paid. Thank you for completing the payment!"
                my_number = '+918052513208'
                send_sms(to=my_number, message=message)
            
            return JsonResponse({'status': 'success', 'message': 'Payment marked as paid.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


class GetProjectPriceView(OrganisorAndLoginRequiredMixin,View):
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

from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from .models import Kisan

from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from .models import Kisan

class KisanListView(OrganisorAndLoginRequiredMixin, ListView):
    model = Kisan
    template_name = 'kisan/kisan_list.html'
    context_object_name = 'kisans'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Handle date range filtering
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).date()  # Default to last 30 days if no start_date
        if not end_date:
            end_date = timezone.now().date()  # Default to today if no end_date

        try:
            # Convert to date objects
            start_date = self.convert_to_date(start_date)
            end_date = self.convert_to_date(end_date)
        except ValueError:
            start_date = (timezone.now() - timedelta(days=30)).date()  # Fallback on error
            end_date = timezone.now().date()

        # Filtering Kisans based on date range
        kisans = Kisan.objects.filter(date_added__range=[start_date, end_date])

        # Show all option
        show_all = self.request.GET.get('show_all') == 'true'
        if show_all:
            kisans = Kisan.objects.all()  # Fetch all kisans if "show_all" is true

        # Calculate total available land
        total_available_land = kisans.filter(is_sold=False).aggregate(total_area=Sum('area_in_beegha')).get('total_area', 0)
        total_available_land = total_available_land or 0  # Default to 0 if None

        # Total land in sqft
        total_land_in_sqft = total_available_land * 27200

        context['kisans'] = kisans
        context['total_land_in_sqft'] = total_land_in_sqft
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['show_all'] = show_all

        return context

    def convert_to_date(self, date_str):
        """
        Convert date string to a datetime.date object. 
        If the input is already a date object, it will return it as is.
        """
        if isinstance(date_str, str):
            return parser.parse(date_str).date()
        return date_str  # If it's already a date object, return it as is.



class KisanUpdateView(OrganisorAndLoginRequiredMixin,UpdateView):

    model = Kisan
    fields = [
        'first_name', 'last_name', 'contact_number', 'address',
        'khasra_number', 'area_in_beegha', 'land_costing', 'development_costing',
        'kisan_payment', 'land_address', 'payment_to_kisan', 'basic_sales_price',
    ]
    template_name = 'kisan/kisan_update.html'  # Updated template name
    success_url = reverse_lazy('leads:kisan_list')

# View for deleting Kisan

class KisanDeleteView(OrganisorAndLoginRequiredMixin,DeleteView):
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



from .models import Salary  # Replace with your Salary model
def export_salaries_to_csv(request):
    # Get the start_date and end_date from the request's GET parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Start building the response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="salaries.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Agent Name', 'Commission', 'Payment Date', 'Property ID'])  # Adjust columns as needed
    
    # Start with all salaries, but apply filters if date range is provided
    salaries = Salary.objects.all()

    # Filter salaries based on the date range if provided
    if start_date:
        salaries = salaries.filter(payment_date__gte=start_date)  # Greater than or equal to start_date
    if end_date:
        salaries = salaries.filter(payment_date__lte=end_date)  # Less than or equal to end_date

    # Write the salary data rows for the filtered data
    for salary in salaries:
        writer.writerow([
            salary.agent.username,  # Assuming agent has a user relation with username
            salary.base_salary,
            salary.payment_date,  # Format the payment date as needed
            salary.property.title if salary.property else 'N/A'  # Handle the case if there's no property
        ])
    
    return response




from .models import Kisan  # Replace with your Kisan model

import csv
from django.http import HttpResponse
from .models import Kisan

def export_kisans_to_csv(request):
    # Handle date range filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()  # Default to last 30 days if no start_date
    if not end_date:
        end_date = timezone.now().date()  # Default to today if no end_date

    try:
        # Convert to date objects if they are strings
        start_date = convert_to_date(start_date)
        end_date = convert_to_date(end_date)
    except ValueError:
        start_date = (timezone.now() - timedelta(days=30)).date()  # Fallback on error
        end_date = timezone.now().date()

    # Handle showing all Kisans
    show_all = request.GET.get('show_all') == 'true'
    if show_all:
        kisans = Kisan.objects.all()  # Fetch all kisans if "show_all" is true
    else:
        # Filter Kisans based on the date range
        kisans = Kisan.objects.filter(date_added__range=[start_date, end_date])

    # Start building the response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="kisans.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'First Name', 'Last Name', 'Contact', 'Khasra Number', 'Area in Beegha', 'Land Cost', 'Date Added'])  # Adjust columns as needed

    # Write Kisan data rows
    for kisan in kisans:
        writer.writerow([
            kisan.id,
            kisan.first_name,
            kisan.last_name,
            kisan.contact_number,
            kisan.khasra_number,
            kisan.area_in_beegha,
            kisan.land_costing,
            kisan.date_added  # You can adjust this column as needed
        ])

    return response

def convert_to_date(date_str):
    """
    Convert date string to a datetime.date object.
    If the input is already a date object, it will return it as is.
    """
    if isinstance(date_str, str):
        return parser.parse(date_str).date()
    return date_str  # If it's already a date object, return it as is.










from django.forms import modelformset_factory
from django.shortcuts import render, redirect
from .forms import BillForm, BillItemForm
from .models import Bill, BillItem
from django.http import HttpResponse
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from num2words import num2words

# Function to convert number to words
def convert_number_to_words(amount):
    return num2words(amount)

# Function to generate PDF
def render_to_pdf(template_name, context):
    template = get_template(template_name)
    html = template.render(context)
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return pdf

# Create Bill and Bill Items
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal, ROUND_HALF_UP
from num2words import num2words
from .forms import BillForm, BillItemForm
from .models import Bill, BillItem
# from weasyprint import HTML
from django.template.loader import render_to_string

# def render_to_pdf(template_src, context_dict):
#     html_string = render_to_string(template_src, context_dict)
#     pdf_file = HTML(string=html_string).write_pdf()
#     return pdf_file

from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import BillForm, BillItemForm
from .models import Bill, BillItem
from decimal import Decimal, ROUND_HALF_UP
from num2words import num2words
# from .utils import render_to_pdf  # Assuming you have a utility to render PDF

from django.shortcuts import render, redirect
from decimal import Decimal


class BillListView(OrganisorAndLoginRequiredMixin,ListView):
    model = Bill
    template_name = 'billing/invoice_list.html'
    context_object_name = 'bills'

    def get_queryset(self):
        queryset = Bill.objects.all().order_by('-invoice_date')
        search_query = self.request.GET.get('search', None)
        
        # Filter for bills created within the last month by default
        one_month_ago = timezone.now() - timedelta(days=30)
        if search_query:
            # Search for bills by bill number or buyer name
            queryset = queryset.filter(
                Q(bill_number__icontains=search_query) |
                Q(buyer_name__icontains=search_query)
            )
        else:
            queryset = queryset.filter(invoice_date__gte=one_month_ago)
        
        return queryset

# from weasyprint import HTML 
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from django.conf import settings

def download_invoice(request, bill_id):
    try:
        # Get the bill object
        bill = Bill.objects.get(id=bill_id)

        # Prepare the context for the bill PDF
        context = {
            'bill': bill,
            'items': bill.items.all(),
            'total_amount': bill.total_amount,
            'amount_in_words': num2words(bill.total_amount, lang='en').capitalize(),
        }

        # Render the HTML content using a template (for the PDF)
        html_content = render_to_string('billing/bill_template.html', context)

        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()

        # Convert HTML to PDF using xhtml2pdf
        pisa_status = pisa.CreatePDF(html_content, dest=buffer)

        # Check if PDF was created successfully
        if pisa_status.err:
            return HttpResponse("Error generating PDF.", status=500)

        # Get the PDF from the buffer
        buffer.seek(0)
        pdf = buffer.read()

        # Return the PDF as an HTTP response with the appropriate content type
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bill_{bill.bill_number}.pdf"'

        return response
    except Bill.DoesNotExist:
        # Handle error if the bill is not found
        return HttpResponse("Invoice not found.", status=404)


from django.shortcuts import render, redirect
from .forms import BillForm, BillItemForm
from .models import Bill, BillItem
from django.http import HttpResponse
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings
from num2words import num2words

# Function to convert number to words
def convert_number_to_words(amount):
    return num2words(amount)

# Function to generate PDF
def render_to_pdf(template_name, context):
    template = get_template(template_name)
    html = template.render(context)
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return pdf

# Create Bill and Bill Items
class CreateBillView(OrganisorAndLoginRequiredMixin, ListView):
    model = Bill
    template_name = 'billing/create_bill.html'
    context_object_name = 'bills'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'bill_form': BillForm(),
            'bill_item_forms': [BillItemForm(prefix=str(i)) for i in range(1)],  # Default to one item form
        })
        return context

    def post(self, request, *args, **kwargs):
        bill_form = BillForm(request.POST)

        # Extract list data for each bill item field
        descriptions = request.POST.getlist('description[]')
        quantities = request.POST.getlist('quantity[]')
        rates = request.POST.getlist('rate[]')
        taxes = request.POST.getlist('tax[]')

        # Debug: Print POST data to verify item form submission
        print("Request POST Data:", request.POST)

        if bill_form.is_valid():
            # Save the Bill
            bill = bill_form.save(commit=False)
            bill.save()  # Save to assign an ID to the Bill instance

            total_amount = 0  # Initialize total amount
            product_total_amount = 0
            # total_tax_rate = sum(map(float, taxes))
            # print("Final Total Tax Rate (Sum of Tax Percentages):", total_tax_rate)

            # Loop through items and create BillItem instances
            for i in range(len(descriptions)):
                description = descriptions[i]
                quantity = int(quantities[i])
                rate = float(rates[i])
                tax = float(taxes[i])

                
                item_total_price = quantity * rate
                print("Item Total Price",item_total_price)
                item_total_with_tax = item_total_price + (item_total_price * (tax / 100))
                print("Item Total with tax",item_total_with_tax)

                # Create and save each BillItem
                BillItem.objects.create(
                    bill=bill,
                    description=description,
                    quantity=quantity,
                    rate=rate,
                    tax=tax,
                    total_price=item_total_price
                )
                print("Bill Items are",BillItem)
                total_amount += item_total_with_tax
                print("Accumulated Total Amount with Tax In Loop:", total_amount)

            
            product_total_amount += total_amount
            print("Accumulated Total Amount with Tax:", product_total_amount)
        
            # Add any other charges and finalize Bill's total amount
            bill.total_amount = total_amount + float(bill.other_charges)
            print("bill toal amount",bill.total_amount)
            total_amount += bill.total_amount
            print("new total",total_amount)
            bill.save()

            # Convert total amount to words
            amount_in_words = convert_number_to_words(round(bill.total_amount, 2))
            print(amount_in_words)

            # Prepare the PDF context
            context = {
                'bill': bill,
                'items': bill.items.all(),
                'item_total_with_tax': f"{item_total_with_tax:.2f}",
                'total_amount': f"{bill.total_amount:.2f}",
                'product_total_amount': f"{product_total_amount:.2f}",
                'amount_in_words': amount_in_words,
                # 'total_tax_rate': total_tax_rate, 
            }

            pdf = render_to_pdf('billing/bill_template.html', context)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="bill_{bill.bill_number}.pdf"'
            return response

        # Debug: If form is invalid, print errors
        else:
            bill_form = BillForm()
            print("BillForm errors:", bill_form.errors)

        # If form is invalid, re-render the page with errors
        return render(request, 'billing/create_bill.html', {
            'bill_form': bill_form,
            'bill_item_forms': [BillItemForm(prefix=str(i)) for i in range(len(descriptions))],
        })




from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from .models import Bill, BillItem
from .forms import BillForm, BillItemForm
# Create the BillItemFormSet
BillItemFormSet = modelformset_factory(BillItem, fields=('description', 'quantity', 'rate', 'tax'), extra=1)
