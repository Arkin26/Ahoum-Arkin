from rest_framework.response import Response


def api_error(detail, code, status_code):
    return Response({"detail": detail, "code": code}, status=status_code)
