# NextMove — project plan (updated checklist)

Updated 11 November 2026. `[x]` = done, `[ ]` = still open. Every phase shows the planned week from the original plan, then what actually happened.
Roles: **Supriya** database · **Jay** project manager and tester · **Karthik** architect · **Chinna** senior developer · **Kirthan** junior developer, shadowing Karthik and Chinna.

## What changed from the original plan
- Roles were settled as above, so the model and database tasks moved to Supriya, and team coordination and weekly validation moved to Jay.
- The app has **four** apps (accounts, marketplace, messaging, reports), not three.
- Signup uses an **email OTP code** instead of a verification link. Forgot password, campus on every listing, live chat updates, scam alerts and a status dropdown were added.
- **Ratings were not built** (no model, table, form or admin page).
- Testing was **manual**: written test cases, weekly validation and user acceptance testing. There are no automated test scripts.
- Weeks 4 to 9 finished about **two to five weeks after plan**, so Week 10 is still open.

## Phase 0: Kickoff (Week 1, 17 to 21 Aug) — done on time
- [x] **Jay:** form the team, assign roles, set up the task tracker (GitHub issues)
- [x] **Whole team:** initialize the shared GitHub repo (Django project, templates, static files, `installation.sh`)
- [x] **Whole team:** meet to align on project scope before any code is written (everyone attended)
- [x] **Jay:** schedule a recurring weekly meeting (every Thursday, minutes in Appendix L)
- [x] **Deliverable:** team formed, roles assigned, repo initialized

## Phase 1: Requirements Gathering (Week 2, 24 to 28 Aug) — done on time
- [x] **Jay + Karthik + Chinna:** draft the feature list and user stories
- [x] **Whole team:** review the feature list against the assignment brief
- [x] **Deliverable:** agreed feature list to design against

## Phase 2: Design — EER & Storyboard (Week 3, 31 Aug to 4 Sep) — done on time
- [x] **Supriya:** draft the EER diagram — users, categories, listings, listing_images, conversations, messages, favorites, reports, ratings, moderation_keywords, listing_flags
- [x] **Karthik + Chinna:** draft the storyboard/wireframes for all core pages
- [x] **Whole team:** review and sign off on both before development starts (4 Sep)
- [x] **Deliverable:** finalized EER diagram and storyboard
- [x] *Later:* diagrams updated with the fields added during the build (campus, OTP fields); the ratings table stayed in the diagram but was never built

## Phase 3: Dev Week 1 — Foundation: Skeleton, Custom User, Auth (Week 4, planned 7 to 11 Sep) — finished 23 Sep
- [x] **Karthik + Chinna:** Django project skeleton — four apps (accounts, marketplace, messaging, reports) (skeleton merged 6 Sep, PR #1)
- [x] **Supriya:** custom User model (UoN email domain validation, is_verified flag) and the first migration, before any other migration
- [x] **Karthik + Chinna:** signup, email OTP verification, login and logout views + Bootstrap templates (merged 23 Sep, PR #3; the separate passwords branch, PR #2, was closed unmerged)
- [x] **Jay:** validate the full signup → verify → login flow end to end
- [x] **Kirthan:** shadow Karthik and Chinna during development
- [x] **Jay:** run the weekly meeting, keep the tracker and the Gantt chart updated
- [x] **Deliverable:** working signup/login gated on UoN email verification

## Phase 4: Dev Week 2 — Homepage & Browse (Week 5, planned 14 to 18 Sep) — finished 4 Oct
- [x] **Supriya:** Category and Listing models, registered in Django admin, seeded with sample data
- [x] **Karthik + Chinna:** homepage and browse/search views + templates — category, price, keyword, campus, "open to trade" and sort filters
- [x] **Jay:** validate the homepage and browse filters (4 Oct)
- [x] **Deliverable:** homepage and browse page working against real listings
- [x] *Note:* the campus change was merged 30 Sep (PR #4), reverted the same day (PR #5), and fixed 4 Oct (PR #6)

## Phase 5: Dev Week 3 — Listing Detail & CRUD (Week 6, planned 21 to 25 Sep) — finished 15 Oct
- [x] **Supriya:** ListingImage model + migration
- [x] **Karthik:** listing detail page — photo gallery, trade badge, owner vs. buyer actions
- [x] **Chinna:** post/edit/delete/mark-sold views, multi-photo upload (local storage), and the My Listings page
- [x] **Karthik:** forgot password by emailed code (added task, merged 14 Oct, PR #8)
- [x] **Jay:** validate CRUD, ownership checks (a user can't edit someone else's listing), and photo upload (merged 15 Oct, PR #9)
- [x] **Deliverable:** the full listing lifecycle working end to end, including photos

## Phase 6: Dev Week 4 — Moderation & Favorites (Week 7, planned 28 Sep to 2 Oct) — finished 5 Nov
- [x] **Supriya:** ModerationKeyword, ListingFlag, and Favorite models
- [x] **Chinna (reviewed by Karthik):** the auto-hold keyword scan, built into `Listing.save()`, and the favorites toggle + favorites page (PR #12, merged 5 Nov with the review fixes; Karthik's duplicate build was dropped)
- [x] **Jay:** validate the auto-hold flow and the favorite toggle
- [x] **Deliverable:** listings containing blocked keywords land in `on_hold` automatically; favorites work

## Phase 7: Dev Week 5 — Messaging (Week 8, planned 5 to 9 Oct) — finished 4 Nov
- [x] **Supriya:** Conversation and Message models
- [x] **Karthik:** the find-or-create conversation logic + inbox view
- [x] **Chinna:** the inbox template (conversation list + thread view) and read receipts
- [x] **Karthik:** live updates (the page checks for new messages every 3 seconds) and the unread badge
- [x] **Jay:** validate two-way messaging and access control — a non-participant is blocked from viewing a conversation (PRs #13 and #14, merged 4 Nov)
- [x] **Deliverable:** a buyer and seller can message each other about a listing

## Phase 8: Dev Week 6 — Reports & Admin Dashboard (Week 9, planned 12 to 16 Oct) — finished 5 Nov
- [x] **Supriya + Karthik:** Report model, report form and view
- [x] **Karthik:** admin bulk actions (approve / reject / mark reviewed)
- [x] **Chinna:** the admin dashboard stats view + template
- [x] **Karthik:** Message Scam Alert (added task: eight rule groups, only the receiver is warned, nothing stored)
- [x] **Jay:** validate the reporting flow and confirm the dashboard's figures match the database (PR #16 merged 5 Nov)
- [x] **Jay:** confirm the admin scope matches the brief's "administrative section" requirement (the Django admin with our own actions counts)
- [x] **Deliverable:** working reports queue and admin stats dashboard

## Phase 9: Dev Week 7 — MySQL Cutover & Full Regression (Week 10, planned 19 to 23 Oct) — still open
- [x] **Supriya:** `seed_data` management command, then the MySQL migration and cutover with Karthik (in place by mid-October, estimated)
- [ ] **Karthik + Chinna:** bug-fixing only, no new features (90% done on 10 Nov, forecast 12 Nov)
- [ ] **Jay:** a full end-to-end regression pass across every feature (50% done on 10 Nov, forecast 12 Nov)
- [ ] **Jay + Kirthan:** compile the test evidence, the defect list and the sign-off record (Appendix N)
- [ ] **Whole team:** finish the final report (the minutes, test evidence and individual reflections still have placeholders)
- [x] **Chinna:** test `installation.sh` on a machine that isn't a dev's own laptop
- [ ] **Whole team:** rehearse the demo (script written; two timed rehearsals still to do)
- [ ] **Stretch goal, not done:** a "leave a rating" page — the ratings table was never built, so it would need a model, form and admin view first
- [ ] **Deliverable:** a fully working app on real MySQL, regression-tested, ready for submission

## Added after the plan: Weeks 11 to 13 (to submission on 13 Nov)
- [x] **Jay, Kirthan, Karthik:** user acceptance testing with teammates; found a missing status dropdown, missing login/signup links and a scam alert whose yellow warning bar did not appear — all fixed
- [x] **Jay and Kirthan:** re-test the scam alerts after the fix (all cases pass)
- [ ] **Karthik / Jay:** open GitHub issues: #19 (yellow bar when a listing is moved to active), #20 (update the readme), #10 (login and signup), #11 (test)
- [ ] **Whole team:** submit the report, the presentation and the code on Canvas by 11.59pm, Friday 13 November
