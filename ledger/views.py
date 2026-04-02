from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required


# Import all models we need
from .models import Account, JournalHeader, JournalLine, TaxType

# Import all forms we need
from .forms import (
    AccountForm, 
    AccountSearchForm, 
    JournalHeaderForm, 
    JournalLineFormSet, 
    JournalSearchForm,
    ReportFilterForm,
    TaxReportFilterForm
)
@login_required
# ==================== DASHBOARD ====================
def dashboard(request):
    """Homepage dashboard"""
    # Calculate totals from posted journals only
    posted_journals = JournalHeader.objects.filter(status='POSTED')
    total_debits = JournalLine.objects.filter(
        journal__status='POSTED'
    ).aggregate(Sum('debit_amount'))['debit_amount__sum'] or 0
    
    total_credits = JournalLine.objects.filter(
        journal__status='POSTED'
    ).aggregate(Sum('credit_amount'))['credit_amount__sum'] or 0
    
    context = {
        'total_accounts': Account.objects.filter(is_active=True).count(),
        'total_journals': JournalHeader.objects.count(),
        'posted_journals': posted_journals.count(),
        'draft_journals': JournalHeader.objects.filter(status='DRAFT').count(),
        'total_debits': total_debits,
        'total_credits': total_credits,
    }
    return render(request, 'ledger/dashboard.html', context)

@login_required
# ==================== CHART OF ACCOUNTS ====================
def accounts_list(request):
    """List all accounts with search and filter"""
    accounts = Account.objects.all().order_by('code')
    
    # Initialize search form
    search_form = AccountSearchForm(request.GET)
    
    # Apply filters
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        account_type = search_form.cleaned_data.get('account_type')
        status = search_form.cleaned_data.get('status')
        
        # Search by code or name
        if search_query:
            accounts = accounts.filter(
                Q(code__icontains=search_query) | 
                Q(name__icontains=search_query)
            )
        
        # Filter by account type
        if account_type:
            accounts = accounts.filter(account_type=account_type)
        
        # Filter by status
        if status == 'active':
            accounts = accounts.filter(is_active=True)
        elif status == 'inactive':
            accounts = accounts.filter(is_active=False)
    
    context = {
        'accounts': accounts,
        'search_form': search_form,
        'total_count': accounts.count(),
    }
    return render(request, 'ledger/accounts_list.html', context)

@login_required
def account_add(request):
    """Add new account"""
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save()
            messages.success(request, f'Account {account.code} - {account.name} created successfully!')
            return redirect('accounts_list')
    else:
        form = AccountForm()
    
    context = {
        'form': form,
        'title': 'Add New Account',
        'button_text': 'Create Account',
    }
    return render(request, 'ledger/account_form.html', context)

@login_required
def account_edit(request, pk):
    """Edit existing account"""
    account = get_object_or_404(Account, pk=pk)
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            account = form.save()
            messages.success(request, f'Account {account.code} - {account.name} updated successfully!')
            return redirect('accounts_list')
    else:
        form = AccountForm(instance=account)
    
    context = {
        'form': form,
        'account': account,
        'title': f'Edit Account: {account.code}',
        'button_text': 'Save Changes',
    }
    return render(request, 'ledger/account_form.html', context)

@login_required
def account_delete(request, pk):
    """Deactivate account (soft delete)"""
    account = get_object_or_404(Account, pk=pk)
    
    if request.method == 'POST':
        account.is_active = False
        account.save()
        messages.warning(request, f'Account {account.code} - {account.name} deactivated.')
        return redirect('accounts_list')
    
    context = {
        'account': account,
    }
    return render(request, 'ledger/account_confirm_delete.html', context)

@login_required
# ==================== JOURNAL ENTRIES ====================
def journals_list(request):
    """List all journal entries with search and filter"""
    journals = JournalHeader.objects.all().order_by('-transaction_date', '-journal_number')
    
    # Initialize search form
    search_form = JournalSearchForm(request.GET)
    
    # Apply filters
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        # Search by journal number, reference, or description
        if search_query:
            journals = journals.filter(
                Q(journal_number__icontains=search_query) | 
                Q(reference__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by status
        if status:
            journals = journals.filter(status=status)
        
        # Filter by date range
        if date_from:
            journals = journals.filter(transaction_date__gte=date_from)
        if date_to:
            journals = journals.filter(transaction_date__lte=date_to)
    
    context = {
        'journals': journals,
        'search_form': search_form,
        'total_count': journals.count(),
    }
    return render(request, 'ledger/journals_list.html', context)

@login_required
def journal_detail(request, pk):
    """View journal entry details"""
    journal = get_object_or_404(JournalHeader, pk=pk)
    lines = journal.lines.all().order_by('line_number')
    
    context = {
        'journal': journal,
        'lines': lines,
    }
    return render(request, 'ledger/journal_detail.html', context)

@login_required
@transaction.atomic
def journal_add(request):
    """Add new journal entry"""
    if request.method == 'POST':
        form = JournalHeaderForm(request.POST)
        formset = JournalLineFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Create header
            journal = form.save(commit=False)
            
            # Auto-generate journal number if blank
            if not journal.journal_number:
                last_journal = JournalHeader.objects.order_by('-id').first()
                if last_journal and last_journal.journal_number:
                    # Extract number from format JV-00001
                    try:
                        last_num = int(last_journal.journal_number.split('-')[-1])
                    except (ValueError, IndexError):
                        last_num = 0
                    journal.journal_number = f'JV-{last_num + 1:05d}'
                else:
                    journal.journal_number = 'JV-00001'
            
            # Set created_by if user is authenticated
            if request.user.is_authenticated:
                journal.created_by = request.user
            
            journal.save()
            
            # Create lines
            formset.instance = journal
            lines = formset.save()
            
            # Validate double-entry
            if not journal.is_balanced():
                messages.error(request, f'Journal is not balanced! Debits: ₱{journal.total_debits()}, Credits: ₱{journal.total_credits()}')
                journal.delete()
                return redirect('journal_add')
            
            messages.success(request, f'Journal {journal.journal_number} created successfully!')
            return redirect('journal_detail', pk=journal.pk)
    else:
        form = JournalHeaderForm(initial={'transaction_date': timezone.now().date()})
        formset = JournalLineFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Journal Entry',
    }
    return render(request, 'ledger/journal_form.html', context)

@login_required
@transaction.atomic
def journal_edit(request, pk):
    """Edit draft journal entry"""
    journal = get_object_or_404(JournalHeader, pk=pk)
    
    # Only drafts can be edited
    if journal.status != 'DRAFT':
        messages.error(request, 'Only draft journals can be edited.')
        return redirect('journal_detail', pk=pk)
    
    if request.method == 'POST':
        form = JournalHeaderForm(request.POST, instance=journal)
        formset = JournalLineFormSet(request.POST, instance=journal)
        
        if form.is_valid() and formset.is_valid():
            journal = form.save()
            formset.save()
            
            # Validate balance
            if not journal.is_balanced():
                messages.error(request, f'Journal is not balanced! Debits: ₱{journal.total_debits()}, Credits: ₱{journal.total_credits()}')
                return redirect('journal_edit', pk=pk)
            
            messages.success(request, f'Journal {journal.journal_number} updated successfully!')
            return redirect('journal_detail', pk=journal.pk)
    else:
        form = JournalHeaderForm(instance=journal)
        formset = JournalLineFormSet(instance=journal)
    
    context = {
        'form': form,
        'formset': formset,
        'journal': journal,
        'title': f'Edit Journal: {journal.journal_number}',
    }
    return render(request, 'ledger/journal_form.html', context)

@login_required
def journal_post(request, pk):
    """Post a draft journal (finalize it)"""
    journal = get_object_or_404(JournalHeader, pk=pk)
    
    if journal.status != 'DRAFT':
        messages.error(request, 'Only draft journals can be posted.')
        return redirect('journal_detail', pk=pk)
    
    if not journal.is_balanced():
        messages.error(request, 'Cannot post unbalanced journal!')
        return redirect('journal_detail', pk=pk)
    
    if request.method == 'POST':
        journal.status = 'POSTED'
        journal.posted_at = timezone.now()
        journal.save()
        messages.success(request, f'Journal {journal.journal_number} posted successfully!')
        return redirect('journal_detail', pk=pk)
    
    context = {
        'journal': journal,
    }
    return render(request, 'ledger/journal_confirm_post.html', context)

@login_required
def journal_void(request, pk):
    """Void a posted journal"""
    journal = get_object_or_404(JournalHeader, pk=pk)
    
    if journal.status != 'POSTED':
        messages.error(request, 'Only posted journals can be voided.')
        return redirect('journal_detail', pk=pk)
    
    if request.method == 'POST':
        journal.status = 'VOID'
        journal.save()
        messages.warning(request, f'Journal {journal.journal_number} voided.')
        return redirect('journal_detail', pk=pk)
    
    context = {
        'journal': journal,
    }
    return render(request, 'ledger/journal_confirm_void.html', context)

@login_required
# ==================== FINANCIAL REPORTS ====================
def report_trial_balance(request):
    """Trial Balance Report"""
    from django.db.models import Sum, Q
    from decimal import Decimal
    
    # Get filter form
    filter_form = ReportFilterForm(request.GET)
    
    date_from = None
    date_to = None
    
    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
    
    # Base query: only posted journals
    lines = JournalLine.objects.filter(journal__status='POSTED')
    
    # Apply date filters
    if date_from:
        lines = lines.filter(journal__transaction_date__gte=date_from)
    if date_to:
        lines = lines.filter(journal__transaction_date__lte=date_to)
    
    # Calculate balances per account
    accounts_data = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')
    
    for account in Account.objects.filter(is_active=True).order_by('code'):
        account_lines = lines.filter(account=account)
        
        debits = account_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')
        credits = account_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')
        
        if debits > 0 or credits > 0:
            accounts_data.append({
                'account': account,
                'debits': debits,
                'credits': credits,
            })
            total_debits += debits
            total_credits += credits
    
    is_balanced = abs(total_debits - total_credits) < Decimal('0.01')
    
    context = {
        'filter_form': filter_form,
        'accounts_data': accounts_data,
        'total_debits': total_debits,
        'total_credits': total_credits,
        'is_balanced': is_balanced,
        'date_from': date_from,
        'date_to': date_to,
        'report_title': 'Trial Balance',
    }
    return render(request, 'ledger/report_trial_balance.html', context)

@login_required
def report_income_statement(request):
    """Income Statement (Profit & Loss)"""
    from django.db.models import Sum
    from decimal import Decimal
    
    # Get filter form
    filter_form = ReportFilterForm(request.GET)
    
    date_from = None
    date_to = None
    
    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
    
    # Base query: only posted journals
    lines = JournalLine.objects.filter(journal__status='POSTED')
    
    # Apply date filters
    if date_from:
        lines = lines.filter(journal__transaction_date__gte=date_from)
    if date_to:
        lines = lines.filter(journal__transaction_date__lte=date_to)
    
    # Revenue accounts (credits - debits for revenue = net revenue)
    revenue_accounts = Account.objects.filter(account_type='REVENUE', is_active=True).order_by('code')
    revenue_data = []
    total_revenue = Decimal('0.00')
    
    for account in revenue_accounts:
        account_lines = lines.filter(account=account)
        credits = account_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')
        debits = account_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')
        net = credits - debits
        
        if net != 0:
            revenue_data.append({
                'account': account,
                'amount': net,
            })
            total_revenue += net
    
    # Expense accounts (debits - credits for expense = net expense)
    expense_accounts = Account.objects.filter(account_type='EXPENSE', is_active=True).order_by('code')
    expense_data = []
    total_expenses = Decimal('0.00')
    
    for account in expense_accounts:
        account_lines = lines.filter(account=account)
        debits = account_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')
        credits = account_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')
        net = debits - credits
        
        if net != 0:
            expense_data.append({
                'account': account,
                'amount': net,
            })
            total_expenses += net
    
    net_income = total_revenue - total_expenses
    
    context = {
        'filter_form': filter_form,
        'revenue_data': revenue_data,
        'expense_data': expense_data,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'date_from': date_from,
        'date_to': date_to,
        'report_title': 'Income Statement',
    }
    return render(request, 'ledger/report_income_statement.html', context)

@login_required
def report_balance_sheet(request):
    """Balance Sheet Report"""
    from django.db.models import Sum
    from decimal import Decimal
    
    # Get filter form
    filter_form = ReportFilterForm(request.GET)
    
    date_to = None
    
    if filter_form.is_valid():
        date_to = filter_form.cleaned_data.get('date_to')
    
    # Base query: only posted journals up to date_to
    lines = JournalLine.objects.filter(journal__status='POSTED')
    
    if date_to:
        lines = lines.filter(journal__transaction_date__lte=date_to)
    
    # Assets (debits - credits = asset balance)
    asset_accounts = Account.objects.filter(account_type='ASSET', is_active=True).order_by('code')
    asset_data = []
    total_assets = Decimal('0.00')
    
    for account in asset_accounts:
        account_lines = lines.filter(account=account)
        debits = account_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')
        credits = account_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')
        balance = debits - credits
        
        if balance != 0:
            asset_data.append({
                'account': account,
                'balance': balance,
            })
            total_assets += balance
    
    # Liabilities (credits - debits = liability balance)
    liability_accounts = Account.objects.filter(account_type='LIABILITY', is_active=True).order_by('code')
    liability_data = []
    total_liabilities = Decimal('0.00')
    
    for account in liability_accounts:
        account_lines = lines.filter(account=account)
        credits = account_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')
        debits = account_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')
        balance = credits - debits
        
        if balance != 0:
            liability_data.append({
                'account': account,
                'balance': balance,
            })
            total_liabilities += balance
    
    # Equity (credits - debits = equity balance)
    equity_accounts = Account.objects.filter(account_type='EQUITY', is_active=True).order_by('code')
    equity_data = []
    total_equity = Decimal('0.00')
    
    for account in equity_accounts:
        account_lines = lines.filter(account=account)
        credits = account_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')
        debits = account_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')
        balance = credits - debits
        
        if balance != 0:
            equity_data.append({
                'account': account,
                'balance': balance,
            })
            total_equity += balance
    
    # Calculate retained earnings (net income from P&L)
    revenue_lines = lines.filter(account__account_type='REVENUE')
    expense_lines = lines.filter(account__account_type='EXPENSE')
    
    total_revenue = (revenue_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')) - \
                   (revenue_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00'))
    
    total_expenses = (expense_lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')) - \
                    (expense_lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00'))
    
    retained_earnings = total_revenue - total_expenses
    total_equity += retained_earnings
    
    total_liabilities_equity = total_liabilities + total_equity
    is_balanced = abs(total_assets - total_liabilities_equity) < Decimal('0.01')
    
    context = {
        'filter_form': filter_form,
        'asset_data': asset_data,
        'liability_data': liability_data,
        'equity_data': equity_data,
        'retained_earnings': retained_earnings,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
        'total_liabilities_equity': total_liabilities_equity,
        'is_balanced': is_balanced,
        'date_to': date_to,
        'report_title': 'Balance Sheet',
    }
    return render(request, 'ledger/report_balance_sheet.html', context)

@login_required
def report_general_ledger(request):
    """General Ledger Report by Account"""
    from django.db.models import Sum
    from decimal import Decimal
    
    # Get filter form
    filter_form = ReportFilterForm(request.GET)
    
    date_from = None
    date_to = None
    selected_account = None
    
    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        selected_account = filter_form.cleaned_data.get('account')
    
    ledger_data = []
    
    if selected_account:
        # Base query: only posted journals
        lines = JournalLine.objects.filter(
            journal__status='POSTED',
            account=selected_account
        ).select_related('journal').order_by('journal__transaction_date', 'journal__journal_number', 'line_number')
        
        # Apply date filters
        if date_from:
            lines = lines.filter(journal__transaction_date__gte=date_from)
        if date_to:
            lines = lines.filter(journal__transaction_date__lte=date_to)
        
        # Calculate running balance
        running_balance = Decimal('0.00')
        
        for line in lines:
            # For assets and expenses: debits increase, credits decrease
            # For liabilities, equity, revenue: credits increase, debits decrease
            if selected_account.account_type in ['ASSET', 'EXPENSE']:
                running_balance += line.debit_amount - line.credit_amount
            else:
                running_balance += line.credit_amount - line.debit_amount
            
            ledger_data.append({
                'date': line.journal.transaction_date,
                'journal': line.journal.journal_number,
                'description': line.description or line.journal.description,
                'debit': line.debit_amount,
                'credit': line.credit_amount,
                'balance': running_balance,
            })
    
    context = {
        'filter_form': filter_form,
        'selected_account': selected_account,
        'ledger_data': ledger_data,
        'date_from': date_from,
        'date_to': date_to,
        'report_title': 'General Ledger',
    }
    return render(request, 'ledger/report_general_ledger.html', context)

@login_required
def report_chart_of_accounts(request):
    """Chart of Accounts Report with Balances"""
    from django.db.models import Sum
    from decimal import Decimal
    
    # Get all active accounts
    accounts = Account.objects.filter(is_active=True).order_by('account_type', 'code')
    
    # Calculate balances
    accounts_with_balances = []
    
    for account in accounts:
        lines = JournalLine.objects.filter(
            journal__status='POSTED',
            account=account
        )
        
        debits = lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0.00')
        credits = lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0.00')
        
        # Calculate balance based on account type
        if account.account_type in ['ASSET', 'EXPENSE']:
            balance = debits - credits
        else:
            balance = credits - debits
        
        accounts_with_balances.append({
            'account': account,
            'debits': debits,
            'credits': credits,
            'balance': balance,
        })
    
    context = {
        'accounts_with_balances': accounts_with_balances,
        'report_title': 'Chart of Accounts',
    }
    return render(request, 'ledger/report_chart_of_accounts.html', context)
# --- TAX DASHBOARD & REPORTS ---

@login_required
def taxes_dashboard(request):
    """Main tax reports hub."""
    return render(request, "ledger/taxes_dashboard.html")


def report_vat_summary(request):
    """VAT summary (BIR 2550Q)."""
    form = TaxReportFilterForm(request.GET or None)

    date_from = date_to = None
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

    context = {
        "filter_form": form,
        "date_from": date_from,
        "date_to": date_to,
        # placeholder values for now
        "gross_sales": 0,
        "zero_rated_sales": 0,
        "vat_exempt_sales": 0,
        "output_vat": 0,
        "vat_purchases": 0,
        "input_vat": 0,
        "vat_payable": 0,
    }
    return render(request, "ledger/report_vat_summary.html", context)

@login_required
def report_income_tax(request):
    """Income tax summary (BIR 1702)."""
    form = TaxReportFilterForm(request.GET or None)

    date_from = date_to = None
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

    # placeholder numbers; we’ll wire real computations later
    revenue = 0
    expenses = 0
    taxable_income = revenue - expenses
    tax_8_percent = taxable_income * 0.08 if taxable_income > 0 else 0

    context = {
        "filter_form": form,
        "date_from": date_from,
        "date_to": date_to,
        "revenue": revenue,
        "expenses": expenses,
        "taxable_income": taxable_income,
        "tax_8_percent": tax_8_percent,
    }
    return render(request, "ledger/report_income_tax.html", context)

@login_required
def report_withholding_tax(request):
    """Withholding tax report (EWT and Final WHT)."""
    form = TaxReportFilterForm(request.GET or None)

    date_from = date_to = None
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

    context = {
        "filter_form": form,
        "date_from": date_from,
        "date_to": date_to,
        # placeholder totals
        "ewt_total": 0,
        "final_wht_total": 0,
    }
    return render(request, "ledger/report_withholding_tax.html", context)

@login_required
def report_tax_liabilities(request):
    """Tax liabilities tracker."""
    form = TaxReportFilterForm(request.GET or None)

    date_from = date_to = None
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

    context = {
        "filter_form": form,
        "date_from": date_from,
        "date_to": date_to,
        # empty for now – we’ll compute from accounts later
        "liabilities": [],
        "total_liabilities": 0,
    }
    return render(request, "ledger/report_tax_liabilities.html", context)
