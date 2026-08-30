# NextMove — project plan (step-by-step)

## Phase 0: Kickoff (Week 1)
1. Supriya: write the requirements doc / project charter, get team sign-off
2. Supriya: set up the task tracker (GitHub Projects)
3. Whole team: initialize the shared GitHub repo — `backend/`, `frontend/`, `database/`, `installation.sh`
4. Whole team: meet to align on the DB schema and API contract before any code is written
5. Supriya: schedule a recurring weekly check-in

## Phase 1: Design & Architecture (Week 1–2)
1. Jay: wireframe all core pages — home/browse, listing detail, post-listing form, login/signup, user dashboard, admin dashboard, admin listing moderation
2. Jay + whole team: finalize the MySQL schema and write `schema.sql` — users, listings, categories, listing images, conversations, messages, reports/flags, favorites, ratings, **moderation_keywords**
3. Include the trade fields (`is_tradeable`, `trade_notes`) and moderation fields (`auto_flagged`, `flagged_reason`, `on_hold` status) in the schema from the start, not bolted on later
4. Set up the Vue project skeleton — routes, layout, Pinia store for auth token + user state
5. Set up the Azure Blob Storage container for listing images
6. Supriya: turn the wireframes + schema into the Sprint 1 / Sprint 2 backlog

**Deliverable:** wireframes, finalized `schema.sql`, empty-but-running Vue + FastAPI apps, `installation.sh` works end to end

## Phase 2: Core Build — Sprint 1 (Week 3–4)
1. Chinna: build signup/login endpoints — JWT issuing, UoN email domain check, password hashing
2. Chinna: build listing CRUD endpoints (create/read/update/delete/mark-sold), including the trade toggle fields and the auto-hold keyword scan on creation
3. Karthik: build login/signup pages
4. Karthik: build the post-a-listing form — image upload to Blob, trade toggle + notes field
5. Karthik: build the listing detail page and "my listings" page
6. Jay: style pages as they're built, establish the shared design system (colors, buttons, cards)
7. Kirthan: write test cases per user story before each feature is finished, not after
8. Supriya: run the weekly check-in, chase blockers, keep the tracker updated

**Deliverable:** working signup/login; users can post/edit/delete a listing with a photo, optionally marked as tradeable; listings containing blocked keywords land in `on_hold` automatically

## Phase 3: Core Build — Sprint 2 (Week 5–6)
1. Karthik: build search/filter endpoints — category, price range, keyword, "open to trade"
2. Karthik: build the categories table + endpoints
3. Karthik: build in-app messaging endpoints — find-or-create conversation, send/poll messages, mark as read
4. Chinna: build the browse/search page with filters (including "open to trade")
5. Chinna: build category navigation
6. Chinna: build the messaging UI — inbox list + conversation thread view
7. Chinna: build favorites/watchlist
8. Jay: polish browse/search UX — the page students will use most
9. Kirthan: execute test cases against Sprint 1 features while Sprint 2 is being built
10. Supriya: run the first informal demo to the whole team

**Deliverable:** full buyer/seller loop works — browse, find, message, arrange a sale or a trade

## Phase 4: Admin Panel (Week 7)
1. Karthik: build admin-only endpoints — list/disable users, moderate any listing, view the reports queue, approve/reject `on_hold` listings
2. Karthik: build the admin dashboard stats endpoint — users (total/active/banned), listings (total/active/sold/on-hold/removed), pending reports vs pending auto-flags
3. Chinna: build admin Vue views under `/admin/*`, gated by role
4. Chinna: build the dashboard stats view, user management view, listing moderation view (with a separate on-hold queue), and reports/flags queue
5. Kirthan: test that non-admin users cannot hit any admin endpoint — this is the #1 thing markers check
6. Supriya: confirm admin scope matches the brief's "administrative section" requirement, check it off explicitly

**Deliverable:** working admin panel — dashboard stats, user management, listing moderation (including on-hold approvals), reports queue

## Phase 5: Stretch Features (Week 8, only if on schedule)
1. Supriya: triage which stretch features are realistic given time left
2. Pick from: ratings/reviews, saved searches, map view for accommodation
3. Whole team: don't start a stretch feature that can't be finished — better to polish the MVP than half-build extras

## Phase 6: Testing & Hardening (Week 9)
1. Kirthan: full regression pass across all features
2. Kirthan: security checks — auth bypass attempts, IDOR on listings/conversations, file upload validation on the Blob endpoint, non-admin access to admin routes
3. Chinna/Karthik: bug fixing only, no new features
4. Supriya: track bugs found → fixed → verified in the tracker, freeze scope

## Phase 7: Deployment & Report (Week 10)
1. Supriya: compile the final report — process documentation (sprints, roles, decisions made and why)
2. Jay: final screenshots / demo video
3. Whole team: rehearse the demo
4. Whole team: test `installation.sh` on a clean machine that isn't a dev's own laptop
