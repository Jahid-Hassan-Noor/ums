from django.core.management.base import BaseCommand, CommandError

from chatbot_app.search_indexer import DOMAIN_INDEXERS, rebuild_search_index


class Command(BaseCommand):
    help = "Rebuild the chatbot/global search index from safe portal sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain",
            action="append",
            choices=sorted(DOMAIN_INDEXERS.keys()),
            help="Limit rebuild to one domain. Can be passed more than once.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be indexed without writing database rows.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing rows for selected domains before rebuilding.",
        )

    def handle(self, *args, **options):
        domains = options.get("domain") or list(DOMAIN_INDEXERS.keys())
        unknown = sorted(set(domains) - set(DOMAIN_INDEXERS))
        if unknown:
            raise CommandError(f"Unknown domain(s): {', '.join(unknown)}")

        report = rebuild_search_index(
            domains=domains,
            clear=options["clear"],
            dry_run=options["dry_run"],
        )
        for domain, counts in report.items():
            if "error" in counts:
                self.stderr.write(f"{domain}: {counts['error']}")
                continue
            self.stdout.write(
                "{domain}: seen={seen} created={created} updated={updated} "
                "unchanged={unchanged} dry_run={dry_run} "
                "skipped_sensitive={skipped_sensitive} hidden_stale={hidden_stale}".format(
                    domain=domain,
                    **counts,
                )
            )
