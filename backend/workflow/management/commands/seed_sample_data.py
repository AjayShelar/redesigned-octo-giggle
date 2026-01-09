from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from workflow.models import (
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


class Command(BaseCommand):
    help = "Seed sample workflow data (IT access request)"

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"email": "admin@example.com"}
        )
        if not admin_user.has_usable_password():
            admin_user.set_password("admin")
            admin_user.save(update_fields=["password"])

        UserProfile.objects.get_or_create(user=admin_user, defaults={"role": "admin"})

        workflow, _ = Workflow.objects.get_or_create(name="IT Access Request", defaults={"is_active": True})

        schema_version, _ = SchemaVersion.objects.get_or_create(workflow=workflow, version=1)

        fields = [
            ("requester", "text", True, {}),
            ("department", "enum", True, {"options": ["Engineering", "Finance", "HR"]}),
            ("system", "text", True, {}),
            ("priority", "enum", True, {"options": ["Low", "Medium", "High"]}),
            ("manager_approval", "boolean", False, {}),
        ]
        for name, ftype, required, options in fields:
            SchemaField.objects.get_or_create(
                schema_version=schema_version,
                name=name,
                defaults={"field_type": ftype, "required": required, "options_json": options},
            )

        new_state, _ = State.objects.get_or_create(
            workflow=workflow, name="New", defaults={"order_index": 0, "is_initial": True}
        )
        review_state, _ = State.objects.get_or_create(
            workflow=workflow, name="In Review", defaults={"order_index": 1}
        )
        approved_state, _ = State.objects.get_or_create(
            workflow=workflow, name="Approved", defaults={"order_index": 2}
        )
        done_state, _ = State.objects.get_or_create(
            workflow=workflow, name="Done", defaults={"order_index": 3}
        )

        submit, _ = Transition.objects.get_or_create(
            workflow=workflow,
            name="Submit",
            from_state=new_state,
            to_state=review_state,
            defaults={"order_index": 0},
        )
        approve, _ = Transition.objects.get_or_create(
            workflow=workflow,
            name="Approve",
            from_state=review_state,
            to_state=approved_state,
            defaults={"order_index": 1},
        )
        complete, _ = Transition.objects.get_or_create(
            workflow=workflow,
            name="Complete",
            from_state=approved_state,
            to_state=done_state,
            defaults={"order_index": 2},
        )

        Rule.objects.get_or_create(
            transition=submit,
            name="Require requester",
            defaults={"condition_type": "field_present", "params_json": {"field": "requester"}, "eval_order": 0},
        )
        Rule.objects.get_or_create(
            transition=submit,
            name="Require system",
            defaults={"condition_type": "field_present", "params_json": {"field": "system"}, "eval_order": 1},
        )
        Rule.objects.get_or_create(
            transition=approve,
            name="Manager approval required for High priority",
            defaults={
                "condition_type": "field_equals",
                "params_json": {"field": "priority", "value": "High", "requires": "manager_approval"},
                "eval_order": 0,
            },
        )

        parent = Entity.objects.create(
            workflow=workflow,
            current_state=new_state,
            schema_version=schema_version,
            data_json={
                "requester": "Sam Lee",
                "department": "Engineering",
                "system": "GitHub",
                "priority": "High",
                "manager_approval": False,
            },
            created_by=admin_user,
        )

        approval_task = Entity.objects.create(
            workflow=workflow,
            current_state=review_state,
            schema_version=schema_version,
            parent=parent,
            data_json={
                "requester": "Sam Lee",
                "department": "Engineering",
                "system": "Approval Task",
                "priority": "High",
                "manager_approval": False,
            },
            created_by=admin_user,
        )

        Entity.objects.create(
            workflow=workflow,
            current_state=new_state,
            schema_version=schema_version,
            parent=parent,
            data_json={
                "requester": "Sam Lee",
                "department": "Engineering",
                "system": "Provision Task",
                "priority": "High",
                "manager_approval": False,
            },
            created_by=admin_user,
        )

        Entity.objects.create(
            workflow=workflow,
            current_state=new_state,
            schema_version=schema_version,
            parent=approval_task,
            data_json={
                "requester": "Sam Lee",
                "department": "Engineering",
                "system": "Create SSO account",
                "priority": "High",
                "manager_approval": False,
            },
            created_by=admin_user,
        )

        AuditLog.objects.create(
            entity=parent,
            actor=admin_user,
            action_type="system",
            reason="Seeded sample workflow",
        )

        self.stdout.write(self.style.SUCCESS("Seeded IT Access Request sample data."))
