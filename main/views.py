from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

from common.utils import get_beatmap_path

def main(request):
    if settings.BETA and (not request.user.is_authenticated or not request.user.is_beta_tester):
        return render(request, "beta.html")
    if settings.MAINTENANCE and (not request.user.is_authenticated or not request.user.is_superuser):
        return render(request, "maintenance.html")
    return render(request, "index.html")

def getBeatmapFile(request, beatmap_id):
    with open(get_beatmap_path(beatmap_id), encoding="utf8") as fp:
        response = HttpResponse(fp.read())
        response["Content-Type"] = "text/plain"
        return response
