from django.urls import path
from .views import (
    LeadListView, LeadDetailView, LeadCreateView, LeadUpdateView, LeadDeleteView,
    AssignAgentView, CategoryListView, CategoryDetailView, LeadCategoryUpdateView,
    CategoryCreateView, CategoryUpdateView, CategoryDeleteView,LeadJsonView,
    FollowUpCreateView, FollowUpUpdateView, FollowUpDeleteView,FollowupList, manage_salary, manage_sale,
    create_salary,create_sale,PropertyListView,SaleListView,SalaryListView,BonusInfoView,PropertyDetailView,PropertyCreateView,PropertyUpdateView,PropertyDeleteView
)

app_name = "leads"

urlpatterns = [
    path('properties/', PropertyListView.as_view(), name='property_list'),
    path('sales/', SaleListView.as_view(), name='sale_list'),
    path('salaries/', SalaryListView.as_view(), name='salary_list'),
    path('my_bonus/', BonusInfoView.as_view(), name='bonus_info'),
    path('create_salary/', create_salary, name='create_salary'),
    path('create_sale/', create_sale, name='create_sale'),
    path('manage_salary/', manage_salary, name='manage_salary'),
    path('manage_sale/', manage_sale, name='manage_sale'),
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
    path('properties/create/', PropertyCreateView.as_view(), name='property_create'),
    path('properties/<int:pk>/', PropertyDetailView.as_view(), name='property-detail'),
    path('properties/<int:pk>/update/', PropertyUpdateView.as_view(), name='property-update'),
    path('properties/<int:pk>/delete/', PropertyDeleteView.as_view(), name='property-delete'),
]