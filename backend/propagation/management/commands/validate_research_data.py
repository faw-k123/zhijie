"""Django management command: validate research/data before API use."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from propagation import research_data


class Command(BaseCommand):
    help = "校验 research/data/manifest.json、active_version、四个 JSON 的 SHA256 与记录结构"

    def handle(self, *args, **options):
        try:
            bundle = research_data.load_bundle()
        except research_data.ResearchDataError as exc:
            raise CommandError(f"[{exc.code}] {exc.message}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"OK active_version={bundle.version} status={bundle.version_meta.get('status')} "
                f"cases={len(bundle.cases)} scores={len(bundle.scores)} warnings={len(bundle.warnings)}"
            )
        )
        if bundle.warnings:
            self.stdout.write(self.style.WARNING("存在被隔离的记录："))
            for warning in bundle.warnings:
                self.stdout.write(
                    f"- {warning.get('file')} / {warning.get('record')}: {warning.get('reason')}"
                )
