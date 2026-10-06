# Garage for ERPNext

A Frappe app that adds end-to-end garage / workshop management on top of ERPNext v16.

## Phase 1: Gate Check-In (this release)

- **Garage Vehicle**: customer cars, kept separate from ERPNext's fleet `Vehicle`. Plates are normalised to capitals without spaces (`kda 123a` becomes `KDA123A`). Records VIN, engine, fuel, transmission, body type and odometer history.
- **Vehicle Check In** (submittable, `VCI-YYYY-#####`):
  - plate lookup, quick-create of a new vehicle, and a warning if the car is already in the yard
  - who brought the car (owner or someone else), phone, ID and preferred contact
  - odometer, fuel gauge buttons, dashboard photo, whether the engine starts, and whether the car was driven in or towed
  - warning lights (check engine, oil, battery, temperature, brake, ABS, airbag, TPMS, service, traction, other)
  - keys, remote, spare key, wheel-lock key, logbook, insurance and inspection stickers, service book
  - checklist loaded from a template, with OK / Attention / Damaged / Missing / N/A, notes and a photo per item, plus "Mark all unanswered as OK"
  - **body damage map**: front, rear, left, right and top views of a car. Tap to drop a numbered mark with type, severity, notes and photo. Marks are colour-coded by severity.
  - walk-around photos (front, rear, left, right, interior, boot, engine, plate/VIN) plus any extra photos
  - belongings left in the car, or the customer's "no valuables" confirmation
  - service type, insurance claim details, promised time, approved spend limit, what to do with old parts, and customer concerns
  - terms, customer and staff signatures
  - checks on submit that photos, warning lights, checklist, damage, belongings, concerns and signature are all filled in (configurable in **Garage Settings**)
- **Vehicle Check In Template**: Standard (64 checks, including NTSA triangles and fire extinguisher), Quick and Motorcycle templates are installed.
- **Vehicle Check In Receipt**: print format / PDF with the damage map, the checklist exceptions, photos and signatures.

Planned next: Repair Order / job card, estimate approval, workshop board, QC, invoice and M-Pesa, gate pass, Uwazii SMS.

## Install

```bash
bench get-app https://github.com/paulMkenya/garage
bench --site <site> install-app garage
```

Requires ERPNext v16. For PDF printing of images in Docker setups, set `host_name` in the site config to a URL the backend can reach.

## Licence

MIT
