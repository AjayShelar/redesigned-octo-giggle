from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    AuditLog,
    Entity,
    Rule,
    SchemaField,
    SchemaVersion,
    State,
    Transition,
    UserProfile,
    Workflow,
)


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "workflow", "name", "order_index", "is_initial"]


class TransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transition
        fields = ["id", "workflow", "name", "from_state", "to_state", "order_index"]


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = [
            "id",
            "transition",
            "name",
            "condition_type",
            "params_json",
            "eval_order",
            "is_active",
        ]


class SchemaVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaVersion
        fields = ["id", "workflow", "version", "created_at"]
        read_only_fields = ["created_at"]


class SchemaFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaField
        fields = [
            "id",
            "schema_version",
            "name",
            "field_type",
            "required",
            "options_json",
        ]


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = [
            "id",
            "workflow",
            "current_state",
            "schema_version",
            "parent",
            "data_json",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "entity",
            "actor",
            "action_type",
            "from_state",
            "to_state",
            "rule",
            "reason",
            "metadata_json",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "user", "role"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email"]
