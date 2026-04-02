# **ACCOUNTING LEDGER SYSTEM**

An **Accounting Ledger System** is a web-based application designed to efficiently record, organize, and manage financial transactions while generating accurate financial and tax reports. This system serves as a centralized platform for tracking income, expenses, assets, liabilities, and equity in a structured and auditable manner.

Built using the **Django Framework**, the system leverages a robust Model-View-Template (MVT) architecture to ensure scalability, maintainability, and security. It integrates backend logic with a dynamic user interface, enabling users to perform accounting operations with precision and ease.

---

## **Core Features**

- **Transaction Management**
  - Record debit and credit entries
  - Categorize transactions by account type
  - Maintain chronological financial records

- **General Ledger**
  - Automatically post transactions into ledger accounts
  - Track balances in real-time
  - Ensure double-entry accounting consistency

- **Financial Reporting**
  - Generate key financial statements:
    - Income Statement
    - Balance Sheet
    - Cash Flow Reports
  - Export reports for audit and tax compliance

- **User Authentication**
  - Secure login and session handling
  - Role-based access control (admin/user)

- **Database Integration**
  - Persistent storage using Django ORM
  - Efficient querying and data integrity enforcement

---

## **System Architecture**

- **Framework:** Django (Python)
- **Architecture Pattern:** MVT (Model-View-Template)
- **Database:** SQLite / PostgreSQL (configurable)
- **Backend Logic:** Python
- **Frontend:** HTML, CSS, Django Templates

---

## **Installation & Setup**

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd accounting-ledger-system
```

### **2. Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Apply Database Migrations**
```bash
python manage.py migrate
```

### **5. Create Superuser (Admin Access)**
```bash
python manage.py createsuperuser
```

### **6. Run the Development Server**
```bash
python manage.py runserver
```
