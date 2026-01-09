from django.conf import settings
from django.db import models


class Workflow(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self) -> str:
        return self.name


class State(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=255)
    order_index = models.PositiveIntegerField(default=0)
    is_initial = models.BooleanField(default=False)

    class Meta:
        unique_together = ("workflow", "name")
        indexes = [
            models.Index(fields=["workflow", "order_index"]),
            models.Index(fields=["workflow", "is_initial"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name}: {self.name}"


class Transition(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="transitions")
    name = models.CharField(max_length=255)
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="outgoing_transitions")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="incoming_transitions")
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("workflow", "from_state", "to_state", "name")
        indexes = [
            models.Index(fields=["from_state", "to_state"]),
            models.Index(fields=["workflow", "order_index"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name}: {self.from_state.name} -> {self.to_state.name}"


class Rule(models.Model):
    class ConditionType(models.TextChoices):
        FIELD_EQUALS = "field_equals", "Field equals"
        FIELD_PRESENT = "field_present", "Field present"
        FIELD_IN = "field_in", "Field in list"
        FIELD_GT = "field_gt", "Field greater than"
        FIELD_GTE = "field_gte", "Field greater than or equal"
        FIELD_LT = "field_lt", "Field less than"
        FIELD_LTE = "field_lte", "Field less than or equal"

    transition = models.ForeignKey(Transition, on_delete=models.CASCADE, related_name="rules")
    name = models.CharField(max_length=255)
    condition_type = models.CharField(max_length=64, choices=ConditionType.choices)
    params_json = models.JSONField(default=dict, blank=True)
    eval_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["transition", "eval_order"]),
            models.Index(fields=["transition", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.transition} :: {self.name}"


class SchemaVersion(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="schema_versions")
    version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("workflow", "version")
        indexes = [models.Index(fields=["workflow", "version"])]

    def __str__(self) -> str:
        return f"{self.workflow.name} v{self.version}"


class SchemaField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"
        DATETIME = "datetime", "Datetime"
        ENUM = "enum", "Enum"

    schema_version = models.ForeignKey(
        SchemaVersion, on_delete=models.CASCADE, related_name="fields"
    )
    name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=32, choices=FieldType.choices)
    required = models.BooleanField(default=False)
    options_json = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("schema_version", "name")
        indexes = [models.Index(fields=["schema_version", "name"])]

    def __str__(self) -> str:
        return f"{self.schema_version} :: {self.name}"


class Entity(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="entities")
    current_state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="entities")
    schema_version = models.ForeignKey(
        SchemaVersion, on_delete=models.PROTECT, related_name="entities"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    data_json = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["current_state"]),
            models.Index(fields=["workflow", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name} #{self.pk}"


class AuditLog(models.Model):
    class ActionType(models.TextChoices):
        STATE_CHANGE = "state_change", "State change"
        FIELD_UPDATE = "field_update", "Field update"
        RULE_BLOCK = "rule_block", "Rule block"
        RULE_PASS = "rule_pass", "Rule pass"
        SYSTEM = "system", "System"

    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action_type = models.CharField(max_length=64, choices=ActionType.choices)
    from_state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_from"
    )
    to_state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_to"
    )
    rule = models.ForeignKey(Rule, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity", "created_at"]),
            models.Index(fields=["action_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_id} {self.action_type}"


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"
        VIEWER = "viewer", "Viewer"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.OPERATOR)

    def __str__(self) -> str:
        return f"{self.user_id} {self.role}"
