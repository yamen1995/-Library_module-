# Library Management - Odoo 18 Module

A simple, functional Library Management system built as a custom Odoo 18 Community Edition module.

## Features

- **Book Management**
  - Title, Author, Genre, ISBN with validation
  - Availability tracking
  - Recommended books based on genre
- **Borrowing System**
  - Borrow/Return workflow with states: `draft`, `confirmed`, `returned`, `overdue`
  - Late return triggers automatic invoice generation (if applicable)
- **Quick Actions**
  - Mark as Returned button (List & Form views)
  - Quick Borrow button on book list (pre-fills borrow form)
  - View Recommendations button
- **Author & Genre Management**
- **User Interface Enhancements**
  - List decorations based on state/availability
  - Custom CSS for professional appearance
- **Demo Data Included**

## Installation

1. Place the module in your `custom-addons` directory.
2. Ensure `contacts` and `account` modules are installed.
3. Update the module list via Apps (Developer Mode may be required).
4. Install the module "Library Management".

## Module Structure

```
library_management/
├── __manifest__.py
├── models/
├── views/
├── security/
├── data/       # Contains demo CSV files
└── static/
```

## Demo Data

The `data/` directory contains optional CSV files to populate:

- Authors
- Genres
- Books

## Development Notes

- Implements proper ORM relationships with `Many2one` and `Many2many` fields.
- Late fee logic creates invoices using the `account.move` model.
- UI polished with list decorations and CSS.
- Follows best practices for model constraints and batch `create` methods.

## License

LGPL-3

## Author

Developed by Yamen Tah - 2025

