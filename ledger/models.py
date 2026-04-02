from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from auditlog.registry import auditlog


class Account(models.Model):
    """Chart of Accounts"""

    ACCOUNT_TYPES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    ]

    code = models.CharField(max_length=20, unique=True,
                            help_text="Account code (e.g., 1010, 5010)")
    name = models.CharField(max_length=200, help_text="Account name")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent account for hierarchical chart of accounts"
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = "Account"
        verbose_name_plural = "Chart of Accounts"

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxType(models.Model):
    """Tax types for VAT and Withholding Tax"""

    code = models.CharField(max_length=20, unique=True,
                            help_text="Tax code (e.g., IVAT, OVAT, EWT2)")
    name = models.CharField(
        max_length=100, help_text="Tax name (e.g., Input VAT, Output VAT, EWT 2%)")
    description = models.TextField(blank=True)
    default_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Default tax rate as percentage (e.g., 12.00 for 12%)"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = "Tax Type"
        verbose_name_plural = "Tax Types"

    def __str__(self):
        return f"{self.code} - {self.name} ({self.default_rate}%)"


class JournalHeader(models.Model):
    """Journal Entry Header (Transaction)"""

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('VOID', 'Void'),
    ]

    journal_number = models.CharField(
        max_length=50, unique=True, help_text="Journal entry number")
    transaction_date = models.DateField(help_text="Transaction date")
    reference = models.CharField(
        max_length=100, blank=True, help_text="External reference (invoice, check number, etc.)")
    description = models.TextField(help_text="Journal entry description")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='DRAFT')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='journals_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-transaction_date', '-journal_number']
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"

    def __str__(self):
        return f"{self.journal_number} - {self.transaction_date} - {self.description[:50]}"

    def total_debits(self):
        """Calculate total debits for this journal"""
        return self.lines.aggregate(total=models.Sum('debit_amount'))['total'] or Decimal('0.00')

    def total_credits(self):
        """Calculate total credits for this journal"""
        return self.lines.aggregate(total=models.Sum('credit_amount'))['total'] or Decimal('0.00')

    def is_balanced(self):
        """Check if debits equal credits"""
        return self.total_debits() == self.total_credits()


class JournalLine(models.Model):
    """Journal Entry Lines (Debits and Credits)"""

    journal = models.ForeignKey(
        JournalHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent journal entry"
    )
    line_number = models.IntegerField(help_text="Line sequence number")
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='journal_lines',
        help_text="Account to debit or credit"
    )

    description = models.CharField(
        max_length=200, blank=True, help_text="Line-level description")

    debit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Debit amount (leave 0 if credit)"
    )
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Credit amount (leave 0 if debit)"
    )

    # VAT and Withholding Tax fields
    tax_type = models.ForeignKey(
        TaxType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_lines',
        help_text="Type of tax (VAT, withholding, etc.)"
    )
    tax_base_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,          # allow NULL in DB
        blank=True,         # allow empty in forms
        default=None,       # no forced 0.00
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Amount subject to tax"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Tax rate applied (percentage)"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Computed tax amount"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ['journal', 'line_number']
        unique_together = ['journal', 'line_number']
        verbose_name = "Journal Line"
        verbose_name_plural = "Journal Lines"

    def __str__(self):
        return f"{self.journal.journal_number} - Line {self.line_number} - {self.account.code}"

    def clean(self):
        """Validate that either debit or credit is non-zero, but not both"""
        from django.core.exceptions import ValidationError
        # if self.debit_amount > 0 and self.credit_amount > 0:
        # raise ValidationError("A line cannot have both debit and credit amounts.")
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValidationError(
                "A line must have either a debit or credit amount.")


auditlog.register(Account)
auditlog.register(JournalHeader)
auditlog.register(JournalLine)
