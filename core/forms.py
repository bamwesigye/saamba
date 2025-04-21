from django import forms
from django.forms import ModelForm, HiddenInput, Form, IntegerField, BooleanField, ValidationError
from .models import EventOdds

class EventOddsForm(ModelForm):
    """
    Form for updating odds for an event selection
    """
    class Meta:
        model = EventOdds
        fields = ['event_selection', 'bookmaker', 'odd']
        widgets = {
            'event_selection': HiddenInput(),
            'bookmaker': HiddenInput(),
        }

class ScoreEntryForm(Form):
    """
    Form for entering match scores and settling selections
    """
    hthg = IntegerField(label='Home Team - Half Time', required=True, min_value=0)
    htag = IntegerField(label='Away Team - Half Time', required=True, min_value=0)
    fthg = IntegerField(label='Home Team - Full Time', required=True, min_value=0)
    ftag = IntegerField(label='Away Team - Full Time', required=True, min_value=0)
    confirm_scores = BooleanField(label='Confirm Scores and Settle Selections', required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        # Validate that full-time scores are consistent with half-time scores
        hthg = cleaned_data.get('hthg')
        htag = cleaned_data.get('htag')
        fthg = cleaned_data.get('fthg')
        ftag = cleaned_data.get('ftag')
        
        if hthg is not None and htag is not None and fthg is not None and ftag is not None:
            if fthg < hthg:
                raise ValidationError("Full-time home goals cannot be less than half-time home goals")
            if ftag < htag:
                raise ValidationError("Full-time away goals cannot be less than half-time away goals")
        
        return cleaned_data
