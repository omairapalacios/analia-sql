from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=64)
    message = serializers.CharField()

class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
