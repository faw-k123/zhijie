"""把当前研究版本同步到独立的 SQL Server 分析表（不改业务表/不建 Django migration）。"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from propagation import research_data


DDL = [
    """
    IF OBJECT_ID(N'dbo.research_case_analysis', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.research_case_analysis (
            case_id NVARCHAR(16) NOT NULL PRIMARY KEY,
            candidate_id NVARCHAR(32) NULL,
            performer NVARCHAR(240) NOT NULL,
            country NVARCHAR(80) NULL,
            region NVARCHAR(80) NULL,
            instrument NVARCHAR(400) NULL,
            case_type NVARCHAR(64) NULL,
            extended_category NVARCHAR(64) NULL,
            analysis_sample NVARCHAR(64) NULL,
            performance_status NVARCHAR(64) NULL,
            review_status NVARCHAR(2) NULL,
            source_count INT NOT NULL,
            data_version NVARCHAR(16) NOT NULL,
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
        )
    END
    """,
    """
    IF OBJECT_ID(N'dbo.research_score_analysis', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.research_score_analysis (
            case_id NVARCHAR(16) NOT NULL,
            indicator_id NVARCHAR(64) NOT NULL,
            score DECIMAL(4,1) NULL,
            evidence NVARCHAR(MAX) NULL,
            source_ids NVARCHAR(MAX) NULL,
            missing_reason NVARCHAR(MAX) NULL,
            data_version NVARCHAR(16) NOT NULL,
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_research_score_analysis PRIMARY KEY (case_id, indicator_id)
        )
    END
    """,
    """
    IF OBJECT_ID(N'dbo.research_source_analysis', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.research_source_analysis (
            case_id NVARCHAR(16) NOT NULL,
            source_id NVARCHAR(32) NOT NULL,
            title NVARCHAR(500) NOT NULL,
            publisher NVARCHAR(240) NULL,
            url NVARCHAR(1000) NULL,
            source_type NVARCHAR(32) NULL,
            published_at NVARCHAR(64) NULL,
            reliability NVARCHAR(16) NULL,
            data_version NVARCHAR(16) NOT NULL,
            created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_research_source_analysis PRIMARY KEY (case_id, source_id)
        )
    END
    """,
    """
    IF COL_LENGTH(N'dbo.research_case_analysis', N'performance_status') IS NOT NULL
        ALTER TABLE dbo.research_case_analysis ALTER COLUMN performance_status NVARCHAR(MAX) NULL
    """,
]


class Command(BaseCommand):
    help = "将当前研究版本写入独立的 SQL Server 分析表；不修改业务表。"

    def add_arguments(self, parser):
        parser.add_argument("--target-version", default=None, help="目标版本；默认 active_version")

    def handle(self, *args, **options):
        bundle = research_data.load_bundle()
        version = options.get("target_version") or bundle.version
        if version != bundle.version:
            raise CommandError(f"只允许同步当前 active_version={bundle.version}，收到 {version}")

        cases = bundle.cases
        scores = bundle.scores
        case_rows = []
        score_rows = []
        source_rows = []
        for case in cases:
            cid = case["case_id"]
            instruments = case.get("instrument") or []
            case_rows.append((
                cid, case.get("candidate_id"), case.get("performer") or "",
                case.get("country"), case.get("region"), "/".join(instruments),
                case.get("case_type"), case.get("extended_category"),
                case.get("analysis_sample"), case.get("event_date_text"),
                case.get("review_status"), int(case.get("source_count") or 0), version,
            ))
            for source in case.get("sources") or []:
                source_rows.append((
                    cid, source.get("source_id"), source.get("title") or "",
                    source.get("publisher"), source.get("url"), source.get("source_type"),
                    source.get("published_at"), source.get("reliability"), version,
                ))
        for score in scores:
            source_ids = score.get("source_ids") or []
            score_rows.append((
                score.get("case_id"), score.get("indicator_id"), score.get("score"),
                score.get("evidence"), ";".join(str(x) for x in source_ids),
                score.get("missing_reason"), version,
            ))

        with transaction.atomic():
            with connection.cursor() as cursor:
                for sql in DDL:
                    cursor.execute(sql)
                cursor.execute("DELETE FROM dbo.research_score_analysis WHERE data_version = %s", [version])
                cursor.execute("DELETE FROM dbo.research_source_analysis WHERE data_version = %s", [version])
                cursor.execute("DELETE FROM dbo.research_case_analysis WHERE data_version = %s", [version])
                cursor.executemany(
                    """INSERT INTO dbo.research_case_analysis
                    (case_id,candidate_id,performer,country,region,instrument,case_type,extended_category,
                     analysis_sample,performance_status,review_status,source_count,data_version)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    case_rows,
                )
                cursor.executemany(
                    """INSERT INTO dbo.research_score_analysis
                    (case_id,indicator_id,score,evidence,source_ids,missing_reason,data_version)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    score_rows,
                )
                cursor.executemany(
                    """INSERT INTO dbo.research_source_analysis
                    (case_id,source_id,title,publisher,url,source_type,published_at,reliability,data_version)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    source_rows,
                )
                cursor.execute("SELECT COUNT(*) FROM dbo.research_case_analysis WHERE data_version = %s", [version])
                case_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM dbo.research_score_analysis WHERE data_version = %s", [version])
                score_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM dbo.research_source_analysis WHERE data_version = %s", [version])
                source_count = cursor.fetchone()[0]

        self.stdout.write(self.style.SUCCESS(
            f"OK version={version} cases={case_count} scores={score_count} sources={source_count}"
        ))
