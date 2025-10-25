from django.contrib import admin
from django.urls import path

from app_core.views import (
    ChatAPIView, chat_page,
    HealthAPIView, SessionListCreateAPIView, SessionDetailAPIView,  # <-- nuevos
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # EXISTENTE
    path('api/chat/', ChatAPIView.as_view(), name='api_chat'),

    # NUEVOS
    path('api/health/', HealthAPIView.as_view(), name='api_health'),
    path('api/sessions/', SessionListCreateAPIView.as_view(), name='api_sessions'),
    path('api/sessions/<str:session_id>/', SessionDetailAPIView.as_view(), name='api_session_detail'),

    # UI
    path('', chat_page, name='chat_page'),
]
