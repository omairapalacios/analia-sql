from rest_framework import serializers
from .models import ChatSession, ChatMessage
class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=64)
    message = serializers.CharField()

class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()

class ChatSessionSerializer(serializers.ModelSerializer):
    # Lo llenamos desde la vista con annotate(Max(...))
    last_activity = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = ChatSession
        fields = ["session_id", "created_at", "user_label", "last_activity"]

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["role", "content", "created_at"]