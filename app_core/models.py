from django.db import models

class Agent(models.Model):
    code = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=200)
    site = models.CharField(max_length=100, blank=True)
    campaign = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.full_name}"

class Indicator(models.Model):
    name = models.CharField(max_length=100)
    campaign = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    value = models.FloatField()
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['name','campaign','date'])]
        verbose_name = 'Indicator'
        verbose_name_plural = 'Indicators'

class ChatSession(models.Model):
    session_id = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user_label = models.CharField(max_length=100, blank=True)  # opcional

class ChatMessage(models.Model):
    ROLE_CHOICES = (('user','user'), ('assistant','assistant'),)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)