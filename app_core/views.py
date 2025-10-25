from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render
from .serializers import ChatRequestSerializer, ChatResponseSerializer
from .models import ChatSession, ChatMessage
from .services.sql_agent import ask_sql_agent

class ChatAPIView(APIView):
    def post(self, request):
        ser = ChatRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        session_id = ser.validated_data['session_id']
        message = ser.validated_data['message']

        # Crear/obtener sesión
        sess, _ = ChatSession.objects.get_or_create(session_id=session_id)

        # Guardar mensaje de usuario
        ChatMessage.objects.create(session=sess, role='user', content=message, created_at=timezone.now())

        # Consultar agente
        reply = ask_sql_agent(session_id=session_id, user_query=message)

        # Guardar respuesta
        ChatMessage.objects.create(session=sess, role='assistant', content=reply, created_at=timezone.now())

        return Response(ChatResponseSerializer({"reply": reply}).data, status=status.HTTP_200_OK)

def chat_page(request):
    # Render de la UI simple
    return render(request, "chat.html")
