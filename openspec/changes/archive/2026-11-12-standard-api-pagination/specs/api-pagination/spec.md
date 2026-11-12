# Spec Delta: api-pagination

## Purpose

Provides a standardized, consistent pagination envelope structure with metadata and HATEOAS navigation links across all collection endpoints.

## ADDED Requirements

### Requirement: Standard Paginated Response Envelope

The system SHALL return all collection endpoints wrapped in a standardized envelope containing the items array under "data", metadata under "pagination", and navigation URLs under "links".

#### Scenario: Retrieve first page of populated collection

- **GIVEN** 25 active vendor contracts exist in the database
- **WHEN** a client requests contracts with page 1 and perPage 10
- **THEN** the response status is 200 OK
- **AND** "data" contains 10 items
- **AND** "pagination" contains page=1, perPage=10, totalItems=25, and totalPages=3
- **AND** "links" contains self, first, last, next, and null prev

#### Scenario: Retrieve empty collection

- **GIVEN** no records match the requested filter criteria
- **WHEN** a client requests a paginated collection
- **THEN** "data" is an empty list
- **AND** "pagination" contains totalItems=0, totalPages=0, page=1, and perPage=20
- **AND** "links" next and prev are null

### Requirement: Pagination Query Parameter Controls

The system SHALL accept "page" and "perPage" query parameters, defaulting to page 1 and perPage 20, enforcing minimum value 1 and maximum perPage 100.

#### Scenario: Default pagination parameters applied

- **WHEN** a client queries a collection without specifying page or perPage
- **THEN** the system applies page=1 and perPage=20 to the query execution

#### Scenario: Reject non-positive page parameter

- **WHEN** a client provides page=0 or negative page
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Reject perPage exceeding maximum limit

- **WHEN** a client provides perPage=101 or greater
- **THEN** the system returns HTTP 422 Unprocessable Entity

### Requirement: HATEOAS Navigation Links Generation

The system SHALL dynamically construct "self", "first", "last", "next", and "prev" navigation URLs preserving any active filter parameters.

#### Scenario: Intermediate page produces both next and prev links

- **GIVEN** a collection with 50 items and perPage 10
- **WHEN** a client requests page 3
- **THEN** "links.prev" points to page=2
- **AND** "links.next" points to page=4
- **AND** "links.first" points to page=1
- **AND** "links.last" points to page=5

#### Scenario: Last page sets next link to null

- **GIVEN** a collection with 25 items and perPage 10 (totalPages=3)
- **WHEN** a client requests page 3
- **THEN** "links.next" is null
- **AND** "links.prev" points to page=2

#### Scenario: Preserve query filters across generated links

- **GIVEN** a collection queried with filter "?period=2026-03&state=APPROVED&page=1&perPage=10"
- **WHEN** the system generates pagination links
- **THEN** each generated URL retains "period=2026-03" and "state=APPROVED"
