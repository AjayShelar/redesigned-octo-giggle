from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Workflow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [models.Index(fields=["is_active"], name="workflow_is_active_idx")],
            },
        ),
        migrations.CreateModel(
            name="SchemaVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "workflow",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="schema_versions", to="workflow.workflow"),
                ),
            ],
            options={
                "unique_together": {("workflow", "version")},
                "indexes": [models.Index(fields=["workflow", "version"], name="schema_version_idx")],
            },
        ),
        migrations.CreateModel(
            name="State",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("order_index", models.PositiveIntegerField(default=0)),
                ("is_initial", models.BooleanField(default=False)),
                (
                    "workflow",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="states", to="workflow.workflow"),
                ),
            ],
            options={
                "unique_together": {("workflow", "name")},
                "indexes": [
                    models.Index(fields=["workflow", "order_index"], name="state_order_idx"),
                    models.Index(fields=["workflow", "is_initial"], name="state_initial_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Transition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("order_index", models.PositiveIntegerField(default=0)),
                (
                    "from_state",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_transitions", to="workflow.state"),
                ),
                (
                    "to_state",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_transitions", to="workflow.state"),
                ),
                (
                    "workflow",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transitions", to="workflow.workflow"),
                ),
            ],
            options={
                "unique_together": {("workflow", "from_state", "to_state", "name")},
                "indexes": [
                    models.Index(fields=["from_state", "to_state"], name="transition_state_idx"),
                    models.Index(fields=["workflow", "order_index"], name="transition_order_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Rule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "condition_type",
                    models.CharField(
                        choices=[
                            ("field_equals", "Field equals"),
                            ("field_present", "Field present"),
                            ("field_in", "Field in list"),
                            ("field_gt", "Field greater than"),
                            ("field_gte", "Field greater than or equal"),
                            ("field_lt", "Field less than"),
                            ("field_lte", "Field less than or equal"),
                        ],
                        max_length=64,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("params_json", models.JSONField(blank=True, default=dict)),
                ("eval_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "transition",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rules", to="workflow.transition"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["transition", "eval_order"], name="rule_eval_idx"),
                    models.Index(fields=["transition", "is_active"], name="rule_active_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SchemaField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("number", "Number"),
                            ("boolean", "Boolean"),
                            ("date", "Date"),
                            ("datetime", "Datetime"),
                            ("enum", "Enum"),
                        ],
                        max_length=32,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("required", models.BooleanField(default=False)),
                ("options_json", models.JSONField(blank=True, default=dict)),
                (
                    "schema_version",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fields", to="workflow.schemaversion"),
                ),
            ],
            options={
                "unique_together": {("schema_version", "name")},
                "indexes": [models.Index(fields=["schema_version", "name"], name="schema_field_idx")],
            },
        ),
        migrations.CreateModel(
            name="Entity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data_json", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "current_state",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entities", to="workflow.state"),
                ),
                (
                    "parent",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="children", to="workflow.entity"),
                ),
                (
                    "schema_version",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entities", to="workflow.schemaversion"),
                ),
                (
                    "workflow",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="entities", to="workflow.workflow"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["current_state"], name="entity_state_idx"),
                    models.Index(fields=["workflow", "created_at"], name="entity_workflow_created_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("state_change", "State change"),
                            ("field_update", "Field update"),
                            ("rule_block", "Rule block"),
                            ("rule_pass", "Rule pass"),
                            ("system", "System"),
                        ],
                        max_length=64,
                    ),
                ),
                ("reason", models.TextField(blank=True)),
                ("metadata_json", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "entity",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_logs", to="workflow.entity"),
                ),
                (
                    "from_state",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_from", to="workflow.state"),
                ),
                (
                    "rule",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="workflow.rule"),
                ),
                (
                    "to_state",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_to", to="workflow.state"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["entity", "created_at"], name="audit_entity_idx"),
                    models.Index(fields=["action_type"], name="audit_action_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin", "Admin"),
                            ("operator", "Operator"),
                            ("viewer", "Viewer"),
                        ],
                        default="operator",
                        max_length=32,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
    ]
