# from django import forms
# from django.contrib.auth import get_user_model
# from django.contrib.auth.forms import UserCreationForm

# User = get_user_model()



# class AgentModelForm(forms.ModelForm):
#     class Meta:
#         model=User
#         fields =(
#             'email',
#             'username',
#             'first_name',
#             'last_name'
            
#         )
from django import forms
from django.contrib.auth import get_user_model
#from django.contrib.auth.forms import UserCreationForm
from leads.models import Agent

User = get_user_model()

class AgentModelForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            
        )

class AgentCreateForm(forms.ModelForm):
    parent_agent = forms.ModelChoiceField(
        queryset=Agent.objects.none(),  # Start with no agents
        required=False,
        label="Parent Agent",
        help_text="Select a parent agent if applicable."
    )
    # commission_percentage = forms.DecimalField(
    #     max_digits=5,
    #     decimal_places=2,
    #     required=True,
    #     help_text="Commission percentage to share with parent agent."
    # )
    # level = forms.ChoiceField(
    #     choices=[(i, f'Level {i}') for i in range(1, 6)],  # Levels from 1 to 5
    #     required=True,
    #     label="Agent Level",
    #     help_text="Select the level of the agent."
    # )

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'parent_agent',
           
             
        )

    def __init__(self, *args, **kwargs):
        organisation = kwargs.pop('organisation', None)
        super().__init__(*args, **kwargs)

        # Filter the queryset of parent agents based on the organisation
        if organisation:
            self.fields['parent_agent'].queryset = Agent.objects.filter(organisation=organisation)



class AgentUpdateForm(forms.ModelForm):
    parent_agent = forms.ModelChoiceField(
        queryset=Agent.objects.none(),
        required=False,
        label="Parent Agent",
        help_text="Select a parent agent if applicable."
    )
    commission_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
        help_text="Commission percentage to share with parent agent."
    )
    level = forms.IntegerField(
        required=True,
        help_text="Enter the agent level."
    )

    class Meta:
        model = Agent
        fields = ['user', 'parent_agent', 'commission_percentage', 'level']

    def __init__(self, *args, **kwargs):
        organisation = kwargs.pop('organisation', None)
        super().__init__(*args, **kwargs)

        # Set the queryset for parent_agent to show all agents in the same organization
        if organisation:
            self.fields['parent_agent'].queryset = Agent.objects.filter(organisation=organisation)
