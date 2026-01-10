from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from workflow.models import AuditLog, Entity, Rule, SchemaField, SchemaVersion, State, Transition, Workflow
from workflow.models import UserProfile


class WorkflowAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="testpass")
        self.client.force_authenticate(self.user)
        UserProfile.objects.create(user=self.user, role="operator")

        self.workflow = Workflow.objects.create(name="Test Workflow", is_active=True)
        self.schema_version = SchemaVersion.objects.create(workflow=self.workflow, version=1)
        SchemaField.objects.create(
            schema_version=self.schema_version,
            name="requester",
            field_type="text",
            required=True,
        )
        SchemaField.objects.create(
            schema_version=self.schema_version,
            name="priority",
            field_type="enum",
            required=False,
            options_json={"options": ["Low", "High"]},
        )
        SchemaField.objects.create(
            schema_version=self.schema_version,
            name="manager_approval",
            field_type="boolean",
            required=False,
        )

        self.state_new = State.objects.create(
            workflow=self.workflow, name="New", order_index=0, is_initial=True
        )
        self.state_review = State.objects.create(
            workflow=self.workflow, name="Review", order_index=1, is_initial=False
        )
        self.state_done = State.objects.create(
            workflow=self.workflow, name="Done", order_index=2, is_initial=False
        )

        self.transition_submit = Transition.objects.create(
            workflow=self.workflow,
            name="Submit",
            from_state=self.state_new,
            to_state=self.state_review,
            order_index=0,
        )
        self.transition_complete = Transition.objects.create(
            workflow=self.workflow,
            name="Complete",
            from_state=self.state_review,
            to_state=self.state_done,
            order_index=1,
        )

        Rule.objects.create(
            transition=self.transition_submit,
            name="Require requester",
            condition_type="field_present",
            params_json={"field": "requester"},
            eval_order=0,
        )
        Rule.objects.create(
            transition=self.transition_complete,
            name="Require manager approval for High priority",
            condition_type="field_equals",
            params_json={"field": "priority", "value": "High", "requires": "manager_approval"},
            eval_order=0,
        )

    def test_transition_blocked_by_rule(self):
        entity = Entity.objects.create(
            workflow=self.workflow,
            current_state=self.state_new,
            schema_version=self.schema_version,
            data_json={"priority": "Low"},
            created_by=self.user,
        )

        url = reverse("entity-transition", kwargs={"pk": entity.id})
        resp = self.client.post(url, {"transition": self.transition_submit.id}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("detail"), "Rule blocked transition")
        self.assertTrue(
            AuditLog.objects.filter(
                entity=entity, action_type="rule_block", rule__name="Require requester"
            ).exists()
        )

    def test_transition_success(self):
        entity = Entity.objects.create(
            workflow=self.workflow,
            current_state=self.state_new,
            schema_version=self.schema_version,
            data_json={"requester": "Sam", "priority": "Low"},
            created_by=self.user,
        )

        url = reverse("entity-transition", kwargs={"pk": entity.id})
        resp = self.client.post(url, {"transition": self.transition_submit.id}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        entity.refresh_from_db()
        self.assertEqual(entity.current_state_id, self.state_review.id)
        self.assertTrue(
            AuditLog.objects.filter(
                entity=entity, action_type="state_change", to_state=self.state_review
            ).exists()
        )

    def test_transition_by_to_state(self):
        entity = Entity.objects.create(
            workflow=self.workflow,
            current_state=self.state_new,
            schema_version=self.schema_version,
            data_json={"requester": "Sam", "priority": "Low"},
            created_by=self.user,
        )

        url = reverse("entity-transition", kwargs={"pk": entity.id})
        resp = self.client.post(url, {"to_state": self.state_review.id}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        entity.refresh_from_db()
        self.assertEqual(entity.current_state_id, self.state_review.id)

    def test_transition_requires_manager_approval(self):
        entity = Entity.objects.create(
            workflow=self.workflow,
            current_state=self.state_review,
            schema_version=self.schema_version,
            data_json={"requester": "Sam", "priority": "High", "manager_approval": False},
            created_by=self.user,
        )

        url = reverse("entity-transition", kwargs={"pk": entity.id})
        resp = self.client.post(url, {"transition": self.transition_complete.id}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("detail"), "Rule blocked transition")

        entity.data_json["manager_approval"] = True
        entity.save(update_fields=["data_json"])

        resp_ok = self.client.post(url, {"transition": self.transition_complete.id}, format="json")
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)

    def test_transition_mismatch_state(self):
        entity = Entity.objects.create(
            workflow=self.workflow,
            current_state=self.state_new,
            schema_version=self.schema_version,
            data_json={"requester": "Sam", "priority": "Low"},
            created_by=self.user,
        )

        url = reverse("entity-transition", kwargs={"pk": entity.id})
        resp = self.client.post(url, {"transition": self.transition_complete.id}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("detail"), "Transition does not match entity state.")
