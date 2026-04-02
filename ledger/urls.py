from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Chart of Accounts
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/add/', views.account_add, name='account_add'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),

    # Journal Entries
    path('journals/', views.journals_list, name='journals_list'),
    path('journals/add/', views.journal_add, name='journal_add'),
    path('journals/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journals/<int:pk>/edit/', views.journal_edit, name='journal_edit'),
    path('journals/<int:pk>/post/', views.journal_post, name='journal_post'),
    path('journals/<int:pk>/void/', views.journal_void, name='journal_void'),

    # Financial Reports
    path('reports/trial-balance/', views.report_trial_balance,
         name='report_trial_balance'),
    path('reports/income-statement/', views.report_income_statement,
         name='report_income_statement'),
    path('reports/balance-sheet/', views.report_balance_sheet,
         name='report_balance_sheet'),
    path('reports/general-ledger/', views.report_general_ledger,
         name='report_general_ledger'),
    path('reports/chart-of-accounts/', views.report_chart_of_accounts,
         name='report_chart_of_accounts'),

    # Placeholder for future phases
    # Tax Reports (BIR Compliance)
    path('taxes/', views.taxes_dashboard, name='taxes_dashboard'),
    path('taxes/vat-summary/', views.report_vat_summary, name='report_vat_summary'),
    path('taxes/income-tax/', views.report_income_tax, name='report_income_tax'),
    path('taxes/withholding/', views.report_withholding_tax,
         name='report_withholding_tax'),
    path('taxes/liabilities/', views.report_tax_liabilities,
         name='report_tax_liabilities'),
]
