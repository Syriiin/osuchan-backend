from django.shortcuts import render
from django.conf import settings

def main(request):
    if settings.BETA and (not request.user.is_authenticated or not request.user.is_beta_tester):
        return render(request, "beta.html")
    return render(request, "index.html")
