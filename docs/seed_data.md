# Seed Data And Demo Packs

Use `bootstrap_university` for a fresh generic installation:

```bash
python manage.py bootstrap_university
```

This creates generic settings records from the platform settings registry and
synchronizes existing Django superusers into admin role profiles. It does not
create schools, centers, departments, programmes, students, staff, public pages,
or AIU-specific data.

To create an admin during bootstrap, pass an explicit email:

```bash
python manage.py bootstrap_university --admin-email admin@example.edu
```

If `--admin-password` is omitted, a newly created optional admin gets an
unusable password. Set the password through the normal admin/password reset
flow, or pass `--admin-password` only for local disposable environments.

## Demo Commands

Demo data is opt-in:

```bash
python manage.py seed_neutral_demo_data
python manage.py seed_aiu_demo_data
python manage.py seed_aiu_demo_content
python manage.py seed_all_data
```

- `seed_neutral_demo_data` creates a small non-AIU fixture using
  `demo-university.example` users and `DEMO-*` academic records.
- `seed_aiu_demo_data` creates AIU organization, people, programme, and public
  content demo records. It is useful for local AIU-specific testing only.
- `seed_aiu_demo_content` creates only the AIU public CMS demo content.
- `seed_all_data` is the legacy full local-development demo seed. Do not treat
  it as a production bootstrap path.
- `seed_ums_organisation` is a compatibility alias for `seed_aiu_demo_data`.

## Removing Demo Data Safely

For disposable local databases, prefer recreating the database or running Django
`flush` after taking any backup you need.

For shared or long-lived databases:

1. Take a database backup first.
2. Confirm no real users depend on demo rows.
3. Remove neutral demo records by the `DEMO-*` code prefix and
   `demo-university.example` email domain.
4. Remove AIU demo records by the `@aiu.edu.my` email domain and known AIU demo
   organization codes such as `SBSS`, `SEHS`, `SCI`, `ACE-SEDI`, `CRIM`, and
   `CCIE`.
5. Re-run `bootstrap_university` after deletion to restore generic settings
   defaults if needed.

Avoid loading any demo command in production unless the database is explicitly a
demo or training tenant.
