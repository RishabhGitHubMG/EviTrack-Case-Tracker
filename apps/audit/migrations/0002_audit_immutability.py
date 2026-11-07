from django.db import migrations


def create_audit_triggers(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'sqlite':
        schema_editor.execute('''
            CREATE TRIGGER audit_log_no_update
            BEFORE UPDATE ON audit_log
            BEGIN
                SELECT RAISE(ABORT, 'audit_log rows are immutable');
            END;
        ''')
        schema_editor.execute('''
            CREATE TRIGGER audit_log_no_delete
            BEFORE DELETE ON audit_log
            BEGIN
                SELECT RAISE(ABORT, 'audit_log rows are immutable');
            END;
        ''')
    elif vendor == 'postgresql':
        schema_editor.execute('''
            CREATE FUNCTION audit_log_reject_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'audit_log rows are immutable';
            END;
            $$ LANGUAGE plpgsql;
        ''')
        schema_editor.execute('''
            CREATE TRIGGER audit_log_no_mutation
            BEFORE UPDATE OR DELETE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION audit_log_reject_mutation();
        ''')


def drop_audit_triggers(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'sqlite':
        schema_editor.execute('DROP TRIGGER IF EXISTS audit_log_no_update;')
        schema_editor.execute('DROP TRIGGER IF EXISTS audit_log_no_delete;')
    elif vendor == 'postgresql':
        schema_editor.execute('DROP TRIGGER IF EXISTS audit_log_no_mutation ON audit_log;')
        schema_editor.execute('DROP FUNCTION IF EXISTS audit_log_reject_mutation();')


class Migration(migrations.Migration):
    dependencies = [('audit', '0001_initial')]

    operations = [migrations.RunPython(create_audit_triggers, drop_audit_triggers)]
