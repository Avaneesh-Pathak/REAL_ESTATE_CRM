from django.urls import path
from django_distill import distill_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views
from .views import (
    LeadListView, LeadDetailView, LeadCreateView, LeadUpdateView, LeadDeleteView,
    AssignAgentView, CategoryListView, CategoryDetailView, LeadCategoryUpdateView,
    CategoryCreateView, CategoryUpdateView, CategoryDeleteView,LeadJsonView,ProjectCreateView,
    FollowUpCreateView, FollowUpUpdateView, FollowUpDeleteView,FollowupList, manage_salary, manage_sale,
    create_salary,create_sale,PropertyListView,SaleListView,SalaryListView,BonusInfoView,select_properties_view,
    PropertyDetailView,PropertyCreateView,PropertyUpdateView,PropertyDeleteView,calculate_emi,DaybookListView,DaybookCreateView,add_promoter,update_delete_promoter,
    PromoterListView,load_properties,PlotRegistrationView,user_profile_view,BalanceUpdateView,
    update_delete_buyer,pay_emi,BuyersListView,GetProjectPriceView,kisan_view,KisanListView,KisanUpdateView,KisanDeleteView
)

app_name = "leads"



urlpatterns = [

    path('sales/', SaleListView.as_view(), name='sale_list'),
    path('profile/<int:user_id>/', user_profile_view, name='user-profile'),
    path('salaries/', SalaryListView.as_view(), name='salary_list'),
    path('my_bonus/', BonusInfoView.as_view(), name='bonus_info'),
    path('create_salary/', create_salary, name='create_salary'),
    path('create_sale/', create_sale, name='create_sale'),
    path('manage_salary/<int:salary_id>/', manage_salary, name='manage_salary'),
    path('sale/manage/<int:sale_id>/', manage_sale, name='manage_sale'),
    path('', LeadListView.as_view(), name='lead-list'),
    path('<int:pk>/',LeadDetailView.as_view(),name='lead-detail'),
    path('<int:pk>/update/',LeadUpdateView.as_view(), name='lead-update'),
    path('<int:pk>/delete/',LeadDeleteView.as_view(), name='lead-delete'),
    path('create/',LeadCreateView.as_view(),name='lead-create'),
    path('json/', LeadJsonView.as_view(), name='lead-list-json'),
    path('<int:pk>/assign-agent/', AssignAgentView.as_view(), name='assign-agent'),
    path('<int:pk>/category/', LeadCategoryUpdateView.as_view(), name='lead-category-update'),
    path('<int:pk>/followups/', FollowupList.as_view(), name='followup-list'),
    path('<int:pk>/followups/create/', FollowUpCreateView.as_view(), name='lead-followup-create'),
    path('followups/<int:pk>/', FollowUpUpdateView.as_view(), name='lead-followup-update'),
    path('followups/<int:pk>/delete/', FollowUpDeleteView.as_view(), name='lead-followup-delete'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
    path('create-category/', CategoryCreateView.as_view(), name='category-create'),
    #properties
    path('properties/select/', select_properties_view, name='select_properties'),
    path('properties/', PropertyListView.as_view(), name='property_list'),
    path('properties/create/', PropertyCreateView.as_view(), name='property-create'),
    path('properties/create/createProject', ProjectCreateView.as_view(), name='project-create'),
     path('properties/<int:pk>/', PropertyDetailView.as_view(), name='property-detail'),
    path('properties/update/<str:ids>/', PropertyUpdateView.as_view(), name='property-update'),
    path('properties/delete/<str:ids>/', PropertyDeleteView.as_view(), name='delete_properties'),
    # URL for creating a new project
    path('calculate-emi/', calculate_emi, name='calculate_emi'), 
    #DAYBOOK
    path('daybook/', DaybookListView.as_view(), name='daybook_list'),  # URL for listing expenses
    path('daybook/create/', DaybookCreateView.as_view(), name='daybook_create'),
    path('update-balance/', BalanceUpdateView.as_view(), name='update_balance'),
    
    #PROMOTER
    path('promoters/', PromoterListView.as_view(), name='promoter_list'),
    path('promoter/<int:promoter_id>/update-delete/', views.update_delete_promoter, name='update_delete_promoter'),
    path('promoter/add/', add_promoter, name='add_promoter'),  # URL for adding a promoter
    path('register-plot/', PlotRegistrationView.as_view(), name='plot_registration'),
    path('ajax/load-properties/', load_properties, name='ajax_load_properties'),
    path('register/', PlotRegistrationView.as_view(), name='plot_registration'),
    path('register/plot_registration/buyers_list/', BuyersListView.as_view(), name='buyers_list'), 
    path('buyer/<int:buyer_id>/print/', views.buyer_print_view, name='buyer_print'),
    path('buyer/<int:buyer_id>/', views.buyer_detail_view, name='buyer_detail'),
    path('buyer/update-delete/<int:id>/', update_delete_buyer, name='update_delete_buyer'),
    path('emi/pay/<int:payment_id>/',  views.pay_emi, name='pay_emi'),

    path('property/get_price/', GetProjectPriceView.as_view(), name='get_project_price'),
    path('kisan/create/', kisan_view, name='kisan_create'),  # Create Kisan
    path('kisans/', KisanListView.as_view(), name='kisan_list'),
    path('kisan/edit/<int:pk>/', KisanUpdateView.as_view(), name='kisan_edit'),
    path('kisan/delete/<int:pk>/', KisanDeleteView.as_view(), name='kisan_delete'),
  


]   

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)