from django import template

register = template.Library()

@register.inclusion_tag('agents/agent_node.html')
def render_agent_node(agent):
    return {'agent': agent}