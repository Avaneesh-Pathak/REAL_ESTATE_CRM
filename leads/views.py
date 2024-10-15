import logging
import datetime
from django import contrib
from django.contrib import messages
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, reverse,get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import generic
from django.views.generic import ListView
from .models import Property, Sale, Salary, Bonus
from leads.models import Category
from agents.mixins import OrganisorAndLoginRequiredMixin
from django.forms import modelformset_factory
from django.db import models
from .models import Lead, Agent, Category, FollowUp,Promoter
from .forms import (
    LeadForm, 
    LeadModelForm, 
    CustomUserCreationForm, 
    AssignAgentForm, 
    LeadCategoryUpdateForm,
    CategoryModelForm,
    FollowUpModelForm,SalaryForm,SaleForm,
    PropertyModelForm,PromoterForm
)


logger = logging.getLogger(__name__)


# CRUD+L - Create, Retrieve, Update and Delete + List


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated: 
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

def landing_page(request):
    return render(request, "landing.html")


class DashboardView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)

        user = self.request.user

        # How many leads we have in total
        total_lead_count = Lead.objects.filter(organisation=user.userprofile).count()

        # How many new leads in the last 30 days
        thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)
        # Total sales for the organisation          
        total_salaries = Salary.objects.count()
        # Total sales for the organisation
        total_sales = Sale.objects.count()
        
        # Total properties managed by the organisation
        total_properties = Property.objects.count()
        # Total Promoters 
        total_promoters = Promoter.objects.count()

        total_in_past30 = Lead.objects.filter(
            organisation=user.userprofile,
            date_added__gte=thirty_days_ago
        ).count()

        # How many converted leads in the last 30 days
        converted_category = Category.objects.filter(name="Converted").first()
        converted_in_past30 = Lead.objects.filter(
            organisation=user.userprofile,
            category=converted_category,
            converted_date__gte=thirty_days_ago
        ).count()

        context.update({
            "total_lead_count": total_lead_count,
            "total_in_past30": total_in_past30,
            "converted_in_past30": converted_in_past30,
            "total_salaries": total_salaries,
            "total_sales": total_sales,
            "total_properties": total_properties,
            "total_promoters": total_promoters,
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
        send_mail(
            subject="A lead has been created",
            message="Go to the site to see the new lead",
            from_email="test@test.com",
            recipient_list=["test2@test.com"]
        )
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

class PropertyDetailView(LoginRequiredMixin, generic.DetailView):
    model = Property
    template_name = 'property/property_detail.html'  # Update with your template path
    context_object_name = 'property'

    def get_queryset(self):
        return Property.objects.filter(agent__user=self.request.user)

        
# views.py
from django.views import View
from django.forms import modelformset_factory

class PropertyCreateView(LoginRequiredMixin, View):
    template_name = 'property/property_create.html'

    def get(self, request):
        # Render the initial form for number of properties and common attributes
        return render(request, self.template_name)

    def post(self, request):
        # Get the number of properties to create and common attributes
        num_properties = int(request.POST.get('num_properties', 1))
        property_name = request.POST.get('property_name', '')

        # Create the properties in the database
        for _ in range(num_properties):
            Property.objects.create(
                title=property_name,
                description=100,  # Example size, modify as needed
                address='Default Location',  # Example location, modify as needed
                price=100000.00  # Example price, modify as needed
            )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('leads:property_list')  # Redirect to property list after creation  # Redirect to property list after successful update

def add_property(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('desc')
        address = request.POST.get('address')
        price = request.POST.get('price')
        # agent = request.POST.get('agent')
        # organisation = request.POST.get('organisation')

        # Create and save the new Property
        new_property = Property(
            title=title,
            description=desc,
            address=address,
            price=price,
            # agent=agent,
            # organisation=organisation
        )
        new_property.save()
        return HttpResponse("Property added successfully!")

    return render(request, 'property_list.html')  # Adjust to your template


class PropertyUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = 'property/property_update.html'  # Update with your template path
    form_class = PropertyModelForm

    def get_queryset(self):
        return Property.objects.filter(agent__user=self.request.user)

    def get_success_url(self):
        return reverse('property_list')  # Redirect to property list after successful update

    def form_valid(self, form):
        form.save()
        messages.info(self.request, "Property updated successfully.")
        return super(PropertyUpdateView, self).form_valid(form)

class PropertyDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Property
    template_name = 'property/property_delete.html'  # Update with your template path

    def get_queryset(self):
        return Property.objects.filter(agent__user=self.request.user)

    def get_success_url(self):
        return reverse('property_list')  # Redirect to property list after successful deletion

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Property deleted successfully.")
        return super(PropertyDeleteView, self).delete(request, *args, **kwargs)


class SaleListView(LoginRequiredMixin, generic.ListView):
    model = Sale
    template_name = 'sale/sale_list.html'  # Update with your template path
    context_object_name = 'sales'

class SalaryListView(LoginRequiredMixin, generic.ListView):
    model = Salary
    template_name = 'salary/salary_list.html'  # Update with your template path
    context_object_name = 'salaries'

class BonusInfoView(LoginRequiredMixin, generic.ListView):
    model = Bonus
    template_name = 'leads/bonus_info.html'  # Update with your template path
    context_object_name = 'bonuses'



# Project
from django.shortcuts import render
from .models import Plot

def plot_status_view(request):
    projects = Project.objects.all()  # Fetch all project names
    project_name = request.GET.get('project_name', None)
    block_code = request.GET.get('block_code', 'All')
    
    plots = Plot.objects.none()  # Initialize with no plots
    if project_name:
        plots = Plot.objects.filter(project__name=project_name)
        if block_code != 'All':
            plots = plots.filter(project__block_code=block_code)

    return render(request, 'project\plot_status.html', {
        'projects': projects, 
        'plots': plots,
        'selected_project': project_name,
        'block_code': block_code
    })
from django.shortcuts import render, redirect
from .forms import ProjectForm
from .models import Project, Plot

def create_project_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            # Create the project
            project_name = form.cleaned_data['name']
            block_code = form.cleaned_data['block_code']
            start_plot = form.cleaned_data['start_plot']
            end_plot = form.cleaned_data['end_plot']

            # Save the project
            project = Project.objects.create(name=project_name, block_code=block_code)

            # Create plots for the project
            for plot_no in range(start_plot, end_plot + 1):
                Plot.objects.create(project=project, plot_no=f"{block_code}-{plot_no}")

            return redirect('project/plot_status')  # Redirect to project status page after creation
    else:
        form = ProjectForm()

    return render(request, 'project/create_project.html', {'form': form})




# EMI
from decimal import Decimal, InvalidOperation, getcontext

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
from .models import Daybook
from django.utils import timezone
from .forms import DaybookEntryForm  # Update the import statement
from django.db.models import Sum


def daybook_list(request):
    # Get today's date
    today = timezone.now().date()

    # Calculate today's expenses
    todays_expenses = Daybook.objects.filter(date=today)
    total_todays_expenses = sum(expense.amount for expense in todays_expenses)

    # Get current balance (assuming it's stored in a variable or model)
    current_balance = 25000  # Replace this with your actual current balance logic
    updated_balance = current_balance - total_todays_expenses

    context = {
        'expenses': todays_expenses,
        'total_balance': updated_balance,
        'todays_expense': total_todays_expenses,
    }
    return render(request, 'Daybook/daybook_list.html', context)

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

# Promoter List View
# leads/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Promoter  # Import the Promoter model
from .forms import PromoterForm  # Import the PromoterForm

def promoter_list(request):
    promoters = Promoter.objects.all()
    return render(request, 'promoter/promoter_list.html', {'promoters': promoters})

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

#PLOT REGISTRATION


from .forms import PlotBookingForm
from .models import Project, Promoter

def plot_registration(request):
    if request.method == 'POST':
        form = PlotBookingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')  # Redirect to a success page after saving
    else:
        form = PlotBookingForm()
    return render(request, 'plot_registration/plot_registration.html', {'form': form})