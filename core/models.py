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

    link_url = models.URLField(_("link"), max_length=200)
    league = models.CharField(_("league"), max_length=50)
    country = models.CharField(_("Country"), max_length=50)
    Level = models.CharField(_("Level"), max_length=50)
    order = models.FloatField(_("order"), default=2.0)

    class Meta:
        ordering = ['order']
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
