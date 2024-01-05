from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

# Create your models here.
class Startegy(models.Model):
    Startegy = models.CharField(_("Startegy"), max_length=50)
    notes = models.TextField(_("Strategy Notes"), blank=True, null=True)
    

    class Meta:
        verbose_name = _("startegy")
        verbose_name_plural = _("startegies")

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse("startegy_detail", kwargs={"pk": self.pk})

class Betslip(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Won'),
        (-1, 'Lost'),
        (2, 'Cancelled'),
    ]


    betslipUser = models.ForeignKey(User, verbose_name=_("bettor"), on_delete=models.CASCADE)
    strategy = models.ForeignKey(Startegy, verbose_name=_("Strategy"), on_delete=models.CASCADE)
    betslip_link = models.URLField(_("Betslip Link"), max_length=200)
    betslip_text = models.TextField(_("Bet Text")) 
    stake = models.PositiveIntegerField(_("Stake"))
    odd = models.PositiveIntegerField(_("Odd"))
    bonus = models.DecimalField(_("Bonus Percentage"), max_digits=5, decimal_places=2)
    payout = models.PositiveIntegerField(_("Payout"),)
    status = models.IntegerField(choices=STATUS_CHOICES,default=0,)
    amount = models.FloatField(_("Amount Won/Lost"))


    class Meta:
        verbose_name = _("Betslp")
        verbose_name_plural = _("Betslps")

    def __str__(self):
        return self.betslip_link

    # def get_absolute_url(self):
    #     return reverse("Betslp_detail", kwargs={"pk": self.pk})

