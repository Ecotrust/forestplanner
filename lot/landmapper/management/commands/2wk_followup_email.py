from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.utils import timezone
from landmapper.models import TwoWeekFollowUpSurvey

class Command(BaseCommand):
    help = 'Reminds users to fill out their 2-week follow-up survey'

    def handle(self, *args, **options):
        TWO_WEEKS = 14
        # Get all eligible users
        #   Registers >= 2 weeks ago
        #   Has no TwoWeekFollowUpSurvey or no TwoWeekFollowUpSurvey with 'email-sent' and not 'survey-complete'

        ineligible_user_IDs = [x.user.pk for x in TwoWeekFollowUpSurvey.objects.exclude(email_sent=False, survey_complete=False)]
        users_to_email = User.objects.filter(date_joined__lte=timezone.now()-timedelta(days=14)).exclude(pk__in=ineligible_user_IDs)

        # For each:
        #   * populate and send draft email
        #   * Create/Update their record with 'email-sent' as 'True'
        email_template = 'landmapper/emails/2wk-followup-survey.html'
        context = {
            'protocol': 'https',
            'domain': 'landmapper.ecotrust.org',
            'site_name': 'LandMapper'
        }

        try:
            sites = Site.objects.all()
            if sites.count() > 0:
                site = sites[0]
                if site.domain and site.domain.length > 0:
                    context['domain'] = site.domain
                if site.name and site.name.length > 0:
                    context['site_name'] = site.name
        except Exception as e:
            pass
        for user in users_to_email:
            context['username'] = user.username
            subject = "Thank you for using LandMapper"
            message = render_to_string(
                template_name=email_template,
                context=context,
                request=None,
            )
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

            (survey, created) = TwoWeekFollowUpSurvey.objects.get_or_create(user=user, email_sent=False)
            survey.email_sent = True
            survey.save()

