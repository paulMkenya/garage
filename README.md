# Garage for ERPNext

A Frappe app that adds end-to-end garage / workshop management on top of ERPNext v16: gate check-in → job card → estimate and customer approval → invoice → quality check → gate pass → service history.

## Install

```bash
bench get-app https://github.com/paulMkenya/garage
bench --site <site> install-app garage
bench --site <site> migrate
```

Requires ERPNext v16. Nothing else needs installing. The installer adds:
- the Standard, Quick and Motorcycle check-in templates
- labour items in the `Garage Labour` item group
- the `Garage Parts` item group
- the Workshop Board
- `repair_order` links on Quotation and Sales Invoice
- Garage Settings defaults

No demo customers, parts or stock are created.

On a brand-new site, the labour items and item groups are added when you finish the ERPNext setup wizard.

After installing:
1. Set prices for the labour items, then add your parts to `Garage Parts`.
2. Open **Garage Settings** to adjust the check-in rules, the credit-release role and the Quality Check rule.
3. For SMS, enter your Uwazii API URL, username, password and sender ID in Garage Settings and tick **Enable SMS**. Sending is off until you do this.
4. In Docker setups, set `host_name` in the site config to a URL the backend can reach. Without it, images don't appear in PDFs, and SMS links point to the wrong address.

## What's included

- **Garage Vehicle**: customer cars, kept separate from ERPNext's fleet `Vehicle`.
  - Plates are normalised (`kda 123a` becomes `KDA123A`).
  - Service history, next service date and km.
- **Vehicle Check In** (submittable):
  - plate lookup and quick-add, with a warning if the car is already in the yard
  - who brought the car, their phone and ID
  - odometer, fuel level, warning lights, keys and documents
  - template checklist with a photo per item
  - **body damage map** (front, rear, left, right, top) with numbered marks
  - walk-around photos and belongings
  - concerns, spend limit, terms and signatures
  - a printed receipt
- **Repair Order** (job card):
  - concern → diagnosis → correction for each job
  - technician and bay, parts and labour, spend-limit warning
  - status flow with timestamps, and a **Workshop Board** (Kanban)
  - Estimate (Quotation), customer approval per item, and a Sales Invoice for the approved items only
- **Quality Check**: workshop checklist and road test. A car can only be marked Ready for Collection after a passed check. A failed check sends it back to In Progress.
- **Customer link** (`/car-status?key=…`): a page the customer opens without logging in to see progress and approve or decline the estimate. It is sent in the estimate and car-ready SMS.
- **Gate Pass**: the car is released only when the invoice is paid or a manager authorises credit. Needs exit odometer, exit photos, keys returned and the customer's signature. On release it updates the vehicle's service history.
- **Uwazii SMS**: car received, estimate ready, car ready, payment received, car released and service reminders (daily). Every message is logged in **Garage SMS Log**.
- **Reports**: Cars In Yard, Repair Turnaround, Technician Workload, Garage Revenue.
- **Print formats**: check-in receipt, job card, gate pass.
