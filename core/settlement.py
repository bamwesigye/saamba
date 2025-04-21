"""
Settlement logic for event selections based on match results.
This module handles marking selections as won, lost, or void based on event scores.
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)
from .models import EventSelection

def process_selections(event):
    """
    Process all selections for an event based on the entered scores.
    """
    # settle 1x2 Market
    home_win_selection = EventSelection.objects.filter(event=event, selection__id=1).first()
    draw_win_selection = EventSelection.objects.filter(event=event, selection__id=2).first()
    away_win_selection = EventSelection.objects.filter(event=event, selection__id=3).first()
    
    print("1x2 scores = ", event.fthg," - ", event.ftag)    
    if event.fthg > event.ftag:
        print("Home win")
        if home_win_selection:
            home_win_selection.status = 'W'
            home_win_selection.save()
            logger.info(f"Settled home win selection {home_win_selection.id} as won")
        
        if away_win_selection:
            away_win_selection.status = 'L'
            away_win_selection.save()
            logger.info(f"Settled away win selection {away_win_selection.id} as lost")
        
        if draw_win_selection:
            draw_win_selection.status = 'L'
            draw_win_selection.save()
            logger.info(f"Settled draw win selection {draw_win_selection.id} as lost")
    
    elif event.fthg < event.ftag:
        print("Away win")
        if away_win_selection:
            away_win_selection.status = 'W'
            away_win_selection.save()
            logger.info(f"Settled away win selection {away_win_selection.id} as won")
        
        if home_win_selection:
            home_win_selection.status = 'L'
            home_win_selection.save()
            logger.info(f"Settled home win selection {home_win_selection.id} as lost")
        
        if draw_win_selection:
            draw_win_selection.status = 'L'
            draw_win_selection.save()
            logger.info(f"Settled draw win selection {draw_win_selection.id} as lost")
    
    elif event.fthg == event.ftag:
        print("Draw win")
        if draw_win_selection:
            draw_win_selection.status = 'W'
            draw_win_selection.save()
            logger.info(f"Settled draw win selection {draw_win_selection.id} as won")
        
        if home_win_selection:
            home_win_selection.status = 'L'
            home_win_selection.save()
            logger.info(f"Settled home win selection {home_win_selection.id} as lost")
        
        if away_win_selection:
            away_win_selection.status = 'L'
            away_win_selection.save()
            logger.info(f"Settled away win selection {away_win_selection.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")

    # settle Double chance Market
    home_or_draw = EventSelection.objects.filter(event=event, selection__id=4).first()
    away_or_draw = EventSelection.objects.filter(event=event, selection__id=5).first()
    home_or_away = EventSelection.objects.filter(event=event, selection__id=6).first()

    if event.fthg > event.ftag:
        if home_or_draw:
            home_or_draw.status = 'W'
            home_or_draw.save()
            logger.info(f"Settled home or draw selection {home_or_draw.id} as won")
        
        if away_or_draw:
            away_or_draw.status = 'L'
            away_or_draw.save()
            logger.info(f"Settled away or draw selection {away_or_draw.id} as lost")
        
        if home_or_away:
            home_or_away.status = 'W'
            home_or_away.save()
            logger.info(f"Settled home or away selection {home_or_away.id} as won")
    
    elif event.fthg < event.ftag:
        if away_or_draw:
            away_or_draw.status = 'W'
            away_or_draw.save()
            logger.info(f"Settled away or draw selection {away_or_draw.id} as won")
        
        if home_or_draw:
            home_or_draw.status = 'L'
            home_or_draw.save()
            logger.info(f"Settled home or draw selection {home_or_draw.id} as lost")
        
        if home_or_away:
            home_or_away.status = 'W'
            home_or_away.save()
            logger.info(f"Settled home or away selection {home_or_away.id} as won")

    elif event.fthg == event.ftag:
        if home_or_draw:
            home_or_draw.status = 'W'
            home_or_draw.save()
            logger.info(f"Settled home or draw selection {home_or_draw.id} as won")
        
        if away_or_draw:
            away_or_draw.status = 'W'
            away_or_draw.save()
            logger.info(f"Settled away or draw selection {away_or_draw.id} as won")
        
        if home_or_away:
            home_or_away.status = 'L'
            home_or_away.save()
            logger.info(f"Settled home or away selection {home_or_away.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")

    #settle BTTS
    BTTS_yes = EventSelection.objects.filter(event=event, selection__id=7).first()
    BTTS_no = EventSelection.objects.filter(event=event, selection__id=8).first()
    
    if event.fthg > 0 and event.ftag > 0:
        if BTTS_yes:
            BTTS_yes.status = 'W'
            BTTS_yes.save()
            logger.info(f"Settled BTTS yes selection {BTTS_yes.id} as won")
        
        if BTTS_no:
            BTTS_no.status = 'L'
            BTTS_no.save()
            logger.info(f"Settled BTTS no selection {BTTS_no.id} as lost")
    
    else:
        if BTTS_no:
            BTTS_no.status = 'W'
            BTTS_no.save()
            logger.info(f"Settled BTTS no selection {BTTS_no.id} as won")
        
        if BTTS_yes:
            BTTS_yes.status = 'L'
            BTTS_yes.save()
            logger.info(f"Settled BTTS yes selection {BTTS_yes.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")

    #settle goals markets   
    #over 0.5 goals
    over_05 = EventSelection.objects.filter(event=event, selection__id=9).first()
    under_05 = EventSelection.objects.filter(event=event, selection__id=10).first()
    
    if event.fthg + event.ftag > 0.5:
        if over_05:
            over_05.status = 'W'
            over_05.save()
            logger.info(f"Settled over 0.5 goals selection {over_05.id} as won")
        
        if under_05:
            under_05.status = 'L'
            under_05.save()
            logger.info(f"Settled under 0.5 goals selection {under_05.id} as lost")
    
    else:
        if under_05:
            under_05.status = 'W'
            under_05.save()
            logger.info(f"Settled under 0.5 goals selection {under_05.id} as won")
        
        if over_05:
            over_05.status = 'L'
            over_05.save()
            logger.info(f"Settled over 0.5 goals selection {over_05.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    #over 1.5 goals
    over_15 = EventSelection.objects.filter(event=event, selection__id=11).first()
    under_15 = EventSelection.objects.filter(event=event, selection__id=12).first()
    
    if event.fthg + event.ftag > 1.5:
        if over_15:
            over_15.status = 'W'
            over_15.save()
            logger.info(f"Settled over 1.5 goals selection {over_15.id} as won")
        
        if under_15:
            under_15.status = 'L'
            under_15.save()
            logger.info(f"Settled under 1.5 goals selection {under_15.id} as lost")
    
    else:
        if under_15:
            under_15.status = 'W'
            under_15.save()
            logger.info(f"Settled under 1.5 goals selection {under_15.id} as won")
        
        if over_15:
            over_15.status = 'L'
            over_15.save()
            logger.info(f"Settled over 1.5 goals selection {over_15.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    #over 2.5 goals
    over_25 = EventSelection.objects.filter(event=event, selection__id=13).first()
    under_25 = EventSelection.objects.filter(event=event, selection__id=14).first()
    
    if event.fthg + event.ftag > 2.5:
        if over_25:
            over_25.status = 'W'
            over_25.save()
            logger.info(f"Settled over 2.5 goals selection {over_25.id} as won")
        
        if under_25:
            under_25.status = 'L'
            under_25.save()
            logger.info(f"Settled under 2.5 goals selection {under_25.id} as lost")
    
    else:
        if under_25:
            under_25.status = 'W'
            under_25.save()
            logger.info(f"Settled under 2.5 goals selection {under_25.id} as won")
        
        if over_25:
            over_25.status = 'L'
            over_25.save()
            logger.info(f"Settled over 2.5 goals selection {over_25.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")

    #over 3.5 goals
    over_35 = EventSelection.objects.filter(event=event, selection__id=15).first()
    under_35 = EventSelection.objects.filter(event=event, selection__id=16).first()
    
    if event.fthg + event.ftag > 3.5:
        if over_35:
            over_35.status = 'W'
            over_35.save()
            logger.info(f"Settled over 3.5 goals selection {over_35.id} as won")
        
        if under_35:
            under_35.status = 'L'
            under_35.save()
            logger.info(f"Settled under 3.5 goals selection {under_35.id} as lost")
    
    else:
        if under_35:
            under_35.status = 'W'
            under_35.save()
            logger.info(f"Settled under 3.5 goals selection {under_35.id} as won")
        
        if over_35:
            over_35.status = 'L'
            over_35.save()
            logger.info(f"Settled over 3.5 goals selection {over_35.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    #over 4.5 goals
    over_45 = EventSelection.objects.filter(event=event, selection__id=17).first()
    under_45 = EventSelection.objects.filter(event=event, selection__id=18).first()
    
    if event.fthg + event.ftag > 4.5:
        if over_45:
            over_45.status = 'W'
            over_45.save()
            logger.info(f"Settled over 4.5 goals selection {over_45.id} as won")
        
        if under_45:
            under_45.status = 'L'
            under_45.save()
            logger.info(f"Settled under 4.5 goals selection {under_45.id} as lost")
    
    else:
        if under_45:
            under_45.status = 'W'
            under_45.save()
            logger.info(f"Settled under 4.5 goals selection {under_45.id} as won")
        
        if over_45:
            over_45.status = 'L'
            over_45.save()
            logger.info(f"Settled over 4.5 goals selection {over_45.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #over 5.5 goals
    over_55 = EventSelection.objects.filter(event=event, selection__id=19).first()
    under_55 = EventSelection.objects.filter(event=event, selection__id=20).first()
    
    if event.fthg + event.ftag > 5.5:
        if over_55:
            over_55.status = 'W'
            over_55.save()
            logger.info(f"Settled over 5.5 goals selection {over_55.id} as won")
        
        if under_55:
            under_55.status = 'L'
            under_55.save()
            logger.info(f"Settled under 5.5 goals selection {under_55.id} as lost")
    
    else:
        if under_55:
            under_55.status = 'W'
            under_55.save()
            logger.info(f"Settled under 5.5 goals selection {under_55.id} as won")
        
        if over_55:
            over_55.status = 'L'
            over_55.save()
            logger.info(f"Settled over 5.5 goals selection {over_55.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #over 6.5 goals
    over_65 = EventSelection.objects.filter(event=event, selection__id=21).first()
    under_65 = EventSelection.objects.filter(event=event, selection__id=22).first()
    
    if event.fthg + event.ftag > 6.5:
        if over_65:
            over_65.status = 'W'
            over_65.save()
            logger.info(f"Settled over 6.5 goals selection {over_65.id} as won")
        
        if under_65:
            under_65.status = 'L'
            under_65.save()
            logger.info(f"Settled under 6.5 goals selection {under_65.id} as lost")
    
    else:
        if under_65:
            under_65.status = 'W'
            under_65.save()
            logger.info(f"Settled under 6.5 goals selection {under_65.id} as won")
        
        if over_65:
            over_65.status = 'L'
            over_65.save()
            logger.info(f"Settled over 6.5 goals selection {over_65.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #settle home team goals
    #over 0.5 home goals
    over_05_home = EventSelection.objects.filter(event=event, selection__id=23).first()
    under_05_home = EventSelection.objects.filter(event=event, selection__id=24).first()
    
    if event.fthg > 0.5:
        if over_05_home:
            over_05_home.status = 'W'
            over_05_home.save()
            logger.info(f"Settled over 0.5 home goals selection {over_05_home.id} as won")
        
        if under_05_home:
            under_05_home.status = 'L'
            under_05_home.save()
            logger.info(f"Settled under 0.5 home goals selection {under_05_home.id} as lost")
    
    else:
        if under_05_home:
            under_05_home.status = 'W'
            under_05_home.save()
            logger.info(f"Settled under 0.5 home goals selection {under_05_home.id} as won")
        
        if over_05_home:
            over_05_home.status = 'L'
            over_05_home.save()
            logger.info(f"Settled over 0.5 home goals selection {over_05_home.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #settle home team goals
    #over 1.5 home goals
    over_15_home = EventSelection.objects.filter(event=event, selection__id=25).first()
    under_15_home = EventSelection.objects.filter(event=event, selection__id=26).first()
    
    if event.fthg > 1.5:
        if over_15_home:
            over_15_home.status = 'W'
            over_15_home.save()
            logger.info(f"Settled over 1.5 home goals selection {over_15_home.id} as won")
        
        if under_15_home:
            under_15_home.status = 'L'
            under_15_home.save()
            logger.info(f"Settled under 1.5 home goals selection {under_15_home.id} as lost")
    
    else:
        if under_15_home:
            under_15_home.status = 'W'
            under_15_home.save()
            logger.info(f"Settled under 1.5 home goals selection {under_15_home.id} as won")
        
        if over_15_home:
            over_15_home.status = 'L'
            over_15_home.save()
            logger.info(f"Settled over 1.5 home goals selection {over_15_home.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #settle home team goals
    #over 2.5 home goals
    over_25_home = EventSelection.objects.filter(event=event, selection__id=27).first()
    under_25_home = EventSelection.objects.filter(event=event, selection__id=28).first()
    
    if event.fthg > 2.5:
        if over_25_home:
            over_25_home.status = 'W'
            over_25_home.save()
            logger.info(f"Settled over 2.5 home goals selection {over_25_home.id} as won")
        
        if under_25_home:
            under_25_home.status = 'L'
            under_25_home.save()
            logger.info(f"Settled under 2.5 home goals selection {under_25_home.id} as lost")
    
    else:
        if under_25_home:
            under_25_home.status = 'W'
            under_25_home.save()
            logger.info(f"Settled under 2.5 home goals selection {under_25_home.id} as won")
        
        if over_25_home:
            over_25_home.status = 'L'
            over_25_home.save()
            logger.info(f"Settled over 2.5 home goals selection {over_25_home.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #settle home team goals
    #over 3.5 home goals
    over_35_home = EventSelection.objects.filter(event=event, selection__id=29).first()
    
    if event.fthg > 3.5:
        if over_35_home:
            over_35_home.status = 'W'
            over_35_home.save()
            logger.info(f"Settled over 3.5 home goals selection {over_35_home.id} as won")
    else:        
        if over_35_home:
            over_35_home.status = 'L'
            over_35_home.save()
            logger.info(f"Settled over 3.5 home goals selection {over_35_home.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #settle away team goals
    #over 0.5 away goals
    over_05_away = EventSelection.objects.filter(event=event, selection__id=30).first()
    under_05_away = EventSelection.objects.filter(event=event, selection__id=31).first()
    
    if event.ftag > 0.5:
        if over_05_away:
            over_05_away.status = 'W'
            over_05_away.save()
            logger.info(f"Settled over 0.5 away goals selection {over_05_away.id} as won")
        if under_05_away:
            under_05_away.status = 'L'
            under_05_away.save()
            logger.info(f"Settled under 0.5 away goals selection {under_05_away.id} as lost")
    else:        
        if over_05_away:
            over_05_away.status = 'L'
            over_05_away.save()
            logger.info(f"Settled over 0.5 away goals selection {over_05_away.id} as lost")
        if under_05_away:
            under_05_away.status = 'W'
            under_05_away.save()
            logger.info(f"Settled under 0.5 away goals selection {under_05_away.id} as won")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #settle away team goals
    #over 1.5 away goals
    over_15_away = EventSelection.objects.filter(event=event, selection__id=32).first()
    under_15_away = EventSelection.objects.filter(event=event, selection__id=33).first()
    
    if event.ftag > 1.5:
        if over_15_away:
            over_15_away.status = 'W'
            over_15_away.save()
            logger.info(f"Settled over 1.5 away goals selection {over_15_away.id} as won")
        if under_15_away:
            under_15_away.status = 'L'
            under_15_away.save()
            logger.info(f"Settled under 1.5 away goals selection {under_15_away.id} as lost")
    else:        
        if over_15_away:
            over_15_away.status = 'L'
            over_15_away.save()
            logger.info(f"Settled over 1.5 away goals selection {over_15_away.id} as lost")
        if under_15_away:
            under_15_away.status = 'W'
            under_15_away.save()
            logger.info(f"Settled under 1.5 away goals selection {under_15_away.id} as won")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
            
    #settle away team goals
    #over 2.5 away goals
    over_25_away = EventSelection.objects.filter(event=event, selection__id=34).first()
    under_25_away = EventSelection.objects.filter(event=event, selection__id=35).first()
    
    if event.ftag > 2.5:
        if over_25_away:
            over_25_away.status = 'W'
            over_25_away.save()
            logger.info(f"Settled over 2.5 away goals selection {over_25_away.id} as won")
        if under_25_away:
            under_25_away.status = 'L'
            under_25_away.save()
            logger.info(f"Settled under 2.5 away goals selection {under_25_away.id} as lost")
    else:        
        if over_25_away:
            over_25_away.status = 'L'
            over_25_away.save()
            logger.info(f"Settled over 2.5 away goals selection {over_25_away.id} as lost")
        if under_25_away:
            under_25_away.status = 'W'
            under_25_away.save()
            logger.info(f"Settled under 2.5 away goals selection {under_25_away.id} as won")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    #settle away team goals
    #over 3.5 away goals
    over_35_away = EventSelection.objects.filter(event=event, selection__id=36).first()
    
    if event.ftag > 3.5:
        if over_35_away:
            over_35_away.status = 'W'
            over_35_away.save()
            logger.info(f"Settled over 3.5 away goals selection {over_35_away.id} as won")

    else:        
        if over_35_away:
            over_35_away.status = 'L'
            over_35_away.save()
            logger.info(f"Settled over 3.5 away goals selection {over_35_away.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    # settle first half win
    first_half_home_win = EventSelection.objects.filter(event=event, selection__id=37).first()
    first_half_draw_win = EventSelection.objects.filter(event=event, selection__id=38).first()
    first_half_away_win = EventSelection.objects.filter(event=event, selection__id=39).first()
    print("first half score = ", event.hthg," - ", event.htag)
    if event.hthg > event.htag:
        if first_half_home_win:
            first_half_home_win.status = 'W'
            first_half_home_win.save()
            logger.info(f"Settled first half home win selection {first_half_home_win.id} as won")
        if first_half_away_win:
            first_half_away_win.status = 'L'
            first_half_away_win.save()
            logger.info(f"Settled first half away win selection {first_half_away_win.id} as lost")
        if first_half_draw_win:
            first_half_draw_win.status = 'L'
            first_half_draw_win.save()
            logger.info(f"Settled first half draw win selection {first_half_draw_win.id} as lost")
    elif event.hthg < event.htag:        
        if first_half_home_win:
            first_half_home_win.status = 'L'
            first_half_home_win.save()
            logger.info(f"Settled first half home win selection {first_half_home_win.id} as lost")
        if first_half_away_win:
            first_half_away_win.status = 'W'
            first_half_away_win.save()
            logger.info(f"Settled first half away win selection {first_half_away_win.id} as won")
        if first_half_draw_win:
            first_half_draw_win.status = 'L'
            first_half_draw_win.save()
            logger.info(f"Settled first half draw win selection {first_half_draw_win.id} as lost")
    elif event.hthg == event.htag:
        if first_half_home_win:
            first_half_home_win.status = 'L'
            first_half_home_win.save()
            logger.info(f"Settled first half home win selection {first_half_home_win.id} as lost")
        if first_half_away_win:
            first_half_away_win.status = 'L'
            first_half_away_win.save()
            logger.info(f"Settled first half away win selection {first_half_away_win.id} as lost")
        if first_half_draw_win:
            first_half_draw_win.status = 'W'
            first_half_draw_win.save()
            logger.info(f"Settled first half draw win selection {first_half_draw_win.id} as won")

    #settle second half win
    second_half_home_win = EventSelection.objects.filter(event=event, selection__id=40).first()
    second_half_draw_win = EventSelection.objects.filter(event=event, selection__id=41).first()
    second_half_away_win = EventSelection.objects.filter(event=event, selection__id=42).first()
    
    if (event.fthg-event.hthg) > (event.ftag-event.htag):
        if second_half_home_win:
            second_half_home_win.status = 'W'
            second_half_home_win.save()
            logger.info(f"Settled second half home win selection {second_half_home_win.id} as won")
        if second_half_away_win:
            second_half_away_win.status = 'L'
            second_half_away_win.save()
            logger.info(f"Settled second half away win selection {second_half_away_win.id} as lost")
        if second_half_draw_win:
            second_half_draw_win.status = 'L'
            second_half_draw_win.save()
            logger.info(f"Settled second half draw win selection {second_half_draw_win.id} as lost")
    elif (event.fthg-event.hthg) < (event.ftag-event.htag):
        if second_half_home_win:
            second_half_home_win.status = 'L'
            second_half_home_win.save()
            logger.info(f"Settled second half home win selection {second_half_home_win.id} as lost")
        if second_half_away_win:
            second_half_away_win.status = 'W'
            second_half_away_win.save()
            logger.info(f"Settled second half away win selection {second_half_away_win.id} as won")
        if second_half_draw_win:
            second_half_draw_win.status = 'L'
            second_half_draw_win.save()
            logger.info(f"Settled second half draw win selection {second_half_draw_win.id} as lost")
    elif (event.fthg-event.hthg) == (event.ftag-event.htag):
        if second_half_draw_win:
            second_half_draw_win.status = 'W'
            second_half_draw_win.save()
            logger.info(f"Settled second half draw win selection {second_half_draw_win.id} as won")
        if second_half_home_win:
            second_half_home_win.status = 'L'
            second_half_home_win.save()
            logger.info(f"Settled second half home win selection {second_half_home_win.id} as lost")
        if second_half_away_win:
            second_half_away_win.status = 'L'
            second_half_away_win.save()
            logger.info(f"Settled second half away win selection {second_half_away_win.id} as lost")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    #settle first half goals
    #settle over 0.5goals
    first_half_over_05 = EventSelection.objects.filter(event=event, selection__id=43).first()
    first_half_under_05 = EventSelection.objects.filter(event=event, selection__id=44).first()
    
    if event.fthg > 0.5:
        if first_half_over_05:
            first_half_over_05.status = 'W'
            first_half_over_05.save()
            logger.info(f"Settled first half over 0.5 goals selection {first_half_over_05.id} as won")
        if first_half_under_05:
            first_half_under_05.status = 'L'
            first_half_under_05.save()
            logger.info(f"Settled first half under 0.5 goals selection {first_half_under_05.id} as lost")
    else:
        if first_half_over_05:
            first_half_over_05.status = 'L'
            first_half_over_05.save()
            logger.info(f"Settled first half over 0.5 goals selection {first_half_over_05.id} as lost")
        if first_half_under_05:
            first_half_under_05.status = 'W'
            first_half_under_05.save()
            logger.info(f"Settled first half under 0.5 goals selection {first_half_under_05.id} as won")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    #settle over 1.5 goals
    first_half_over_15 = EventSelection.objects.filter(event=event, selection__id=45).first()
    first_half_under_15 = EventSelection.objects.filter(event=event, selection__id=46).first()
    
    if event.fthg > 1.5:
        if first_half_over_15:
            first_half_over_15.status = 'W'
            first_half_over_15.save()
            logger.info(f"Settled first half over 1.5 goals selection {first_half_over_15.id} as won")
        if first_half_under_15:
            first_half_under_15.status = 'L'
            first_half_under_15.save()
            logger.info(f"Settled first half under 1.5 goals selection {first_half_under_15.id} as lost")
    else:
        if first_half_over_15:
            first_half_over_15.status = 'L'
            first_half_over_15.save()
            logger.info(f"Settled first half over 1.5 goals selection {first_half_over_15.id} as lost")
        if first_half_under_15:
            first_half_under_15.status = 'W'
            first_half_under_15.save()
            logger.info(f"Settled first half under 1.5 goals selection {first_half_under_15.id} as won")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")
    
    #settle over 2.5 goals
    first_half_over_25 = EventSelection.objects.filter(event=event, selection__id=47).first()
    first_half_under_25 = EventSelection.objects.filter(event=event, selection__id=48).first()
    
    if event.fthg > 2.5:
        if first_half_over_25:
            first_half_over_25.status = 'W'
            first_half_over_25.save()
            logger.info(f"Settled first half over 2.5 goals selection {first_half_over_25.id} as won")
        if first_half_under_25:
            first_half_under_25.status = 'L'
            first_half_under_25.save()
            logger.info(f"Settled first half under 2.5 goals selection {first_half_under_25.id} as lost")
    else:
        if first_half_over_25:
            first_half_over_25.status = 'L'
            first_half_over_25.save()
            logger.info(f"Settled first half over 2.5 goals selection {first_half_over_25.id} as lost")
        if first_half_under_25:
            first_half_under_25.status = 'W'
            first_half_under_25.save()
            logger.info(f"Settled first half under 2.5 goals selection {first_half_under_25.id} as won")
    
    event.scores_confirmed = True
    event.save()
    logger.info(f"Settled event {event.id} scores confirmed")    
    