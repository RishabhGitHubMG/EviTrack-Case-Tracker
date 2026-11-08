from django.core.management.base import BaseCommand
from django.urls import include, path
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiYamlRenderer
from drf_spectacular.validation import validate_schema


class Command(BaseCommand):
    help = 'Write the /api/v1/ OpenAPI schema to a YAML file (same routes as /api/schema/).'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='docs/openapi.yaml')

    def handle(self, *args, **options):
        patterns = [path('api/v1/', include('apps.core.api.urls'))]
        schema = SchemaGenerator(patterns=patterns).get_schema(request=None, public=True)
        validate_schema(schema)
        with open(options['file'], 'wb') as f:
            f.write(OpenApiYamlRenderer().render(schema))
        self.stdout.write(f"Wrote {options['file']}")
