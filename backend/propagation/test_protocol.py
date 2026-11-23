"""六国首轮协议与随机分配测试。"""

from __future__ import annotations

import os
import shutil
import tempfile

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from api import pilot_auth
from propagation import protocol, research_data


class ProtocolTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.tmp = tempfile.mkdtemp(prefix="protocol-test-")
        self.old = os.environ.get("PILOT_STORE_DIR")
        os.environ["PILOT_STORE_DIR"] = self.tmp
        research_data.clear_cache()

    def tearDown(self):
        if self.old is None:
            os.environ.pop("PILOT_STORE_DIR", None)
        else:
            os.environ["PILOT_STORE_DIR"] = self.old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def auth(self, role):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {pilot_auth.issue_token(role, role)}")

    def draft_and_freeze(self, version="IRP-TEST-V1"):
        self.auth("operator")
        draft = self.client.post("/api/research/pilot/protocol/draft/", {"protocol_version": version}, format="json")
        self.assertEqual(draft.status_code, 200, draft.content)
        self.assertEqual(draft.json()["data"]["status"], "pending_approval")
        self.auth("approver")
        frozen = self.client.post(f"/api/research/pilot/protocol/{version}/approve/", {}, format="json")
        self.assertEqual(frozen.status_code, 200, frozen.content)
        self.assertEqual(frozen.json()["data"]["status"], "frozen")
        self.assertEqual(protocol.current_protocol()["protocol_version"], version)
        self.assertEqual(protocol.current_protocol()["status"], "frozen")
        return frozen.json()["data"]

    def prepare_localization(self, doc, country="日本"):
        self.auth("operator")
        generated = self.client.post("/api/research/pilot/localizations/generate/", {
            "protocol_version": doc["protocol_version"],
        }, format="json")
        self.assertEqual(generated.status_code, 200, generated.content)
        item = next(row for row in generated.json()["data"]["items"] if row["country"] == country)
        translations = item["source_zh"]
        submitted = self.client.post(
            f"/api/research/pilot/localizations/{doc['protocol_version']}/{country}/submit/",
            {"translations": translations}, format="json",
        )
        self.assertEqual(submitted.status_code, 200, submitted.content)
        self.auth("approver")
        approved = self.client.post(
            f"/api/research/pilot/localizations/{doc['protocol_version']}/{country}/approve/",
            {}, format="json",
        )
        self.assertEqual(approved.status_code, 200, approved.content)
        self.assertEqual(approved.json()["data"]["status"], "approved")
        return approved.json()["data"]

    def test_protocol_contains_tools_and_localization_pending(self):
        doc = self.draft_and_freeze()
        self.assertEqual(len(doc["music"]), 20)
        self.assertEqual(len(doc["measurement"]["items"]), 8)
        self.assertEqual(len(doc["localization"]), 6)
        self.assertTrue(all(item["translation_status"] == "pending_native_review" for item in doc["localization"]))
        self.assertTrue(doc["sha256"])
        self.assertEqual(doc["approved_by"], "approver")

    def test_protocol_requires_auth(self):
        self.assertEqual(self.client.post("/api/research/pilot/protocol/draft/", {}, format="json").status_code, 401)
        self.assertEqual(self.client.post("/api/research/pilot/localizations/generate/", {}, format="json").status_code, 401)
        self.assertEqual(self.client.post("/api/research/pilot/assignments/", {}, format="json").status_code, 401)
        self.auth("operator")
        self.assertEqual(self.client.post("/api/research/pilot/protocol/IRP-TEST-V1/approve/", {}, format="json").status_code, 403)

    def test_assignment_reproducible_and_consent_required(self):
        doc = self.draft_and_freeze()
        self.prepare_localization(doc)
        self.auth("operator")
        bad = self.client.post("/api/research/pilot/assignments/", {
            "protocol_version": doc["protocol_version"], "participant_ref": "person-1", "country": "日本", "consent": False,
        }, format="json")
        self.assertEqual(bad.status_code, 400)
        first = self.client.post("/api/research/pilot/assignments/", {
            "protocol_version": doc["protocol_version"], "participant_ref": "person-1", "country": "日本", "consent": True,
        }, format="json")
        self.assertEqual(first.status_code, 200, first.content)
        second = self.client.post("/api/research/pilot/assignments/", {
            "protocol_version": doc["protocol_version"], "participant_ref": "person-1", "country": "日本", "consent": True,
        }, format="json")
        self.assertEqual(second.status_code, 400)
        # 撤回后同一种子仍应产生相同分配（可复现），但需要新分配编号。
        aid = first.json()["data"]["assignment_id"]
        self.client.post(f"/api/research/pilot/assignments/{aid}/withdraw/", {}, format="json")
        third = self.client.post("/api/research/pilot/assignments/", {
            "protocol_version": doc["protocol_version"], "participant_ref": "person-1", "country": "日本", "consent": True,
        }, format="json")
        self.assertEqual(third.status_code, 200, third.content)
        a, b = first.json()["data"], third.json()["data"]
        self.assertEqual(a["assignment_hash"], b["assignment_hash"])
        self.assertEqual(a["music_id"], b["music_id"])
        self.assertEqual(a["variant"], b["variant"])

    def test_formal_assignment_requires_approved_localization(self):
        doc = self.draft_and_freeze()
        self.auth("operator")
        response = self.client.post("/api/research/pilot/assignments/", {
            "protocol_version": doc["protocol_version"], "participant_ref": "person-1",
            "country": "日本", "consent": True,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("母语审校", response.json()["message"])

    def test_quota_balancing_and_assignment_lifecycle(self):
        doc = self.draft_and_freeze()
        self.prepare_localization(doc)
        self.auth("operator")
        assignments = []
        for index in range(40):
            response = self.client.post("/api/research/pilot/assignments/", {
                "protocol_version": doc["protocol_version"],
                "participant_ref": f"quota-{index}", "country": "日本", "consent": True,
            }, format="json")
            self.assertEqual(response.status_code, 200, response.content)
            assignments.append(response.json()["data"])
        combos = {(row["music_id"], row["variant"]) for row in assignments}
        self.assertEqual(len(combos), 40)
        first = assignments[0]
        for event, extra in (("started", {}), ("played", {}), ("completed", {"completion_rate": 95}), ("submitted", {})):
            response = self.client.post(
                f"/api/research/pilot/assignments/{first['assignment_id']}/event/",
                {"event": event, **extra}, format="json",
            )
            self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["data"]["status"], "submitted")
        counts = self.client.get("/api/research/pilot/assignments/").json()["data"]
        self.assertEqual(counts["by_status"]["submitted"], 1)
        self.assertEqual(counts["imbalanced_cells"], 0)

    def test_localization_requires_separate_native_reviewer(self):
        doc = self.draft_and_freeze()
        self.auth("operator")
        generated = self.client.post("/api/research/pilot/localizations/generate/", {
            "protocol_version": doc["protocol_version"],
        }, format="json").json()["data"]
        item = next(row for row in generated["items"] if row["country"] == "日本")
        self.client.post(
            f"/api/research/pilot/localizations/{doc['protocol_version']}/日本/submit/",
            {"translations": item["source_zh"]}, format="json",
        )
        # operator 无审批权限；服务端不能接受客户端自报审校人。
        denied = self.client.post(
            f"/api/research/pilot/localizations/{doc['protocol_version']}/日本/approve/",
            {}, format="json",
        )
        self.assertEqual(denied.status_code, 403)

    def test_new_protocol_version_does_not_mutate_old(self):
        old = self.draft_and_freeze("IRP-TEST-V1")
        new = self.draft_and_freeze("IRP-TEST-V2")
        self.assertEqual(old["protocol_version"], "IRP-TEST-V1")
        self.assertEqual(new["protocol_version"], "IRP-TEST-V2")
        self.assertEqual(old["status"], "frozen")
        self.assertEqual(new["status"], "frozen")
