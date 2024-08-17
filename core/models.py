from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.


class Market(models.Model):
    market = models.CharField(_("Market Name"), max_length=50)

    

    class Meta:
        verbose_name = _("Market")
        verbose_name_plural = _("Markets")

    def __str__(self):
        return self.market

    # def get_absolute_url(self):
    #     return reverse("Market_detail", kwargs={"pk": self.pk})


class Selections(models.Model):
    market = models.ForeignKey(Market, verbose_name=_("Market"), related_name='selections', on_delete=models.CASCADE)
    selection_code = models.CharField(_("Seclection Code"), max_length=50, unique=True)
    selection = models.CharField(_("Selection"), max_length=50)
    desription = models.CharField(_("description"), max_length=50)   

    class Meta:
        verbose_name = _("Selections")
        verbose_name_plural = _("Selectionss")

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse("Selections_detail", kwargs={"pk": self.pk})

class Bookmakers(models.Model):

    name = models.CharField(_(""), max_length=50)

    class Meta:
        verbose_name = _("Bookmaker")
        verbose_name_plural = _("Bookmakers")

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})

class BetLink(models.Model):

    league_code = models.CharField(_("league Code"), max_length=50)
    link_url = models.URLField(_("link"), max_length=200)
    league = models.CharField(_("league"), max_length=50)
    country = models.CharField(_("Country"), max_length=50)
    Level = models.CharField(_("Level"), max_length=50)
    order = models.FloatField(_("order"), default=2.0)
    model_value = models.IntegerField(_("model_value"), default=0)

    class Meta:
        ordering = ['league_code']
        verbose_name = _("Betlink")
        verbose_name_plural = _("Betlinks")

    def __str__(self):
        return f"{self.league}"
    # def get_absolute_url(self):
    #     return reverse("betlink_detail", kwargs={"pk": self.pk})


class Event(models.Model):
    event_link = models.URLField(_("event link"), max_length=200, unique=True)
    event_time = models.CharField(_("event time"), max_length=50)
    event_particpants = models.CharField(_(""), max_length=100)
    tournament = models.CharField(_("Tournament"), max_length=50)    

    class Meta:
        verbose_name = _("Events")
        verbose_name_plural = _("Events")

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse("Events_detail", kwargs={"pk": self.pk})


class EventSelection(models.Model):
    event = models.ForeignKey(Event,verbose_name=_(""), related_name='event_selections', on_delete=models.CASCADE)
    selection = models.ForeignKey(Selections, verbose_name=_(""), on_delete=models.CASCADE)
    class Meta:
        verbose_name = _("EventSelection")
        verbose_name_plural = _("EventSelections")

    def __str__(self):
        return self.event

    # def get_absolute_url(self):
    #     return reverse("EventSelection_detail", kwargs={"pk": self.pk})

class EventOdds(models.Model):
    event_selection = models.ForeignKey(EventSelection, verbose_name=_(""), on_delete=models.CASCADE)
    entered_at = models.DateTimeField(_("Time Entered"), auto_now=False, auto_now_add=True)
    odd = models.DecimalField(_("Odds Value"), max_digits=5, decimal_places=3)
    

    class Meta:
        verbose_name = _("EventOdds")
        verbose_name_plural = _("EventOddss")

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse("EventOdds_detail", kwargs={"pk": self.pk})


class BetpawaBets(models.Model):
    event_time = models.DateTimeField(_("Match Time"), blank=True, null=True)
    event_link = models.URLField(_("Event Link"), max_length=200)
    event_match = models.CharField(_("Event Match"), max_length=255)
    event_tournament = models.CharField(_("Tournament"), max_length=50)
    selection = models.CharField(_("Selection"), max_length=50)
    selection_odds = models.DecimalField(_("Odds"), max_digits=5, decimal_places=2, null=True, blank=True)
    event_data = models.CharField(_("data"), max_length=50)
    is_placed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['event_link','selection']
        verbose_name = _("betpawabets")
        verbose_name_plural = _("betpawabets")

    def __str__(self):
        return f"{self.event_match} - {self.event_tournament}"

    # def get_absolute_url(self):
    #     return reverse("betpawabets_detail", kwargs={"pk": self.pk})


class PlacedBets(models.Model):
    betcode = models.CharField(_("betcode"), max_length=50, null=True, blank=True)
    betid = models.CharField(_("betid"), max_length=50, null=True, blank=True)
    betlink = models.URLField(_("betlink"), max_length=200)
    won_legs = models.PositiveBigIntegerField(_("won_legs"), default=0)
    lost_legs = models.PositiveBigIntegerField(_("lost_legs"), default=0)
    pending_legs = models.PositiveBigIntegerField(_("pending_legs"), default=0)
    postponed_legs = models.PositiveBigIntegerField(_("postponed_legs"), default=0)
    stake   = models.PositiveBigIntegerField(_("stake"), default=0)
    odds = models.DecimalField(_("odds"), max_digits=20, decimal_places=2, default = 1.00)
    payout  = models.PositiveBigIntegerField(_("payout"), default=0)

    class Meta:
        verbose_name = _("placedbets")
        verbose_name_plural = _("placedbets")

    def __str__(self):
        return self.betcode

    # def get_absolute_url(self):
    #     return reverse("placedbets_detail", kwargs={"pk": self.pk})

class BetpawaMatch(models.Model):
    match_link = models.URLField(_("Match Link"), max_length=200, unique=True,null=False,blank=False)
    match_time = models.DateTimeField(_("Match Time"), blank=True, null=True)
    home_team = models.CharField(_("Home Team"), max_length=50)
    away_team = models.CharField(_("Away Team"), max_length=50)
    tournament = models.CharField(_("Tournament"), max_length=50)
    home_played = models.PositiveBigIntegerField(_("home_played"), default=0)
    away_played = models.PositiveBigIntegerField(_("away_played"), default=0)
    home_win_percentage = models.PositiveBigIntegerField(_("home_win_percentage"), default=0, null=True, blank=True)
    away_win_percentage = models.PositiveBigIntegerField(_("away_win_percentage"), default=0, null=True, blank=True)
    home_total_goals = models.PositiveBigIntegerField(_("home_total_goals"), default=0)
    away_total_goals = models.PositiveBigIntegerField(_("away_total_goals"), default=0)
    home_average_scored = models.DecimalField(_("Home Average Scored"), max_digits=5, decimal_places=2)
    away_average_scored = models.DecimalField(_("Away Average Scored"), max_digits=5, decimal_places=2)
    home_average_conceded = models.DecimalField(_("Home Average Conceded"), max_digits=5, decimal_places=2)
    away_average_conceded = models.DecimalField(_("Away Average Conceded"), max_digits=5, decimal_places=2)
    home_bts_percentage = models.PositiveBigIntegerField(_("home_bts_percentage"), default=0)
    away_bts_percentage = models.PositiveBigIntegerField(_("away_bts_percentage"), default=0)
    home_over_15 = models.PositiveBigIntegerField(_("home_over_15"), default=0)
    away_over_15 = models.PositiveBigIntegerField(_("away_over_15"), default=0)
    home_over_25 = models.PositiveBigIntegerField(_("home_over_25"), default=0)
    away_over_25 = models.PositiveBigIntegerField(_("away_over_25"), default=0)
    ht_home_over_05 = models.PositiveBigIntegerField(_("ht_home_over_05"), default=0)
    ht_away_over_05 = models.PositiveBigIntegerField(_("ht_away_over_05"), default=0)
    ht_home_over_15 = models.PositiveBigIntegerField(_("ht_home_over_15"), default=0)
    ht_away_over_15 = models.PositiveBigIntegerField(_("ht_away_over_15"), default=0)
    home_yellow_cards = models.PositiveBigIntegerField(_("home_yellow_card"), default=0, null=True, blank=True)
    away_yellow_cards = models.PositiveBigIntegerField(_("away_yellow_card"), default=0, null=True, blank=True)
    home_total_cards = models.PositiveBigIntegerField(_("home_total_cards"), default=0, null=True, blank=True)
    away_total_cards = models.PositiveBigIntegerField(_("away_total_cards"), default=0, null=True, blank=True)
    is_settled = models.BooleanField(_("Is Settled"), default=False)
    half_time_home_goals = models.PositiveBigIntegerField(_("half_time_home_goals"), null=True, blank=True)
    half_time_away_goals = models.PositiveBigIntegerField(_("half_time_away_goals"), null=True, blank=True)
    full_time_home_goals = models.PositiveBigIntegerField(_("full_time_home_goals"), null=True, blank=True)
    full_time_away_goals = models.PositiveBigIntegerField(_("full_time_away_goals"), null=True, blank=True)
    home_odds = models.DecimalField(_("Home Odds"), max_digits=5, decimal_places=2)
    draw_odds = models.DecimalField(_("Draw Odds"), max_digits=5, decimal_places=2)
    away_odds = models.DecimalField(_("Away Odds"), max_digits=5, decimal_places=2)
    Over25ft_odds = models.DecimalField(_("Over 2.5 goals Odds"), max_digits=5, decimal_places=2)
    unde25ft_odds = models.DecimalField(_("Under 2.5 goals Odds"), max_digits=5, decimal_places=2)
    dc1x_odds = models.DecimalField(_("1x Double Chance odds"), max_digits=5, decimal_places=2)
    dcx3_odds = models.DecimalField(_("x2 Double Chance odds"), max_digits=5, decimal_places=2)
    dc12_odds = models.DecimalField(_("12 Double Chance odds"), max_digits=5, decimal_places=2)
    

    class Meta:
        verbose_name = _("betpawamatch")
        verbose_name_plural = _("betpawamatches")

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.match_link}"

    # def get_absolute_url(self):
    #     return reverse("betpawamatch_detail", kwargs={"pk": self.pk})


class AccountBalance(models.Model):
    day = models.DateTimeField(_("day"), blank=True, null=True)
    amount = models.PositiveBigIntegerField(_("amount"), default=0)
       

    class Meta:
        verbose_name = _("accountbalance")
        verbose_name_plural = _("accountbalances")

    def __str__(self):
        return f"{self.day} - {self.amount}"

    # def get_absolute_url(self):
    #     return reverse("accountbalance_detail", kwargs={"pk": self.pk})
