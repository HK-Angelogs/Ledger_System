from django import forms
from django.forms import inlineformset_factory
from .models import Account, JournalHeader, JournalLine
from datetime import datetime  # ← Make sure this line exists


class AccountForm(forms.ModelForm):
    """Form for creating and editing accounts"""
    
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'parent', 'is_active', 'description']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1010, 5010',
                'maxlength': '20'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Cash in Bank, Office Supplies Expense'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description or notes'
            }),
        }
        labels = {
            'code': 'Account Code',
            'name': 'Account Name',
            'account_type': 'Account Type',
            'parent': 'Parent Account (optional)',
            'is_active': 'Active',
            'description': 'Description',
        }
        help_texts = {
            'code': 'Unique account code (e.g., 1010 for Cash)',
            'parent': 'Leave blank for main accounts, select parent for sub-accounts',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter parent dropdown to exclude self and only show active accounts
        if self.instance.pk:
            self.fields['parent'].queryset = Account.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['parent'].queryset = Account.objects.filter(is_active=True)
        
        # Make parent optional
        self.fields['parent'].required = False
        self.fields['description'].required = False


class AccountSearchForm(forms.Form):
    """Form for searching and filtering accounts"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by code or name...'
        })
    )
    
    account_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + Account.ACCOUNT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Accounts'),
            ('active', 'Active Only'),
            ('inactive', 'Inactive Only'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
from .models import JournalHeader, JournalLine, TaxType
from django.forms import inlineformset_factory


class JournalHeaderForm(forms.ModelForm):
    """Form for journal entry header"""
    
    class Meta:
        model = JournalHeader
        fields = ['journal_number', 'transaction_date', 'reference', 'description']
        widgets = {
            'journal_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated if left blank'
            }),
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Invoice #, Check #, PO #'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of this transaction'
            }),
        }
        labels = {
            'journal_number': 'Journal Number',
            'transaction_date': 'Transaction Date',
            'reference': 'Reference',
            'description': 'Description',
        }


class JournalLineForm(forms.ModelForm):
    """Form for journal entry lines"""
    
    class Meta:
        model = JournalLine
        fields = ['line_number', 'account', 'description', 'debit_amount', 'credit_amount', 
                  'tax_type', 'tax_base_amount', 'tax_rate', 'tax_amount']
        widgets = {
            'line_number': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': 1
            }),
            'account': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Line description (optional)'
            }),
            'debit_amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'tax_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'tax_base_amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active accounts
        self.fields['account'].queryset = Account.objects.filter(is_active=True).order_by('code')
        # Only show active tax types
        self.fields['tax_type'].queryset = TaxType.objects.filter(is_active=True).order_by('code')
        self.fields['tax_type'].required = False
        self.fields['tax_base_amount'].required = False
        self.fields['tax_rate'].required = False
        self.fields['tax_amount'].required = False


# Formset for multiple journal lines
JournalLineFormSet = inlineformset_factory(
    JournalHeader,
    JournalLine,
    form=JournalLineForm,
    extra=3,  # Start with 3 blank lines
    can_delete=True,
    min_num=2,  # Minimum 2 lines for double-entry
    validate_min=True,
)


class JournalSearchForm(forms.Form):
    """Form for searching journals"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by journal #, reference, or description...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')] + JournalHeader.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
class ReportFilterForm(forms.Form):
    """Form for filtering financial reports by date range"""
    
    date_from = forms.DateField(
        required=False,
        label='From Date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='To Date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    account = forms.ModelChoiceField(
        required=False,
        queryset=Account.objects.filter(is_active=True).order_by('code'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Account (for General Ledger)',
        empty_label='Select Account'
    )
class TaxReportFilterForm(forms.Form):
    """Filter form for tax reports with quarters and year selection"""
    
    QUARTER_CHOICES = [
        ('', 'All Quarters'),
        ('Q1', '1st Quarter (Jan-Mar)'),
        ('Q2', '2nd Quarter (Apr-Jun)'),
        ('Q3', '3rd Quarter (Jul-Sep)'),
        ('Q4', '4th Quarter (Oct-Dec)'),
    ]
    
    # Generate year choices (current year ± 5 years)
    current_year = datetime.now().year
    YEAR_CHOICES = [('', 'All Years')] + [(str(year), str(year)) for year in range(current_year - 5, current_year + 2)]
    
    quarter = forms.ChoiceField(
        choices=QUARTER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
