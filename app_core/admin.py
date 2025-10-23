from django.contrib import admin
from .models import Agent, Indicator, ChatSession, ChatMessage
admin.site.register(Agent)
admin.site.register(Indicator)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
