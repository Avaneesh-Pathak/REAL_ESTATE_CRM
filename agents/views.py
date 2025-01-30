import random
from django import forms
from django.db.models import Sum
from django.utils import timezone
from django.core.mail import send_mail
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse,get_object_or_404
from leads.models import Agent,Salary
from .forms import AgentModelForm,AgentCreateForm,AgentUpdateForm
from .mixins import OrganisorAndLoginRequiredMixin ,AgentAndLoginRequiredMixin



class AgentListView(AgentAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/agent_list.html"
    
    def get_queryset(self):
        # organisation = self.request.user.userprofile
        return Agent.objects.all()



class AgentCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    template_name = "agents/agent_create.html"
    form_class = AgentCreateForm

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # kwargs['organisation'] = self.request.user.userprofile  # Pass the organisation
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(f"{random.randint(0, 1000000)}")  # Setting a random password
        user.save()

        # Get the cleaned data from the form
        parent_agent = form.cleaned_data.get('parent_agent')
        # commission_percentage = form.cleaned_data.get('commission_percentage')

        # Check if the parent agent exists and if commission percentage is valid
        if parent_agent:
            # Check if the parent agent's level is at maximum
            if parent_agent.level >= 5:
                print('Level Exceeds')
                form.add_error(None, "Exceeding maximum level of agent.")  # Use None to add a non-field error
                return self.form_invalid(form)
            
            # Validate the commission percentage against existing sub-agents
            # total_commission_shared = sum(sub_agent.commission_percentage for sub_agent in parent_agent.sub_agents.all())
            # if total_commission_shared + commission_percentage > 20:
            #     form.add_error('commission_percentage', "Total commission shared cannot exceed 20%.")
            #     return self.form_invalid(form)

            # If validations pass, set the level of the new agent
            else:
                level = parent_agent.level + 1  # Increment level based on parent agent
        else:
            level = 1  # Top-level agent if no parent agent is provided

            

        

        # # Create and save the Agent instance
        Agent.objects.create(
            user=user,
            parent_agent=parent_agent,
            # commission_percentage=commission_percentage,
            
            level=level
        )

        return super(AgentCreateView, self).form_valid(form)


class AgentDetailView(AgentAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/agent_detail.html"
    context_object_name = "agent"

    def get_queryset(self):
        # organisation = self.request.user.userprofile
        return Agent.objects.all()
    

class AgentUpdateView(OrganisorAndLoginRequiredMixin, generic.UpdateView):
    template_name = "agents/agent_update.html"
    form_class = AgentUpdateForm

    def get_object(self, queryset=None):
        # Access the primary key from URL kwargs and get the object
        pk = self.kwargs.get('pk')
        return get_object_or_404(Agent, pk=pk)

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass additional context if needed (e.g., current organisation)
        # kwargs['organisation'] = self.request.user
        return kwargs

    def get_queryset(self):
        # Adjust this query as needed to filter agents by organization, if applicable
        return Agent.objects.all()

    # def form_valid(self, form):
    #     # Get the instance of Agent being updated
    #     agent = self.get_object()
        
    #     # Get the cleaned data from the form
    #     parent_agent = form.cleaned_data.get('parent_agent')

    #     # Check if the parent agent exists and if commission percentage is valid
    #     if parent_agent:
    #         # Check if the parent agent's level is at maximum
    #         if parent_agent.level >= 5:
    #             form.add_error(None, "Exceeding maximum level of agent.")  # Non-field error
    #             return self.form_invalid(form)
            
    #         # Set the new level based on the parent agent’s level
    #         agent.level = parent_agent.level + 1
    #         print(agent.level)
    #     else:
    #         agent.level = 1  # Top-level agent if no parent agent is provided
        
    #     # Update the agent fields
    #     agent.parent_agent = parent_agent

    #     # agent.level = 
    #     # agent.save()  # Save changes to the database
    #     print(agent.level)

    #     # return super().form_valid(form)

class AgentDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/agent_delete.html"
    context_object_name = "agent"

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        # organisation = self.request.user.userprofile
        return Agent.objects.all()
from django.views import generic

class AgentTreeView(AgentAndLoginRequiredMixin, generic.TemplateView):
    template_name = 'agents/agent_tree.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch the logged-in user
        user = self.request.user
        
        # Fetch all agents if the user is an organisor
        if user.is_organisor:
            agents = Agent.objects.all()
        else:
            # Fetch only the logged-in agent and their descendants
            agents = self.get_agent_and_descendants(user.agent)

        # Create a dictionary to hold agents by their ID
        agent_dict = {agent.id: agent for agent in agents}

        # Create a list to hold agents for tree representation
        tree_agents = []

        # Build the tree structure
        for agent in agents:
            if agent.parent_agent:
                # Instead of append, use the RelatedManager's add method
                parent = agent_dict.get(agent.parent_agent.id)
                if parent:
                    if not hasattr(parent, 'sub_agents_list'):
                        parent.sub_agents_list = []  # Initialize a list if it doesn't exist
                    parent.sub_agents_list.append(agent)  # Append to the list we created
            else:
                tree_agents.append(agent)

        # Add the tree agents to context
        context['agents'] = tree_agents  # Use the list of top-level agents
        return context

    def get_agent_and_descendants(self, agent):
        """
        Recursively fetch the given agent and all their descendants.
        """
        descendants = [agent]
        sub_agents = Agent.objects.filter(parent_agent=agent)
        for sub_agent in sub_agents:
            descendants.extend(self.get_agent_and_descendants(sub_agent))
        return descendants
