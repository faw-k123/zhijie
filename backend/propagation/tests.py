"""P2 研究数据服务层与 7 个只读 API 的测试。

使用 SimpleTestCase：不访问 SQL Server；所有数据来自版本化 JSON。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from propagation import research_analytics, research_data
from propagation.research_analytics import indicator_gate, sample_status


REAL_DATA_ROOT = Path(settings.BASE_DIR).parent / "research" / "data"
RESEARCH_PATHS = (
    "/api/research/status/",
    "/api/research/cases/",
    "/api/research/cases/CASE001/",
    "/api/research/statistics/",
    "/api/research/success-factors/",
    "/api/research/music-potential/",
    "/api/research/regional-matrix/",
)


class ResearchApiTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        research_data.clear_cache()

    def _status_sample(self):
        response = self.client.get("/api/research/status/")
        self.assertEqual(response.status_code, 200)
        return response.json()["data"]

    def test_status_returns_sample_and_version(self):
        data = self._status_sample()
        n = data["sample"]["n"]
        expected_status = "descriptive" if n >= 20 else ("exploratory" if n >= 5 else "insufficient")
        self.assertEqual(data["sample"]["target"], 80)
        self.assertEqual(data["sample"]["status"], expected_status)
        self.assertAlmostEqual(
            data["sample"]["progress_percent"],
            round(data["sample"]["n"] / 80 * 100, 1),
        )
        self.assertIn(data["version"]["active_version"], ("v1.0", "v1.1", "v1.2", "v1.5", "v1.6", "v1.7", "v1.8"))
        self.assertEqual(data["version"]["status"], "reviewed")
        self.assertGreaterEqual(data["counts"]["sources"], 7)
        self.assertEqual(data["counts"]["cases"], 80)
        self.assertEqual(data["counts"]["approved"], 80)
        self.assertEqual(data["counts"]["strict_reviewed"], 10)
        self.assertEqual(data["counts"]["extended_reference"], 70)
        self.assertEqual(data["counts"]["pending_review"], 0)
        self.assertEqual(
            data["counts"]["cases"],
            data["counts"]["strict_reviewed"]
            + data["counts"]["extended_reference"]
            + data["counts"]["pending_review"],
        )
        cases = self.client.get("/api/research/cases/", {"page_size": 50}).json()["data"]["items"]
        self.assertEqual(len(cases), 50)
        self.assertTrue(all(case["owner_approval_status"] == "approved" for case in cases))

        factors = self.client.get(
            "/api/research/success-factors/", {"analysis_sample": "all"}
        ).json()["data"]
        self.assertEqual(factors["analysis_scope"]["case_count"], 80)
        self.assertEqual(factors["analysis_scope"]["scored_case_count"], 80)

    def test_every_endpoint_returns_sample(self):
        status = self._status_sample()
        for path in RESEARCH_PATHS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertTrue(payload["success"])
                self.assertIn("sample", payload["data"])
                self.assertEqual(payload["data"]["sample"]["n"], status["sample"]["n"])
                self.assertEqual(payload["data"]["sample"]["target"], 80)
                self.assertEqual(payload["data"]["sample"]["status"], status["sample"]["status"])

    def test_cases_filter_and_pagination(self):
        response = self.client.get("/api/research/cases/", {"q": "二胡", "page_size": 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertGreaterEqual(data["total"], 2)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["case_id"], "CASE001")
        self.assertEqual(data["pagination"]["page_size"], 1)
        self.assertTrue(data["pagination"]["has_next"])
        self.assertEqual(data["items"][0]["mean_score"], 2.7)

    def test_all_approved_cases_are_available_to_case_library(self):
        response = self.client.get(
            "/api/research/cases/", {"analysis_sample": "all", "page_size": 50}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["total"], 80)
        self.assertEqual(data["analysis_scope"]["case_count"], 80)
        self.assertTrue(all(item["owner_approval_status"] == "approved" for item in data["items"]))

    def test_cases_filter_by_country(self):
        response = self.client.get("/api/research/cases/", {"country": "日本"})
        data = response.json()["data"]
        self.assertGreaterEqual(data["total"], 1)
        self.assertIn("CASE003", [item["case_id"] for item in data["items"]])

    def test_invalid_pagination_returns_400(self):
        for params in ({"page": "0"}, {"page": "abc"}, {"page_size": "51"}):
            with self.subTest(params=params):
                response = self.client.get("/api/research/cases/", params)
                self.assertEqual(response.status_code, 400)

    def test_case_detail_contains_coding_and_similar_cases(self):
        response = self.client.get("/api/research/cases/CASE001/")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["case"]["case_id"], "CASE001")
        self.assertEqual(len(data["coding"]["indicators"]), 10)
        self.assertEqual(data["coding"]["mean_score"], 2.7)
        self.assertEqual(data["coding"]["valid_count"], 10)
        self.assertEqual(data["coding"]["missing_count"], 0)
        self.assertGreaterEqual(len(data["similar_cases"]), 2)
        self.assertNotIn("CASE001", [item["case_id"] for item in data["similar_cases"]])

    def test_case_detail_404(self):
        response = self.client.get("/api/research/cases/CASE999/")
        self.assertEqual(response.status_code, 404)

    def test_statistics_distributions_and_sample_gate(self):
        status = self._status_sample()
        response = self.client.get("/api/research/statistics/")
        data = response.json()["data"]
        n = status["sample"]["n"]
        expected_status = "descriptive" if n >= 20 else ("exploratory" if n >= 5 else "insufficient")
        self.assertEqual(data["sample"]["status"], expected_status)
        self.assertEqual(data["rankings_allowed"], status["sample"]["n"] >= 20)
        self.assertEqual(data["success_factors_available"], status["sample"]["n"] >= 5)
        self.assertGreaterEqual(len(data["distributions"]["country"]), 3)
        self.assertEqual(len(data["indicator_coverage"]), 10)
        self.assertGreaterEqual(len(data["country_factor_correspondence"]), 13)
        self.assertTrue(all(len(row["top_factors"]) <= 3 for row in data["country_factor_correspondence"]))

    def test_success_factors_gate_matches_sample_size(self):
        status = self._status_sample()
        response = self.client.get("/api/research/success-factors/")
        data = response.json()["data"]
        self.assertEqual(len(data["factors"]), 10)
        if status["sample"]["n"] < 5:
            self.assertEqual(data["availability"], "unavailable")
            self.assertIsNone(data["rankings"])
            self.assertTrue(all(item["status"] == "insufficient" for item in data["factors"]))
        elif status["sample"]["n"] < 20:
            self.assertEqual(data["availability"], "exploratory")
            self.assertEqual(data["rankings"], [])
            emotional = next(item for item in data["factors"] if item["indicator_id"] == "emotional_resonance")
            self.assertLess(emotional["n"], 5)
            self.assertEqual(emotional["status"], "insufficient")
            self.assertFalse(emotional["ranking_allowed"])
        else:
            self.assertEqual(data["availability"], "descriptive")
            self.assertIsNotNone(data["rankings"])

    def test_success_factors_can_rank_top_three_by_country(self):
        response = self.client.get(
            "/api/research/success-factors/",
            {"analysis_sample": "all", "country": "美国"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["analysis_scope"]["country"], "美国")
        self.assertEqual(data["analysis_scope"]["case_count"], 17)
        scored = sorted(
            [factor for factor in data["factors"] if factor["mean_score"] is not None],
            key=lambda factor: (-factor["mean_score"], factor["order"] or 999),
        )
        self.assertEqual(len(scored[:3]), 3)

    def test_indicator_gate_thresholds(self):
        self.assertEqual(indicator_gate(0)["status"], "empty")
        self.assertEqual(indicator_gate(4)["status"], "insufficient")
        self.assertFalse(indicator_gate(4)["ranking_allowed"])
        self.assertEqual(indicator_gate(5)["status"], "exploratory")
        self.assertFalse(indicator_gate(5)["ranking_allowed"])
        self.assertEqual(indicator_gate(19)["status"], "exploratory")
        self.assertEqual(indicator_gate(20)["status"], "descriptive")
        self.assertTrue(indicator_gate(20)["ranking_allowed"])

    def test_analysis_sample_invalid_returns_400(self):
        for path in (
            "/api/research/cases/",
            "/api/research/statistics/",
            "/api/research/success-factors/",
        ):
            with self.subTest(path=path):
                response = self.client.get(path, {"analysis_sample": "not_a_sample"})
                self.assertEqual(response.status_code, 400)

    def test_mining_returns_case_dataset_and_gated_correlations(self):
        response = self.client.get("/api/research/mining/")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data["cases"]), data["case_count"])
        self.assertEqual(len(data["indicators"]), 10)
        self.assertEqual(len(data["correlations"]), 45)
        self.assertTrue(all(item["status"] in {"exploratory", "insufficient"} for item in data["correlations"]))
        self.assertIn(f"n={data['case_count']}", data["scope_note"])
        self.assertIn("library", data)
        self.assertIn("analysis_db", data)

    def test_v15_case_detail_returns_approval_fields(self):
        root = REAL_DATA_ROOT / "v1.5"
        manifest = json.loads((REAL_DATA_ROOT / "manifest.json").read_text(encoding="utf-8-sig"))
        meta = next(v for v in manifest["versions"] if v["version"] == "v1.5")
        bundle = research_data.ResearchBundle(
            manifest=manifest,
            version="v1.5",
            version_meta=meta,
            cases_doc=json.loads((root / "cases.json").read_text(encoding="utf-8")),
            success_doc=json.loads((root / "success_factors.json").read_text(encoding="utf-8")),
            music_doc=json.loads((root / "music_scores.json").read_text(encoding="utf-8")),
            regional_doc=json.loads((root / "regional_strategies.json").read_text(encoding="utf-8")),
        )
        detail = research_analytics.get_case_detail(bundle, "CASE037")
        coding = {x["indicator_id"]: x for x in detail["coding"]["indicators"]}
        self.assertEqual(coding["story_explainability"]["score"], 1)
        self.assertEqual(coding["story_explainability"]["approval_status"], "approved")
        self.assertEqual(coding["story_explainability"]["score_status"], "approved")
        self.assertEqual(coding["story_explainability"]["approver"], "yxh")
        self.assertIsNone(coding["channel_fit"]["score"])
        self.assertEqual(coding["channel_fit"]["approval_status"], "approved_revoked")
        self.assertEqual(coding["channel_fit"]["score_status"], "revoked_approved")

    def test_v17_strict_case_detail_contains_approval_fields(self):
        response = self.client.get("/api/research/cases/CASE001/")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        indicators = data["coding"]["indicators"]
        first = indicators[0]
        self.assertEqual(first["approval_status"], "approved")
        self.assertEqual(first["score_status"], "approved")
        self.assertEqual(first["approver"], "项目负责人（用户确认）")
        self.assertEqual(first["approval_date"], "2026-11-08")
        self.assertEqual(len(data["audience_feedback"]), 2)
        self.assertEqual(data["audience_feedback"][0]["feedback_id"], "FB005")
        self.assertEqual(len(data["acceptance_mechanisms"]), 9)
        self.assertEqual(data["acceptance_mechanisms"][0]["label"], "情绪共鸣")
        self.assertEqual(data["outcome_label"], "学习或行动转化")

    def test_music_candidates_are_selected_but_scores_remain_pending(self):
        response = self.client.get("/api/research/music-potential/")
        data = response.json()["data"]
        self.assertEqual(data["availability"], "partial")
        self.assertEqual(data["status"], "partial")
        self.assertEqual(data["music_sample"]["n"], 0)
        self.assertEqual(data["music_sample"]["target"], 20)
        self.assertEqual(len(data["items"]), 20)
        self.assertTrue(all(item["total_score"] is None for item in data["items"]))
        self.assertIsNone(data["rankings"])

    def test_regional_matrix_contains_six_approved_pilot_strategies(self):
        response = self.client.get("/api/research/regional-matrix/")
        data = response.json()["data"]
        self.assertEqual(data["availability"], "partial")
        self.assertEqual(len(data["rows"]), 6)
        self.assertEqual(len(data["matrix"]), 6)
        self.assertEqual(len(data["regions"]), 6)
        self.assertEqual(len(data["themes"]), 10)
        self.assertTrue(data["independent_of_case_sample"])

    def test_teacher_revision_outcomes_are_complete_without_fake_scores(self):
        response = self.client.get("/api/research/teacher-revision/")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["status"], "approved")
        self.assertEqual(data["counts"]["strict_cases"], 10)
        self.assertEqual(data["counts"]["feedback"], 20)
        self.assertEqual(data["counts"]["coding_eligible_feedback"], 18)
        self.assertEqual(data["counts"]["mechanisms"], 9)
        self.assertEqual(data["counts"]["music_candidates"], 20)
        self.assertEqual(data["counts"]["countries"], 6)
        self.assertEqual(data["counts"]["matrix_cells"], 120)
        self.assertTrue(all(len(case["feedback"]) == 2 for case in data["cases"]))
        self.assertTrue(all(len(case["mechanisms"]) == 9 for case in data["cases"]))
        self.assertTrue(all(item["total_score"] is None for item in data["music"]["items"]))
        self.assertTrue(all(item["score_status"] == "awaiting_six_country_pilot" for item in data["music"]["items"]))
        self.assertTrue(all(len(row["countries"]) == 6 for row in data["matrix"]))
        self.assertTrue(all(
            set(row["countries"].values()).issubset({"A", "B", "C"})
            for row in data["matrix"]
        ))
        self.assertTrue(all(
            item["strong"] + item["partial"] + item["not_evidenced"] == 10
            for item in data["mechanisms"]
        ))
        self.assertEqual(len(data["admission_rules"]), 6)
        self.assertTrue(all(
            len(case["admission_audit"]) == 6
            and all(item["passed"] for item in case["admission_audit"])
            for case in data["cases"]
        ))
        self.assertEqual(data["pilot"]["status"], "not_started")
        self.assertEqual(data["pilot"]["planned_cells"], 120)
        self.assertEqual(data["pilot"]["completed_cells"], 0)
        self.assertGreaterEqual(len(data["pilot"]["response_fields"]), 12)

    def test_pilot_validation_accepts_balanced_rows_without_formal_scoring(self):
        base = {
            "country": "日本",
            "music_id": "MU001",
            "prior_exposure": "limited",
            "completion_rate": 100,
            "emotional_resonance": 4,
            "timbre_identity": 5,
            "melody_accessibility": 4,
            "cultural_understanding": 3,
            "cultural_story": 4,
            "adaptation_space": 3,
            "visual_expressiveness": 3,
            "era_theme_relevance": 4,
            "save_share_intent": 4,
            "learning_intent": 4,
            "open_response": "音色鲜明，愿意了解乐器背景",
            "cultural_risk_flag": "",
            "consent": "yes",
            "collected_at": "2026-11-08T12:00:00+08:00",
        }
        rows = [
            {**base, "response_id": "JP-MU001-001", "variant": "original"},
            {**base, "response_id": "JP-MU001-002", "variant": "adapted"},
        ]
        response = self.client.post("/api/research/pilot/validate/", {"rows": rows}, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["status"], "valid")
        self.assertEqual(data["summary"]["total_rows"], 2)
        self.assertEqual(data["summary"]["eligible_rows"], 2)
        self.assertEqual(data["summary"]["error_count"], 0)
        self.assertEqual(data["summary"]["observed_cells"], 1)
        self.assertEqual(data["summary"]["balanced_cells"], 1)
        self.assertFalse(data["formal_scoring_allowed"])

    def test_pilot_validation_rejects_duplicates_and_invalid_values(self):
        rows = [{
            "response_id": "DUP001",
            "country": "法国",
            "music_id": "MU999",
            "variant": "wrong",
            "prior_exposure": "unknown",
            "completion_rate": 101,
            "emotional_resonance": 6,
            "timbre_identity": 3,
            "melody_accessibility": 3,
            "cultural_understanding": 3,
            "cultural_story": 3,
            "adaptation_space": 3,
            "visual_expressiveness": 3,
            "era_theme_relevance": 3,
            "save_share_intent": 3,
            "learning_intent": 3,
            "open_response": "test",
            "consent": "no",
            "collected_at": "not-a-date",
        }] * 2
        response = self.client.post("/api/research/pilot/validate/", {"rows": rows}, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["status"], "invalid")
        self.assertEqual(data["summary"]["eligible_rows"], 0)
        self.assertEqual(data["summary"]["duplicate_response_ids"], 1)
        self.assertGreater(data["summary"]["error_count"], 10)

    def test_music_context_links_selected_track_without_inventing_scores(self):
        response = self.client.get(
            "/api/research/music-context/",
            {"title": "春江花月夜", "category": "乐器", "subcategory": "古筝"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["association"]["status"], "linked")
        self.assertEqual(data["association"]["matched_by"], "exact_title")
        self.assertEqual(data["potential"]["status"], "incomplete")
        self.assertIsNone(data["potential"]["total_score"])
        self.assertEqual(data["related_cases"], [])
        self.assertEqual(len(data["regional_rows"]), 6)
        self.assertEqual(data["potential"]["selection_tier"], "A")
        self.assertTrue(data["potential"]["selection_reason"])
        self.assertEqual(len(data["global_reference"]["cases"]), 3)
        self.assertEqual(len(data["global_reference"]["factor_shares"]), 10)
        self.assertEqual(len(data["global_reference"]["regional_rows"]), 6)
        self.assertGreaterEqual(len(data["matched_cases"]), 1)
        self.assertEqual(data["factor_reference"]["scope"], "matched")
        self.assertGreaterEqual(len(data["factor_reference"]["factor_shares"]), 1)
        self.assertEqual(
            data["factor_reference"]["case_ids"],
            [item["case_id"] for item in data["matched_cases"]],
        )

    def test_music_context_uses_category_reference_for_non_candidate_song(self):
        response = self.client.get(
            "/api/research/music-context/",
            {"title": "东北人都是活雷锋", "category": "民歌", "subcategory": "东北民歌"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["association"]["status"], "category_reference")
        self.assertEqual(data["association"]["label"], "同类候选参考")
        self.assertIsNone(data["potential"])
        self.assertGreaterEqual(len(data["category_reference"]["items"]), 1)
        self.assertEqual(data["matched_cases"], [])
        self.assertEqual(data["factor_reference"]["scope"], "unavailable")
        self.assertEqual(data["factor_reference"]["factor_shares"], [])
        self.assertEqual(len(data["weights"]), 8)
        self.assertEqual(data["music_status"], "partial")

    def test_song_context_never_uses_global_factor_fallback(self):
        songs = (
            {"title": "东北人都是活雷锋", "category": "民歌", "subcategory": "东北民歌"},
            {"title": "三寸天堂", "category": "乐器", "subcategory": "二胡"},
            {"title": "无直接案例测试曲", "category": "未知类别", "subcategory": "未知小类"},
        )
        references = []
        for params in songs:
            response = self.client.get("/api/research/music-context/", params)
            self.assertEqual(response.status_code, 200)
            reference = response.json()["data"]["factor_reference"]
            self.assertNotEqual(reference["scope"], "library")
            references.append(reference)
        self.assertEqual(references[0]["scope"], "unavailable")
        self.assertEqual(references[0]["factor_shares"], [])
        self.assertEqual(references[1]["scope"], "matched")
        self.assertGreaterEqual(len(references[1]["factor_shares"]), 1)
        self.assertEqual(references[2]["scope"], "unavailable")

    def test_music_context_requires_title(self):
        response = self.client.get("/api/research/music-context/")
        self.assertEqual(response.status_code, 400)

    def test_existing_propagation_endpoint_unchanged(self):
        response = self.client.post(
            "/api/global/propagation/",
            {"category": "民歌", "subcategory": "江南民歌", "song_title": "茉莉花"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["source"], "propagation_analyze_placeholder")

    def test_sample_thresholds(self):
        self.assertEqual(sample_status(0), "empty")
        self.assertEqual(sample_status(1), "insufficient")
        self.assertEqual(sample_status(4), "insufficient")
        self.assertEqual(sample_status(5), "exploratory")
        self.assertEqual(sample_status(19), "exploratory")
        self.assertEqual(sample_status(20), "descriptive")
        self.assertEqual(sample_status(40), "descriptive")


    def _plan_payload(self):
        return {
            "title": "春江花月夜",
            "target_country": "德国",
            "target_city": "柏林",
            "target_audience": "音乐学院学生",
            "age_range": "25-34",
            "purpose": "文化交流",
            "platform": "音乐学院 / 艺术节",
            "content_format": "音乐会 + 工作坊",
            "adaptation_allowed": "yes",
            "budget_range": "中等",
            "duration": "3个月",
            "language": "德语",
            "origin_city": "上海",
        }

    def test_promo_plan_returns_nine_modules_with_separated_types(self):
        response = self.client.post("/api/research/promo-plan/", self._plan_payload(), format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["meta"]["module_count"], 9)
        self.assertEqual(len(data["modules"]), 9)
        self.assertEqual(data["meta"]["generation_mode"], "rule_template")
        self.assertFalse(data["meta"]["ai_generated"])
        self.assertGreaterEqual(data["evidence_summary"]["case_count"], 1)
        self.assertGreaterEqual(data["evidence_summary"]["source_count"], 1)
        self.assertEqual(data["evidence_summary"]["regional_count"], 0)
        self.assertEqual(data["evidence_summary"]["country_case_count"], 5)
        self.assertEqual(data["evidence_summary"]["country_factor_count"], 3)
        self.assertIn("匹配案例", data["evidence_summary"]["case_scope_label"])
        self.assertGreater(data["counts"]["evidence"], 0)
        self.assertGreater(data["counts"]["suggestions"], 0)
        self.assertGreater(data["counts"]["hypotheses"], 0)
        for module in data["modules"]:
            self.assertIn("evidence", module)
            self.assertGreater(len(module["evidence"]), 0)
            self.assertIn("suggestions", module)
            self.assertIn("hypotheses", module)
            self.assertIn("gaps", module)
        module01 = next(module for module in data["modules"] if module["id"] == "01_music_positioning")
        self.assertTrue(any("上海" in item["text"] for item in module01["suggestions"]))
        self.assertIn("不调用大模型", data["disclaimer"])
        self.assertNotIn("提升30%", response.content.decode("utf-8"))

    def test_different_songs_do_not_share_one_fixed_factor_case_set(self):
        case_sets = []
        for title, category, subcategory in (
            ("花木兰", "戏曲", "豫剧"),
            ("春江花月夜", "乐器", "古筝"),
            ("梅花三弄", "乐器", "古琴"),
        ):
            response = self.client.get(
                "/api/research/music-context/",
                {"title": title, "category": category, "subcategory": subcategory},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(data["factor_reference"]["scope"], "matched")
            self.assertGreaterEqual(len(data["factor_reference"]["factor_shares"]), 1)
            self.assertTrue(all(item["match_reasons"] for item in data["matched_cases"]))
            case_sets.append(tuple(data["factor_reference"]["case_ids"]))
        self.assertEqual(len(set(case_sets)), len(case_sets))

    def test_promo_plan_rejects_missing_inputs(self):
        response = self.client.post("/api/research/promo-plan/", {"title": "春江花月夜"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("missing", response.json())


class ResearchDataFailureTests(SimpleTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="research_p2_"))
        shutil.copytree(
            REAL_DATA_ROOT,
            self.tmp,
            dirs_exist_ok=True,
            copy_function=shutil.copyfile,
        )
        self.override = override_settings(RESEARCH_DATA_DIR=str(self.tmp))
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(shutil.rmtree, self.tmp, True)
        research_data.clear_cache()
        self.client = APIClient()

    def _read(self, name):
        return json.loads((self.tmp / name).read_text(encoding="utf-8-sig"))

    def _write(self, name, payload):
        (self.tmp / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _active_version(self):
        return self._read("manifest.json")["active_version"]

    def _active_path(self, filename):
        return self.tmp / self._active_version() / filename

    def _refresh_manifest_hash(self, filename):
        path = self._active_path(filename)
        content = path.read_bytes()
        manifest = self._read("manifest.json")
        version = next(v for v in manifest["versions"] if v["version"] == manifest["active_version"])
        version["files"][filename] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
        self._write("manifest.json", manifest)

    def test_draft_version_is_rejected(self):
        manifest = self._read("manifest.json")
        next(v for v in manifest["versions"] if v["version"] == manifest["active_version"])["status"] = "draft"
        self._write("manifest.json", manifest)
        research_data.clear_cache()
        response = self.client.get("/api/research/status/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "version_not_reviewed")

    def test_hash_mismatch_is_rejected(self):
        path = self._active_path("cases.json")
        raw = path.read_text(encoding="utf-8-sig")
        # keep byte length stable so this tests hash mismatch, not size mismatch
        mutated = raw.replace("2026-11-01", "2025-11-01", 1)
        if mutated == raw:
            mutated = raw[:-1] + ("X" if raw[-1] != "X" else "Y")
        path.write_text(mutated, encoding="utf-8")
        research_data.clear_cache()
        response = self.client.get("/api/research/status/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "hash_mismatch")

    def test_invalid_json_is_rejected_after_manifest_refresh(self):
        path = self._active_path("cases.json")
        path.write_text("{ invalid json", encoding="utf-8")
        self._refresh_manifest_hash("cases.json")
        research_data.clear_cache()
        response = self.client.get("/api/research/status/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "invalid_json")

    def test_music_context_links_only_explicit_related_case(self):
        music = self._read(f"{self._active_version()}/music_scores.json")
        music["status"] = "complete"
        music["items"] = [
            {
                "music_id": "MUS001",
                "title": "春江花月夜",
                "category": "乐器",
                "subcategory": "古筝",
                "scores": {
                    "emotional_resonance": 80,
                    "timbre_identity": 80,
                    "melody_accessibility": 80,
                    "cultural_story": 80,
                    "adaptation_space": 80,
                    "visual_expressiveness": 80,
                    "era_theme_relevance": 80,
                    "existing_evidence": 80,
                },
                "related_case_ids": ["CASE001"],
            }
        ]
        self._write(f"{self._active_version()}/music_scores.json", music)
        self._refresh_manifest_hash("music_scores.json")
        research_data.clear_cache()
        response = self.client.get(
            "/api/research/music-context/",
            {"title": "春江花月夜", "category": "乐器", "subcategory": "古筝"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["association"]["status"], "linked")
        self.assertEqual(data["association"]["matched_by"], "exact_title")
        self.assertEqual(data["potential"]["total_score"], 80.0)
        self.assertEqual([item["case_id"] for item in data["related_cases"]], ["CASE001"])
        self.assertEqual(data["regional_rows"], [])

    def test_v11_strict_and_extended_samples_do_not_mix(self):
        manifest = self._read("manifest.json")
        manifest["active_version"] = "v1.1"
        next(v for v in manifest["versions"] if v["version"] == "v1.1")["status"] = "reviewed"
        self._write("manifest.json", manifest)
        research_data.clear_cache()

        candidate = self.client.get("/api/research/cases/", {"analysis_sample": "strict_candidate"}).json()["data"]
        self.assertEqual(candidate["total"], 3)
        self.assertEqual({item["case_id"] for item in candidate["items"]}, {"CASE005", "CASE006", "CASE007"})
        self.assertEqual(candidate["analysis_scope"]["strict_candidate_count"], 3)
        self.assertEqual(candidate["analysis_scope"]["owner_approved_count"], 2)
        self.assertEqual(candidate["analysis_scope"]["pending_owner_review_count"], 0)
        self.assertEqual(
            {item["owner_approval_status"] for item in candidate["items"]},
            {"approved", "needs_more_evidence"},
        )

        strict = self.client.get("/api/research/cases/", {"analysis_sample": "strict_individual"}).json()["data"]
        self.assertEqual(strict["total"], 2)
        self.assertEqual(strict["analysis_scope"]["strict_approved_case_count"], 2)

        extended = self.client.get("/api/research/cases/", {"analysis_sample": "extended_cross_cultural"}).json()["data"]
        self.assertEqual(extended["total"], 6)
        self.assertNotIn("CASE005", {item["case_id"] for item in extended["items"]})

        stats = self.client.get("/api/research/statistics/", {"analysis_sample": "strict_candidate"}).json()["data"]
        self.assertEqual(stats["analysis_scope"]["case_count"], 3)
        self.assertEqual(stats["analysis_scope"]["owner_approved_count"], 2)
        self.assertEqual(stats["sample"]["status"], "insufficient")

        approved_stats = self.client.get("/api/research/statistics/", {"analysis_sample": "strict_individual"}).json()["data"]
        self.assertEqual(approved_stats["analysis_scope"]["case_count"], 2)

        success = self.client.get("/api/research/success-factors/", {"analysis_sample": "strict_candidate"}).json()["data"]
        self.assertEqual(success["analysis_scope"]["case_count"], 3)
        self.assertEqual(success["availability"], "unavailable")
        self.assertIsNone(success["rankings"])

    def test_empty_cases_returns_empty_sample(self):
        cases = self._read(f"{self._active_version()}/cases.json")
        cases["cases"] = []
        cases["case_count"] = 0
        self._write(f"{self._active_version()}/cases.json", cases)
        self._refresh_manifest_hash("cases.json")
        research_data.clear_cache()
        response = self.client.get("/api/research/status/")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["sample"]["n"], 0)
        self.assertEqual(data["sample"]["status"], "empty")
        self.assertEqual(data["sample"]["progress_percent"], 0.0)
