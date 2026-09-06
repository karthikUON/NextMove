# NextMove — project plan (checklist)

## Phase 0: Kickoff (Week 1)
- [ ] **Supriya:** form the team, assign roles, set up the task tracker (GitHub Projects)
- [ ] **Whole team:** initialize the shared GitHub repo — `backend/` (Django project), `templates/`, `static/`, `installation.sh`
- [ ] **Whole team:** meet to align on project scope before any code is written
- [ ] **Supriya:** schedule a recurring weekly check-in
- [ ] **Deliverable:** team formed, roles assigned, repo initialized

## Phase 1: Requirements Gathering (Week 2)
- [ ] **Supriya + whole team:** draft the feature list and user stories
- [ ] **Whole team:** review the feature list against the assignment brief
- [ ] **Deliverable:** agreed feature list to design against

## Phase 2: Design — EER & Storyboard (Week 3)
- [ ] **Jay:** draft the EER diagram — users, categories, listings, listing_images, conversations, messages, favorites, reports, ratings, moderation_keywords, listing_flags
- [ ] **Karthik + Chinna:** draft the storyboard/wireframes for all core pages
- [ ] **Whole team:** review and sign off on both before development starts
- [ ] **Deliverable:** finalized EER diagram and storyboard

## Phase 3: Dev Week 1 — Foundation: Skeleton, Custom User, Auth (Week 4)
- [ ] **Karthik + Chinna:** Django project skeleton — three apps (accounts, marketplace, messaging)
- [ ] **Jay:** custom User model (UoN email domain validation, is_verified flag) and the first migration — this must happen before any other migration
- [ ] **Karthik + Chinna:** signup, email-verification, login, and logout views + Bootstrap templates
- [ ] **Kirthan:** validate the full signup → verify → login flow end to end
- [ ] **Supriya:** run the weekly check-in, keep the tracker updated
- [ ] **Deliverable:** working signup/login gated on UoN email verification

## Phase 4: Dev Week 2 — Homepage & Browse (Week 5)
- [ ] **Jay:** Category and Listing models, registered in Django admin, seeded with sample data
- [ ] **Karthik:** homepage view + template — recent listings, category quick-links
- [ ] **Chinna:** browse/search view + template — category, price, keyword, "open to trade", and sort filters
- [ ] **Kirthan:** validate the homepage and browse filters render and filter correctly
- [ ] **Deliverable:** homepage and browse page working against real listings

## Phase 5: Dev Week 3 — Listing Detail & CRUD (Week 6)
- [ ] **Jay:** ListingImage model + migration
- [ ] **Karthik:** listing detail page — photo gallery, trade badge, owner vs. buyer actions
- [ ] **Chinna:** post/edit/delete/mark-sold views, multi-photo upload (local storage for now, not Azure), and the My Listings page
- [ ] **Kirthan:** validate CRUD, ownership checks (a user can't edit someone else's listing), and photo upload
- [ ] **Deliverable:** the full listing lifecycle working end to end, including photos

## Phase 6: Dev Week 4 — Moderation & Favorites (Week 7)
- [ ] **Jay:** ModerationKeyword, ListingFlag, and Favorite models
- [ ] **Karthik:** the auto-hold keyword scan, built into `Listing.save()`
- [ ] **Chinna:** favorites toggle + favorites page
- [ ] **Kirthan:** validate the auto-hold flow and the favorite toggle
- [ ] **Deliverable:** listings containing blocked keywords land in `on_hold` automatically; favorites work

## Phase 7: Dev Week 5 — Messaging (Week 8)
- [ ] **Jay:** Conversation and Message models
- [ ] **Karthik:** the find-or-create conversation logic + inbox view
- [ ] **Chinna:** the inbox template (conversation list + thread view) and read receipts
- [ ] **Kirthan:** validate two-way messaging and access control — a non-participant must be blocked from viewing a conversation
- [ ] **Deliverable:** a buyer and seller can message each other about a listing

## Phase 8: Dev Week 6 — Reports & Admin Dashboard (Week 9)
- [ ] **Jay:** Report model
- [ ] **Karthik:** report form, `file_report_view`, and admin bulk actions (approve/reject/mark reviewed)
- [ ] **Chinna:** the admin dashboard stats view + template
- [ ] **Kirthan:** validate the reporting flow and confirm the dashboard's figures match the database
- [ ] **Supriya:** confirm the admin scope matches the brief's "administrative section" requirement — check it off explicitly
- [ ] **Deliverable:** working reports queue and admin stats dashboard

## Phase 9: Dev Week 7 — MySQL Cutover & Full Regression (Week 10)
- [ ] **Jay:** `seed_data` management command, then the MySQL migration and cutover
- [ ] **Karthik + Chinna:** bug-fixing only, no new features
- [ ] **Kirthan:** a full end-to-end regression pass across every feature
- [ ] **Supriya:** compile the final report — process documentation (weeks, roles, decisions made and why); track bugs found → fixed → verified; freeze scope
- [ ] **Whole team:** rehearse the demo, and test `installation.sh` on a machine that isn't a dev's own laptop
- [ ] **Stretch, only if the above finishes early:** a "leave a rating" page for the existing Rating model (schema and admin browsing already exist, the buyer-facing form doesn't)
- [ ] **Deliverable:** a fully working app on real MySQL, regression-tested, ready for submission
