from django.contrib import admin
from .models import Account, TaxType, JournalHeader, JournalLine


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'is_active']
    list_filter = ['account_type', 'is_active']
    search_fields = ['code', 'name']


@admin.register(TaxType)
class TaxTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'default_rate', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(JournalHeader)
class JournalHeaderAdmin(admin.ModelAdmin):
    list_display = ['journal_number', 'transaction_date', 'description', 'status', 'created_by']
    list_filter = ['status', 'transaction_date']
    search_fields = ['journal_number', 'description', 'reference']
    date_hierarchy = 'transaction_date'


@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = ['journal', 'line_number', 'account', 'debit_amount', 'credit_amount', 'tax_type']
    list_filter = ['tax_type']
    search_fields = ['journal__journal_number', 'account__code', 'account__name']
