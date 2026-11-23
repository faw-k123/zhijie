"""六国实测候选服务测试：身份、门槛、证据、批次、发布版本。"""

from __future__ import annotations

import os
import shutil
import tempfile

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from api import pilot_auth
from propagation import pilot, research_data


def make_row(index: int, *, variant: str = "original", country: str = "日本", music_id: str = "MU001", **overrides):
    row = {
        "response_id": f"R-{variant}-{index:04d}",
        "country": country,
        "music_id": music_id,
        "variant": variant,
        "prior_exposure": "none",
        "completion_rate": "100",
        "emotional_resonance": "4",
        "timbre_identity": "4",
        "melody_accessibility": "4",
        "cultural_understanding": "4",
        "cultural_story": "4",
        "adaptation_space": "3",
        "visual_expressiveness": "3",
        "era_theme_relevance": "4",
        "save_share_intent": "3",
        "learning_intent": "3",
        "open_response": "测试开放回答",
        "cultural_risk_flag": "",
        "consent": "yes",
        "collected_at": "2026-11-08T10:00:00+08:00",
    }
    row.update(overrides)
    return row


class PilotCandidateTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.tmp = tempfile.mkdtemp(prefix="pilot-test-")
        self.old_store = os.environ.get("PILOT_STORE_DIR")
        os.environ["PILOT_STORE_DIR"] = self.tmp
        research_data.clear_cache()

    def tearDown(self):
        if self.old_store is None:
            os.environ.pop("PILOT_STORE_DIR", None)
        else:
            os.environ["PILOT_STORE_DIR"] = self.old_store
        shutil.rmtree(self.tmp, ignore_errors=True)

    def auth(self, role="operator"):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {pilot_auth.issue_token(role, role)}")

    def valid_rows(self, count=20):
        return [make_row(i) for i in range(count)]

    def import_batch(self, rows, operator="operator"):
        self.auth("operator")
        response = self.client.post("/api/research/pilot/import/", {"rows": rows, "batch_label": "test"}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["data"]

    def approve_batch(self, batch_id):
        self.auth("approver")
        response = self.client.post(f"/api/research/pilot/batches/{batch_id}/approve/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)

    def approve_config(self, **overrides):
        self.auth("approver")
        payload = {
            "min_per_variant": 20, "min_per_cell": 40, "variant_balance_tolerance": 0.25,
            "min_country_total": 120, "min_country_cells": 12, "min_completion_rate": 70,
            "max_missing_ratio": 0.2, "cross_country_min_countries": 3, "cross_country_min_cells": 12,
        }
        payload.update(overrides)
        submitted = self.client.post("/api/research/pilot/config/submit/", payload, format="json")
        self.assertEqual(submitted.status_code, 200, submitted.content)
        version = submitted.json()["data"]["config_version"]
        approved = self.client.post("/api/research/pilot/config/approve/", {"config_version": version}, format="json")
        self.assertEqual(approved.status_code, 200, approved.content)
        return version

    def approved_evidence(self, music_id="MU001", score=80.0):
        self.auth("operator")
        created = self.client.post("/api/research/pilot/evidence/", {
            "music_id": music_id, "score_0_100": score,
            "source": "test evidence source", "rule_version": "EV-RULE-1",
        }, format="json")
        self.assertEqual(created.status_code, 200, created.content)
        evidence_id = created.json()["data"]["evidence_id"]
        self.auth("approver")
        approved = self.client.post(f"/api/research/pilot/evidence/{evidence_id}/approve/", {}, format="json")
        self.assertEqual(approved.status_code, 200, approved.content)
        return evidence_id

    def test_auth_required_and_role_forbidden(self):
        row = self.valid_rows(1)
        self.assertEqual(self.client.post("/api/research/pilot/import/", {"rows": row}, format="json").status_code, 401)
        self.auth("operator")
        self.assertEqual(self.client.post("/api/research/pilot/import/", {"rows": row}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/research/pilot/batches/not-found/approve/", {}, format="json").status_code, 403)

    def test_forged_approver_is_ignored(self):
        rows = [make_row(i) for i in range(20)] + [make_row(100 + i, variant="adapted") for i in range(20)]
        self.auth("operator")
        batch = self.client.post("/api/research/pilot/import/", {"rows": rows}, format="json").json()["data"]
        self.auth("approver")
        response = self.client.post(
            f"/api/research/pilot/batches/{batch['batch_id']}/approve/",
            {"approver": "forged"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["approved_by"], "approver")

    def test_missing_required_field(self):
        row = make_row(1)
        row.pop("emotional_resonance")
        self.auth("operator")
        errors = self.client.post("/api/research/pilot/validate/", {"rows": [row]}, format="json").json()["data"]["errors"]
        self.assertTrue(any(item["field"] == "emotional_resonance" and item["code"] == "required" for item in errors))

    def test_duplicate_consent_and_invalid_values(self):
        rows = [make_row(1), make_row(2)]
        rows[1]["response_id"] = rows[0]["response_id"]
        rows[1]["consent"] = "no"
        rows[1]["country"] = "法国"
        rows[1]["variant"] = "wrong"
        rows[1]["emotional_resonance"] = "9"
        self.auth("operator")
        errors = self.client.post("/api/research/pilot/validate/", {"rows": rows}, format="json").json()["data"]["errors"]
        codes = {(item["field"], item["code"]) for item in errors}
        self.assertIn(("response_id", "duplicate"), codes)
        self.assertIn(("consent", "not_consented"), codes)
        self.assertIn(("country", "invalid_choice"), codes)
        self.assertIn(("variant", "invalid_choice"), codes)
        self.assertIn(("emotional_resonance", "out_of_range"), codes)

    def test_cross_batch_duplicate_is_isolated(self):
        first = self.import_batch([make_row(1)])
        second = self.import_batch([make_row(1)])
        self.assertEqual(second["rows_clean"], 0)
        self.assertEqual(second["duplicate_conflicts"], 1)
        conflict_file = pilot._root() / "batches" / second["batch_id"] / "conflicts.csv"
        self.assertTrue(conflict_file.exists())
        self.assertIn(first["batch_id"], conflict_file.read_text(encoding="utf-8-sig"))
        self.auth("approver")
        blocked = self.client.post(f"/api/research/pilot/batches/{second['batch_id']}/approve/", {}, format="json")
        self.assertIn(blocked.status_code, (409, 400))

    def test_balanced_sample_without_evidence_is_null(self):
        rows = [make_row(i) for i in range(20)] + [make_row(100 + i, variant="adapted") for i in range(20)]
        batch = self.import_batch(rows)
        self.approve_batch(batch["batch_id"])
        self.auth("operator")
        unit = next(item for item in self.client.post("/api/research/pilot/aggregate/", {}, format="json").json()["data"]["units"] if item["country"] == "日本" and item["music_id"] == "MU001")
        self.assertEqual(unit["status"], "awaiting_evidence")
        self.assertIsNone(unit["formal_score"])
        self.assertIsNone(unit["evidence_score"])

    def test_evidence_conversion_and_publish_flow(self):
        rows = [make_row(i) for i in range(20)] + [make_row(100 + i, variant="adapted") for i in range(20)]
        batch = self.import_batch(rows)
        self.approve_batch(batch["batch_id"])
        evidence_id = self.approved_evidence(score=80.0)
        self.auth("operator")
        unit = next(item for item in self.client.post("/api/research/pilot/aggregate/", {}, format="json").json()["data"]["units"] if item["country"] == "日本" and item["music_id"] == "MU001")
        self.assertEqual(unit["status"], "eligible_for_review")
        self.assertIsNotNone(unit["formal_score"])
        # 1—5 均值转 0—100：(75+75+75+75+50+50+75+80)/8 = 69.375
        self.assertAlmostEqual(unit["formal_score"], 69.38, places=2)
        self.assertGreaterEqual(unit["formal_score"], 0)
        self.assertLessEqual(unit["formal_score"], 100)
        self.assertEqual(unit["evidence_record_id"], evidence_id)
        self.approve_config()
        self.auth("operator")
        draft = self.client.post("/api/research/pilot/scores/", {"title": "draft"}, format="json")
        self.assertEqual(draft.status_code, 200, draft.content)
        score = draft.json()["data"]
        self.assertEqual(score["status"], "pending_approval")
        self.auth("approver")
        approved = self.client.post(f"/api/research/pilot/scores/{score['score_id']}/approve/", {}, format="json")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["data"]["status"], "approved_candidate")
        self.assertEqual(self.client.get("/api/research/pilot/rankings/").json()["data"]["items"], [])
        published = self.client.post(f"/api/research/pilot/scores/{score['score_id']}/publish/", {}, format="json")
        self.assertEqual(published.status_code, 200, published.content)
        ranking = self.client.get("/api/research/pilot/rankings/").json()["data"]["items"]
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["music_id"], "MU001")
        self.assertEqual(ranking[0]["version"], published.json()["data"]["version"])

    def test_new_version_supersedes_old_and_revoke_closes_ranking(self):
        rows = [make_row(i) for i in range(20)] + [make_row(100 + i, variant="adapted") for i in range(20)]
        batch = self.import_batch(rows)
        self.approve_batch(batch["batch_id"])
        self.approved_evidence(score=80)
        self.approve_config()
        self.auth("operator")
        score = self.client.post("/api/research/pilot/scores/", {"title": "draft"}, format="json").json()["data"]
        self.auth("approver")
        self.client.post(f"/api/research/pilot/scores/{score['score_id']}/approve/", {}, format="json")
        first = self.client.post(f"/api/research/pilot/scores/{score['score_id']}/publish/", {}, format="json").json()["data"]
        self.auth("operator")
        score2 = self.client.post("/api/research/pilot/scores/", {"title": "draft2"}, format="json").json()["data"]
        self.auth("approver")
        self.client.post(f"/api/research/pilot/scores/{score2['score_id']}/approve/", {}, format="json")
        second = self.client.post(f"/api/research/pilot/scores/{score2['score_id']}/publish/", {}, format="json").json()["data"]
        old = json_load(pilot._root() / "published" / f"{first['version']}.json")
        self.assertEqual(old["status"], "superseded")
        ranking = self.client.get("/api/research/pilot/rankings/").json()["data"]["items"]
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["version"], second["version"])
        revoked = self.client.post(f"/api/research/pilot/published/{second['version']}/revoke/", {"reason": "test"}, format="json")
        self.assertEqual(revoked.status_code, 200, revoked.content)
        self.assertEqual(self.client.get("/api/research/pilot/rankings/").json()["data"]["items"], [])

    def test_evidence_range_and_pending_not_used(self):
        self.auth("operator")
        invalid = self.client.post("/api/research/pilot/evidence/", {
            "music_id": "MU001", "score_0_100": 101,
            "source": "source", "rule_version": "rule",
        }, format="json")
        self.assertEqual(invalid.status_code, 400)
        created = self.client.post("/api/research/pilot/evidence/", {
            "music_id": "MU001", "score_0_100": 80,
            "source": "source", "rule_version": "rule",
        }, format="json")
        self.assertEqual(created.status_code, 200)
        rows = [make_row(i) for i in range(20)] + [make_row(100 + i, variant="adapted") for i in range(20)]
        batch = self.import_batch(rows)
        self.approve_batch(batch["batch_id"])
        self.auth("operator")
        unit = next(item for item in self.client.post("/api/research/pilot/aggregate/", {}, format="json").json()["data"]["units"] if item["country"] == "日本" and item["music_id"] == "MU001")
        self.assertEqual(unit["status"], "awaiting_evidence")
        self.assertIsNone(unit["formal_score"])

    def test_operator_cannot_approve_publish_or_revoke(self):
        self.auth("operator")
        self.assertEqual(self.client.post("/api/research/pilot/scores/PS-X/approve/", {}, format="json").status_code, 403)
        self.assertEqual(self.client.post("/api/research/pilot/scores/PS-X/publish/", {}, format="json").status_code, 403)
        self.assertEqual(self.client.post("/api/research/pilot/published/PV-X/revoke/", {"reason": "x"}, format="json").status_code, 403)

    def test_rehearsal_and_protocol_mixing_are_excluded(self):
        rows = [make_row(i) for i in range(20)] + [make_row(100 + i, variant="adapted") for i in range(20)]
        for row in rows:
            row["dataset_kind"] = "pilot_rehearsal"
            row["protocol_version"] = "OTHER-PROTOCOL"
        batch = self.import_batch(rows)
        self.approve_batch(batch["batch_id"])
        self.auth("operator")
        data = self.client.post("/api/research/pilot/aggregate/", {}, format="json").json()["data"]
        self.assertEqual(data["rehearsal_rows_excluded"], 40)
        self.assertEqual(data["eligible_rows"], 0)
        unit = next(item for item in data["units"] if item["country"] == "日本" and item["music_id"] == "MU001")
        self.assertEqual(unit["status"], "not_started")

    def test_config_fields_are_enforced(self):
        rows = [make_row(i) for i in range(20)] + [make_row(100 + i, variant="adapted") for i in range(20)]
        batch = self.import_batch(rows)
        self.approve_batch(batch["batch_id"])
        self.approved_evidence(score=80)
        self.approve_config(min_per_cell=41)
        self.auth("operator")
        unit = next(item for item in self.client.post("/api/research/pilot/aggregate/", {}, format="json").json()["data"]["units"] if item["country"] == "日本" and item["music_id"] == "MU001")
        self.assertEqual(unit["status"], "insufficient_sample")

    def test_config_immutable_and_invalid(self):
        self.approve_config()
        self.auth("approver")
        bad = self.client.post("/api/research/pilot/config/submit/", {"min_per_variant": 0}, format="json")
        self.assertEqual(bad.status_code, 400)
        # 已审批版本不可重复审批；新版本必须是新 ID。
        active = pilot.config()
        again = self.client.post("/api/research/pilot/config/approve/", {"config_version": active["config_version"]}, format="json")
        self.assertEqual(again.status_code, 400)


def json_load(path):
    import json
    return json.loads(path.read_text(encoding="utf-8"))
