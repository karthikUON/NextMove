# NextMove
UON Market Place

User ratings, 

Phase 1: Design & Architecture
Designer: Home Page/browse, listing detail, post listing form login/signup, user dashboard, admin dashboard, admin listing moderation.
finalize MySQL schema (users, listings, categories, images, messages, reports/flags), write schema.sql
set up Vue project skeleton (routes, basic layout, Vuex/Pinia if you want state management), set up Azure Blob container (State Managerment is something like sharing the data between different components, like Pinia Store stores all the tokens like stuff and will be shared among them)
turn StoryBoard (Ask Geoff suggested) + schema into a prioritized sprint plan — literally "Sprint 1 = auth + listing CRUD", "Sprint 2 = browse/search + messaging", etc.

Core Build — Sprint 1 (Week 3–4)
Auth + listings CRUD — the foundation everything else sits on.
Chinna : signup/login endpoints, JWT issuing, UoN email domain check, password hashing; listing CRUD endpoints (create/read/update/delete/mark-sold)
Karthik : login/signup pages, "post a listing" form (with image upload to Blob), listing detail page, "my listings" page.
Jay : move from wireframes to actual CSS/styling as pages get built; build out the design system (colors, buttons, cards) so Karthik isn't guessing
Kirthan: write test cases now, not later — for each user story, define pass/fail criteria before the feature is even done, so testing isn't a mad scramble in week 9
Supriya : run the weekly check-in, chase blockers, update the tracker
Deliverable: working signup/login + users can post/edit/delete a listing with a photo


Phase 3: Core Build — Sprint 2 (Week 5–6)
Browse, search, categories, messaging.
Karthik : search/filter endpoints (category, price range, keyword), categories table + endpoints, in-app messaging endpoints (buyer→seller)
CHinna: browse/search page with filters, category navigation, messaging UI (inbox + conversation view), favorites/watchlist
Jay : polish browse/search UX — this is the page students will use most, worth extra attention
Kirthan: start executing test cases against Sprint 1 features while Sprint 2 is being built (don't wait until everything's "done")
Supriya: first informal demo to the team — everyone sees the app for the first time as a real user would
Deliverable: full buyer/seller loop works — browse, find, message, arrange


Phase 4: Admin Panel (Week 7)
Karthik : admin-only endpoints (list all users, disable user, delete/moderate any listing, view reports queue) — protect with a role check, not just JWT presence
Chinna: admin Vue views (separate route group, e.g. /admin/*, gated by role)
Kirthan: specifically test that non-admin users cannot hit admin endpoints (this is the #1 thing markers/security-minded testers check)
Supriya: confirm admin scope matches the brief's "must have an administrative section" requirement — check it off explicitly
Deliverable: working admin panel — user management, listing moderation, reports queue

Phase 5: Stretch Features (Week 8, only if on schedule)
Pick from: ratings/reviews, report/flag flow, saved searches, map view for accommodation. Supriya's job here is triage — don't let the team start a stretch feature that can't be finished; better to polish MVP than half-build extras.

Phase 6: Testing & Hardening (Week 9)
Kirthan: full regression pass, plus the security checks you flagged earlier — auth bypass attempts, file upload validation on the Blob upload endpoint
Chinna/Karthik: bug fixing only, no new features
Supriya: track bugs found  -  fixed  - verified in the tracker, freeze scope

Phase 7: Deployment & Report (Week 10)
Supriya: compile the final report — this usually needs process documentation (sprints, roles, decisions made and why), not just the finished app
Jay: final screenshots/demo video if required
Whole team: rehearse the demo, make sure installation.sh genuinely works on a clean machine (test this on a laptop that isn't a dev's own — this catches a shocking number of last-minute failures)