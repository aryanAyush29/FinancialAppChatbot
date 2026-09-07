# Payments and Money Transfers

How money moves between accounts, focusing on India's electronic payment systems, with brief
notes on international equivalents.

## India's electronic payment systems

### NEFT (National Electronic Funds Transfer)
- Transfers funds from one bank account to another across India.
- Runs 24x7x365, settled in half-hourly batches (not strictly instant).
- No RBI-set minimum or maximum amount (banks may set their own limits).
- Requires the beneficiary's name, account number, and **IFSC**.
- The RBI does not permit banks to charge savings-account customers for online NEFT.

### RTGS (Real Time Gross Settlement)
- For **high-value** transfers; minimum ₹2,00,000, no upper limit.
- Settles transactions individually and continuously in real time (not batched).
- Available 24x7.
- Also needs account number and IFSC.

### IMPS (Immediate Payment Service)
- Instant, 24x7 interbank transfer, typically up to ₹5,00,000 per transaction.
- Can be initiated with account number + IFSC, or with **MMID + mobile number**.
- Operated by NPCI (National Payments Corporation of India).

### UPI (Unified Payments Interface)
- Real-time system that links one or more bank accounts to a mobile app.
- Send/receive money using a **VPA / UPI ID** (`name@bank`), a mobile number, an account+IFSC,
  or a **QR code** — without sharing bank account details.
- Per-transaction limit is commonly ₹1,00,000 (higher for certain categories such as
  hospitals, education, and capital markets; some person-to-merchant caps differ).
- **UPI PIN** (set with debit-card details) authorises every payment.
- Features: UPI Lite (small-value payments without PIN from an on-device wallet),
  UPI AutoPay (recurring mandates), UPI Circle (delegated payments), and credit-line/RuPay
  credit card on UPI.
- UPI is free for normal person-to-person and most person-to-merchant payments; an
  interchange fee applies only to certain merchant transactions via prepaid wallets and is
  not charged to the customer.

### Cheques and the clearing system
- A cheque is a written order to pay. It is now cleared electronically through **CTS**
  (Cheque Truncation System) using a scanned image, usually within about one working day.
- A **bounced cheque** (insufficient funds, signature mismatch, post-dated, etc.) attracts
  charges and, for insufficiency of funds, can have legal consequences under Section 138 of
  the Negotiable Instruments Act.
- **Positive Pay System:** for high-value cheques, the issuer confirms cheque details to the
  bank in advance to reduce fraud.

### Cards
- **Debit card:** draws directly from your bank account. Spending is limited to your
  balance.
- **Credit card:** the bank pays the merchant and bills you later; see the
  cards-and-credit-score topic.
- **Prepaid card / wallet:** loaded with money in advance.
- Card payments use networks such as RuPay, Visa, and Mastercard. **Tokenisation** replaces
  the real card number with a device-specific token so merchants never store the actual
  number.
- **Contactless / NFC** payments up to a small limit (₹5,000 in India) may not need a PIN.

### Other India rails
- **AePS (Aadhaar-enabled Payment System):** withdraw cash or check balance using Aadhaar
  number + fingerprint at a business correspondent, useful in rural areas.
- **NACH (National Automated Clearing House):** bulk recurring debits/credits — salaries,
  dividends, SIPs, loan EMIs, utility bills.
- **Bharat Bill Payment System (BBPS):** a single interface for paying many types of bills.
- **NETC FASTag:** RFID-based toll payment linked to a prepaid or bank account.

## Choosing a method (educational framing)

| Need | Common choice |
|---|---|
| Small everyday payment, person or shop | UPI |
| Send a large sum (e.g. property payment) | RTGS |
| Instant transfer, moderate amount, any time | IMPS or UPI |
| Scheduled, non-urgent transfer | NEFT |
| Recurring fixed debits (EMI, SIP) | NACH mandate or UPI AutoPay |
| Paying a merchant online without sharing card data | UPI or a tokenised card |

## International transfers (brief)

- **SWIFT** network moves cross-border payments between banks; transfers usually take
  1–4 working days and involve fees from the sending bank, correspondent banks, and the
  receiving bank, plus a currency-conversion margin.
- **IBAN** (International Bank Account Number) and **BIC/SWIFT code** identify the
  destination bank and account in many countries.
- Other systems: SEPA (euro area), ACH and FedNow / RTP (United States), Faster Payments
  (United Kingdom).
- Remittance services and fintechs may offer faster or cheaper transfers by netting flows
  rather than moving money across borders each time.

## Safety when transferring money

- Double-check the beneficiary account number and IFSC; most transfers cannot be reversed
  once processed.
- Send a ₹1 test transfer to a new payee before a large one.
- Never share your UPI PIN, card PIN, CVV, OTP, or net-banking password. Banks never ask for
  these. You do **not** need to enter a PIN to *receive* money.
- Be wary of "collect requests" on UPI apps that ask you to approve a payment you did not
  initiate.
- Use official apps, keep the phone locked, and enable transaction alerts.

---

### Sources consulted
- Reserve Bank of India — FAQs on NEFT, RTGS, and card transactions; payment systems
  circulars (rbi.org.in)
- National Payments Corporation of India — product pages for UPI, IMPS, NACH, AePS, BBPS,
  FASTag (npci.org.in)
- U.S. Federal Reserve — FedNow and ACH overviews (federalreserve.gov)
