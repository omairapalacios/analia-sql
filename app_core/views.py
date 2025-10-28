import os
from django.db.models import Max
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render
from .serializers import ChatRequestSerializer, ChatResponseSerializer
from .models import ChatSession, ChatMessage
from .services.sql_agent import ask_sql_agent

from .serializers import (
    ChatRequestSerializer, ChatResponseSerializer,
    ChatSessionSerializer, ChatMessageSerializer,  # <-- nuevos
)
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

        try:
            # Consultar agente
            reply = ask_sql_agent(session_id=session_id, user_query=message)

            # Guardar respuesta
            ChatMessage.objects.create(session=sess, role='assistant', content=reply, created_at=timezone.now())

            return Response(ChatResponseSerializer({"reply": reply}).data, status=status.HTTP_200_OK)
        except RuntimeError as e:
            error_message = str(e)
            # Guardar el error como respuesta del asistente para mantener el histórico
            ChatMessage.objects.create(
                session=sess, 
                role='assistant', 
                content=f"Error: {error_message}", 
                created_at=timezone.now()
            )
            return Response(
                {"error": error_message}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return Response(
                {"error": "Error interno del servidor"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def chat_page(request):
    # Render de la UI simple
    return render(request, "chat.html")


class HealthAPIView(APIView):
    def get(self, request):
        provider = os.getenv("MODEL_PROVIDER", "vertexai")
        db_engine = settings.DATABASES["default"]["ENGINE"]
        try:
            last_msg = ChatMessage.objects.latest("created_at")
            last_ts = last_msg.created_at
        except ChatMessage.DoesNotExist:
            last_ts = None
        return Response({
            "model_provider": provider,
            "db_engine": db_engine,
            "last_message_at": last_ts,
            "server_time": timezone.now(),
        })


# --- NUEVO: listar/crear sesiones ---
class SessionListCreateAPIView(APIView):
    """
    GET: lista sesiones con última actividad (ordenadas por reciente)
    POST: crea/actualiza una sesión. Body: {"session_id":"...", "user_label":"opcional"}
    """
    def get(self, request):
        sessions = (
            ChatSession.objects
            .annotate(last_activity=Max("messages__created_at"))
            .order_by("-last_activity", "-created_at")
        )
        return Response(ChatSessionSerializer(sessions, many=True).data)

    def post(self, request):
        sid = (request.data.get("session_id") or "").strip()
        if not sid:
            return Response({"detail": "session_id es requerido"}, status=400)
        label = (request.data.get("user_label") or "").strip()
        sess, created = ChatSession.objects.get_or_create(
            session_id=sid, defaults={"user_label": label}
        )
        if not created and label:
            sess.user_label = label
            sess.save(update_fields=["user_label"])
        return Response(ChatSessionSerializer(sess).data, status=201 if created else 200)


# --- NUEVO: detalle/elim de una sesión ---
class SessionDetailAPIView(APIView):
    """
    GET /api/sessions/<session_id>/    -> devuelve historial (mensajes ordenados)
    DELETE /api/sessions/<session_id>/ -> elimina sesión e historial
    """
    def get(self, request, session_id):
        try:
            sess = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response({"detail": "No existe la sesión"}, status=404)
        msgs = ChatMessage.objects.filter(session=sess).order_by("created_at")
        return Response(ChatMessageSerializer(msgs, many=True).data)

    def delete(self, request, session_id):
        ChatSession.objects.filter(session_id=session_id).delete()
        return Response(status=204)