from rest_framework import serializers

from apps.cases.models import Case


class UserRefSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.SerializerMethodField()
    role = serializers.CharField(read_only=True)
    initials = serializers.SerializerMethodField()

    def get_name(self, user):
        return user.get_full_name().strip() or user.email

    def get_initials(self, user):
        name = user.get_full_name().strip()
        if not name:
            return user.email[:1].upper()
        return ''.join(part[0] for part in name.split()[:2]).upper()


class CaseRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ('id', 'case_no', 'title')


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()
