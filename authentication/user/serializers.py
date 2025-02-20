from user.models import CustomUser
from rest_framework import serializers


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    uuid = serializers.SerializerMethodField()

    def get_uuid(self, obj):
        return  str(obj.uuid.hex)

    class Meta:
        model = CustomUser
        fields = ("uuid", "username", "email", "first_name", "last_name", "is_staff", "is_superuser")
        read_only_fields = ("email",)


class CustomJWTSerializer(serializers.Serializer):
    access = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def get_access(self, obj):
        return str(obj["access_token"])

    def get_refresh(self, obj):
        return str(obj["refresh_token"])

    def get_user(self, obj):
        """
        Use UserDetailsSerializer and access/refresh for JWT.
        """
        return UserDetailsSerializer(obj["user"], context=self.context).data


class CustomJWTSerializerWithExpiration(CustomJWTSerializer):
    accessTokenExpiration = serializers.DateTimeField()
    refreshTokenExpiration = serializers.DateTimeField()
