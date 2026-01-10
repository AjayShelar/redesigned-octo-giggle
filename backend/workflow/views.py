from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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
from .permissions import RolePermission
from .rules import evaluate_rule
from .serializers import (
    AuditLogSerializer,
    EntitySerializer,
    RuleSerializer,
    SchemaFieldSerializer,
    SchemaVersionSerializer,
    StateSerializer,
    TransitionSerializer,
    UserProfileSerializer,
    WorkflowSerializer,
)


class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": ["admin"]}
    filterset_fields = ["is_active", "name"]


class StateViewSet(viewsets.ModelViewSet):
    queryset = State.objects.select_related("workflow").all()
    serializer_class = StateSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": ["admin"]}
    filterset_fields = ["workflow", "is_initial", "name"]


class TransitionViewSet(viewsets.ModelViewSet):
    queryset = Transition.objects.select_related("workflow", "from_state", "to_state").all()
    serializer_class = TransitionSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": ["admin"]}
    filterset_fields = ["workflow", "from_state", "to_state", "name"]


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.select_related("transition").all()
    serializer_class = RuleSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": ["admin"]}
    filterset_fields = ["transition", "is_active", "condition_type"]


class SchemaVersionViewSet(viewsets.ModelViewSet):
    queryset = SchemaVersion.objects.select_related("workflow").all()
    serializer_class = SchemaVersionSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": ["admin"]}
    filterset_fields = ["workflow", "version"]


class SchemaFieldViewSet(viewsets.ModelViewSet):
    queryset = SchemaField.objects.select_related("schema_version").all()
    serializer_class = SchemaFieldSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": ["admin"]}
    filterset_fields = ["schema_version", "name", "field_type"]


class EntityViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.select_related(
        "workflow", "current_state", "schema_version", "parent", "created_by"
    ).all()
    serializer_class = EntitySerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": ["admin", "operator", "viewer"],
        "retrieve": ["admin", "operator", "viewer"],
        "create": ["admin", "operator"],
        "update": ["admin", "operator"],
        "partial_update": ["admin", "operator"],
        "destroy": ["admin"],
        "transition": ["admin", "operator"],
    }
    filterset_fields = ["workflow", "current_state", "parent", "schema_version"]
    ordering_fields = ["created_at", "updated_at"]

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        entity = self.get_object()
        to_state_id = request.data.get("to_state")
        transition_id = request.data.get("transition")

        if not to_state_id and not transition_id:
            return Response(
                {"detail": "Provide to_state or transition."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if transition_id:
            transition = Transition.objects.filter(id=transition_id).first()
        else:
            transition = Transition.objects.filter(
                workflow=entity.workflow,
                from_state=entity.current_state,
                to_state_id=to_state_id,
            ).first()

        if not transition or transition.workflow_id != entity.workflow_id:
            return Response(
                {"detail": "Invalid transition."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if transition.from_state_id != entity.current_state_id:
            return Response(
                {"detail": "Transition does not match entity state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rules = (
            Rule.objects.filter(transition=transition, is_active=True)
            .order_by("eval_order", "id")
            .all()
        )

        with transaction.atomic():
            for rule in rules:
                passed, reason = evaluate_rule(rule.condition_type, rule.params_json, entity.data_json)
                if not passed:
                    AuditLog.objects.create(
                        entity=entity,
                        actor=request.user if request.user.is_authenticated else None,
                        action_type="rule_block",
                        from_state=entity.current_state,
                        to_state=transition.to_state,
                        rule=rule,
                        reason=reason or "Rule blocked transition",
                    )
                    return Response(
                        {"detail": "Rule blocked transition", "rule": rule.id, "reason": reason},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            from_state = entity.current_state
            entity.current_state = transition.to_state
            entity.save(update_fields=["current_state", "updated_at"])

            AuditLog.objects.create(
                entity=entity,
                actor=request.user if request.user.is_authenticated else None,
                action_type="state_change",
                from_state=from_state,
                to_state=transition.to_state,
                reason=f"Transitioned via {transition.name}",
            )

        return Response(self.get_serializer(entity).data, status=status.HTTP_200_OK)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("entity", "actor", "rule").all()
    serializer_class = AuditLogSerializer
    permission_classes = [RolePermission]
    role_permissions = {"list": ["admin", "operator", "viewer"], "retrieve": ["admin", "operator", "viewer"]}
    filterset_fields = ["entity", "action_type", "rule"]
    ordering_fields = ["created_at"]


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related("user").all()
    serializer_class = UserProfileSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": ["admin"]}
