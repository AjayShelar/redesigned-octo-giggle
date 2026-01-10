from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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


class WorkflowCRUDTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="testpass")
        self.client.force_authenticate(self.user)
        UserProfile.objects.create(user=self.user, role="admin")

    def test_create_workflow(self):
        url = reverse("workflow-list")
        resp = self.client.post(url, {"name": "Onboarding", "is_active": True}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workflow.objects.count(), 1)

    def test_workflow_create_requires_admin(self):
        UserProfile.objects.filter(user=self.user).update(role="viewer")
        url = reverse("workflow-list")
        resp = self.client.post(url, {"name": "Denied", "is_active": True}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_state_transition_rule_crud(self):
        workflow = Workflow.objects.create(name="Test", is_active=True)
        state_a = State.objects.create(workflow=workflow, name="A", order_index=0, is_initial=True)
        state_b = State.objects.create(workflow=workflow, name="B", order_index=1)

        transition_url = reverse("transition-list")
        resp = self.client.post(
            transition_url,
            {
                "workflow": workflow.id,
                "name": "A->B",
                "from_state": state_a.id,
                "to_state": state_b.id,
                "order_index": 0,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        transition_id = resp.data["id"]

        rule_url = reverse("rule-list")
        resp = self.client.post(
            rule_url,
            {
                "transition": transition_id,
                "name": "Require field",
                "condition_type": "field_present",
                "params_json": {"field": "requester"},
                "eval_order": 0,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rule.objects.count(), 1)

    def test_schema_crud(self):
        workflow = Workflow.objects.create(name="Test", is_active=True)
        sv_url = reverse("schemaversion-list")
        resp = self.client.post(sv_url, {"workflow": workflow.id, "version": 1}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        schema_version_id = resp.data["id"]

        sf_url = reverse("schemafield-list")
        resp = self.client.post(
            sf_url,
            {
                "schema_version": schema_version_id,
                "name": "requester",
                "field_type": "text",
                "required": True,
                "options_json": {},
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SchemaField.objects.count(), 1)

    def test_entity_crud(self):
        workflow = Workflow.objects.create(name="Test", is_active=True)
        sv = SchemaVersion.objects.create(workflow=workflow, version=1)
        state = State.objects.create(workflow=workflow, name="New", order_index=0, is_initial=True)

        UserProfile.objects.filter(user=self.user).update(role="operator")

        url = reverse("entity-list")
        resp = self.client.post(
            url,
            {
                "workflow": workflow.id,
                "current_state": state.id,
                "schema_version": sv.id,
                "data_json": {"requester": "Sam"},
                "created_by": self.user.id,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Entity.objects.count(), 1)

    def test_audit_logs_read_only(self):
        workflow = Workflow.objects.create(name="Test", is_active=True)
        sv = SchemaVersion.objects.create(workflow=workflow, version=1)
        state = State.objects.create(workflow=workflow, name="New", order_index=0, is_initial=True)
        entity = Entity.objects.create(
            workflow=workflow,
            current_state=state,
            schema_version=sv,
            data_json={},
            created_by=self.user,
        )
        AuditLog.objects.create(entity=entity, actor=self.user, action_type="system")

        url = reverse("auditlog-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(url, {"entity": entity.id, "action_type": "system"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_profile_crud(self):
        url = reverse("userprofile-list")
        resp = self.client.post(
            url, {"user": self.user.id, "role": "admin"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_entity_filtering(self):
        workflow = Workflow.objects.create(name="FilterTest", is_active=True)
        sv = SchemaVersion.objects.create(workflow=workflow, version=1)
        state_a = State.objects.create(workflow=workflow, name="A", order_index=0, is_initial=True)
        state_b = State.objects.create(workflow=workflow, name="B", order_index=1)

        UserProfile.objects.filter(user=self.user).update(role="operator")

        Entity.objects.create(
            workflow=workflow,
            current_state=state_a,
            schema_version=sv,
            data_json={"requester": "A"},
            created_by=self.user,
        )
        Entity.objects.create(
            workflow=workflow,
            current_state=state_b,
            schema_version=sv,
            data_json={"requester": "B"},
            created_by=self.user,
        )

        url = reverse("entity-list")
        resp = self.client.get(url, {"current_state": state_a.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
