from django.db import models
from djmoney.models.fields import MoneyField, CurrencyField
import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save


class Balance(models.Model):
    name = models.CharField(max_length=100)
    amount = MoneyField(
        max_digits=10, decimal_places=2, default_currency="ZAR", default=0
    )

    def __str__(self):
        return f"{self.name} - {self.amount}"


class Goal(models.Model):
    STATUS_CHOICES = (
        ("locked", "Locked"),
        ("unlocked", "Unlocked"),
        ("completed", "Completed"),
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    date_added = models.DateField(default=datetime.date.today)
    cost = MoneyField(
        max_digits=10, decimal_places=2, default_currency="ZAR", default=0
    )
    image = models.ImageField(upload_to="media/goal/", blank=True, null=True)
    url_link = models.URLField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="locked")
    account = models.ForeignKey(Balance, on_delete=models.CASCADE)
    date_completed = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.cost} - {self.status}"

    # formula to work out if goal is unlocked
    def is_unlocked(self):
        return self.account.amount >= self.cost

    def save(self, *args, **kwargs):
        if self.status == "completed":
            pass
        elif self.is_unlocked():
            self.status = "unlocked"
        super().save(*args, **kwargs)


class Deposit(models.Model):
    amount = MoneyField(
        max_digits=10, decimal_places=2, default_currency="ZAR", default=0
    )
    date_added = models.DateField(default=datetime.date.today)
    account = models.ForeignKey(Balance, on_delete=models.CASCADE)

    def __str__(self):
        return f"Amount added: {self.amount}. Balance: {self.account.amount}"


# Signals / Triggers / Logic

# Add deposit to balance
@receiver(post_save, sender=Deposit)
def debit_balance(sender, instance, **kwargs):
    balance = instance.account
    balance.amount += instance.amount
    balance.save()

        
# Credit balance when goal is completed
@receiver(post_save, sender=Goal)
def credit_balance(sender, instance, **kwargs):
    if instance.status == "completed":
        balance = instance.account
        balance.amount -= instance.cost
        balance.save()
