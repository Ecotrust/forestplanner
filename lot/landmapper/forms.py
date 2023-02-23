from .models import Profile, TwoWeekFollowUpSurvey

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            'type_selection',
            'type_other',
            'has_plan',
            'plan_date',
            'q3_1_health',
            'q3_2_habitat',
            'q3_3_beauty', 
            'q3_4_next_gen',
            'q3_5_risks',
            'q3_6_climate_change',
            'q3_7_carbon',
            'q3_8_invasive_species',
            'q3_9_timber',
            'q3_10_profit',
            'q3_11_cultural_uses'
        )

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = TwoWeekFollowUpSurvey
        fields = (
            'q4a_1_land_management',
            'q4a_2_issue',
            'q4a_3_coordinate',
            'q4a_4_decision',
            'q4a_5_activity',
            'q4a_6_information',
            'q4a_7_plan',
            'feedback'
        )