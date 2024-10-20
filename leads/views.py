import logging
import datetime
from datetime import timedelta
from decimal import Decimal
from django.db import models, IntegrityError
from django.db.models import Count
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.views import View, generic
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin # type: ignore
from leads.models import Lead, Agent, Category, FollowUp, Promoter, PlotBooking, Project, EMIPayment, Area, Typeplot
from agents.mixins import OrganisorAndLoginRequiredMixin
from .models import Property, Sale, Salary, Bonus
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
    PropertyModelForm,
    PromoterForm,
    PlotBookingForm
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
        # Sales Report
        sales_data = Sale.objects.values('sale_date').annotate(properties_sold=Count('id')).order_by('sale_date')
        labels = [sale['sale_date'].strftime("%Y-%m-%d") for sale in sales_data]  # Format dates
        data = [sale['properties_sold'] for sale in sales_data] 
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
                'labels': labels,
                'data': data,
                # Add other context variables like total_lead_count, total_sales, etc.
                'total_lead_count': total_lead_count,
                'total_in_past30': total_in_past30,
                'converted_in_past30': converted_in_past30,
                'total_salaries': total_salaries,
                'total_sales': total_sales,
                'total_properties': total_properties,
                'total_promoters': total_promoters,
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
    if request.method == 'POST':
        print(1)
        selected_ids = request.POST.getlist('properties')  # Get list of selected IDs
        # Redirect to the update view with the selected IDs print
        return redirect('leads:property-update', ids=','.join(selected_ids))  # Join IDs as a comma-separated string
    else:
        id = request.GET.get('project_id')
        projects = Project.objects.all()
        properties = Property.objects.filter(project_id= id)
        return render(request,'property/select_properties.html',{'projects':projects,'properties':properties})
    
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

from django.shortcuts import render, redirect, get_object_or_404
from .models import Promoter  # Import the Promoter model
from .forms import PromoterForm  # Import the PromoterForm

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



# PLOT REGISTRATIOn




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
            plot_booking = form.save()
            # Retrieve EMI amount and tenure from the form
            emi_amount = form.cleaned_data.get('emi_amount')
            tenure = form.cleaned_data.get('emi_tenure')

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
            #return redirect('plot_registration/buyers_list.html')
            return render(request, self.template_name, {'form': form, 'agents': agents})

def load_properties(request):
    project_name = request.GET.get('property.title')
    properties = Property.objects.filter(project_name_id=project_name).values('id', 'property.title')
    return JsonResponse(list(properties), safe=False)

class BuyersListView(LoginRequiredMixin, View):
    template_name = 'plot_registration/buyers_list.html'

    def get(self, request, *args, **kwargs):
        buyers = PlotBooking.objects.select_related('Agent').all()
        return render(request, self.template_name, {'buyers': buyers})

def buyer_print_view(request, buyer_id):
    buyer = get_object_or_404(PlotBooking, id=buyer_id)
    context = {'buyer': buyer}
    return render(request, 'plot_registration/buyer_print_template.html', context)

@login_required
def update_delete_buyer(request, id):
    plot_booking = get_object_or_404(PlotBooking, id=id)

    if request.method == 'POST':
        if 'update' in request.POST:
            form = PlotBookingForm(request.POST, instance=plot_booking)
            if form.is_valid():
                form.save()
                return redirect('leads:buyers_list')  # Redirect after updating
        elif 'delete' in request.POST:
            plot_booking.delete()
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