# EviTrack – API CONTRACT (human summary; the OpenAPI schema is the machine source)

Base: `/api/v1`. Session cookie + CSRF (`X-CSRFToken`). JSON unless noted. Errors use the shape in `BACKEND.md` §3. Pagination `{count,next,previous,results}` (page size 20, `?page=`). "Scope" = server filters to what the user may see.
Permissions: **A** Admin · **M** Case Manager · **I** Investigator/Advocate · **C** Custodian · **R** Reviewer · **Any** any approved signed-in user.
If the real implementation differs, update this file in the same commit.
Machine source: `docs/openapi.yaml`, generated with `python manage.py export_openapi` from `/api/v1/` routes only (the same routes `/api/schema/` serves). Regenerate and commit it after every v1 change.

## S0 – Foundations
| Method | Path | Notes |
|---|---|---|
| GET | `/health/` | `{status:"ok"}` (public) |
| GET | `/auth/csrf/` | Sets `csrftoken` cookie (public) |
| GET | `/api/schema/` | OpenAPI (DEBUG/admin) |

## S1 – Landing
No API. Static content. (Optional later: public `GET /public/stats/`, not required.)

## S2 – Authentication and registration
| Method | Path | Body → Response | Perm |
|---|---|---|---|
| POST | `/auth/register/` | `{name,email,phone?,requested_role,password,password2}` → 201 `{status:"pending_approval"}` | public |
| POST | `/auth/login/` | `{email,password,remember_me?}` → `{status:"otp_required",otp:{sent_to_masked,expires_in,resend_in}}` · errors: `account_pending`, `account_locked`(+`retry_after`), `validation_error`(+`attempts_left`) | public, throttled |
| POST | `/auth/otp/verify/` | `{code}` → `{status:"authenticated"\|"totp_required"}` · errors `otp_invalid`(+`attempts_left`), `otp_locked`(+`retry_after`) | pending-auth |
| POST | `/auth/otp/resend/` | → `{resend_in}` · 429 during cooldown | pending-auth |
| POST | `/auth/totp/verify/` | `{code}` → `{status:"authenticated"}` | pending-auth |
| GET | `/auth/me/` | → `User` (below) or 401 | Any |
| POST | `/auth/logout/` | → 204 | Any |
| POST | `/auth/session/ping/` | → `{expires_in}` | Any |

`User` = `{id,name,email,phone,role,permissions:string[],preferences:{theme,email_enabled,sms_enabled,reminder_hearing:int[],reminder_deadline:int[]},totp_enabled,last_login,unread_notifications,pending_custody,pending_approvals:int|null}`. `pending_approvals` is `null` for non-admins. OTP and TOTP steps use the pending-auth session cookie; all POST requests require CSRF.

## S3 – App shell
| Method | Path | Notes | Perm |
|---|---|---|---|
| PATCH | `/me/preferences/` | `{theme?}` (and later notification prefs) | Any |
| GET | `/notifications/unread-count/` | `{unread, pending_custody, pending_approvals?}` | Any |
| GET | `/notifications/?limit=5` | latest items for the bell | Any |
| GET | `/search/suggest/?q=` | grouped top results: cases, parties, evidence (max 5 each) | Any, scope |

## S4 – Dashboard
| Method | Path | Response | Perm |
|---|---|---|---|
| GET | `/dashboard/summary/` | `{kpis:{open_cases,hearings_this_week,overdue_tasks,pending_transfers,integrity_alerts},upcoming_hearings:[…5],attention:{transfers:[…],overdue_tasks:[…],integrity_alerts:[…]},awaiting_approval?}` | Any, scope |
| GET | `/dashboard/charts/` | `{cases_by_status,cases_by_type,hearings_per_week,workload_per_user?,uploads_over_time}` (workload for A/M only) | Any, scope |

## S5 – Cases
| Method | Path | Notes | Perm |
|---|---|---|---|
| GET | `/cases/` | filters `status,priority,case_type,assignee,search`; `ordering`; each item: `{id,case_no,title,case_type,status,priority,assignees[],next_hearing,updated_at}` | Any, scope |
| POST | `/cases/` | create | A,M |
| GET | `/cases/{id}/` | detail incl. `stats{evidence,hearings,tasks,modified_evidence}`, `allowed_transitions[]`, `can{edit,assign,close}` | scope |
| PATCH | `/cases/{id}/` | edit | A,M,I(if assigned) |
| POST | `/cases/{id}/transition/` | `{to_status,reason?}` | A,M |
| POST | `/cases/{id}/close/` | `{reason}` | A,M |
| GET/POST | `/cases/{id}/assignments/` | list / add `{user,role_on_case}` | read: scope · write: A,M |
| DELETE | `/cases/{id}/assignments/{aid}/` | | A,M |
| GET/POST | `/cases/{id}/parties/` | | read scope · write A,M,I |
| PATCH/DELETE | `/cases/{id}/parties/{pid}/` | | A,M,I |
| GET | `/cases/{id}/timeline/?type=&page=` | merged events `{type,title,actor,at,link}` | scope |
| GET | `/cases/{id}/audit/` | | A,M |
| GET | `/users/lookup/?q=&case=` | for assignee/receiver pickers `{id,name,role}` | Any, scope |

## S6 – Evidence
| Method | Path | Notes | Perm |
|---|---|---|---|
| GET | `/evidence/` | filters `case,tags,file_type,integrity,holder,search` | scope |
| POST | `/evidence/` | multipart upload (see BACKEND §5) → `{id,evidence_no,sha256,version,…}` | A,M,I,C |
| GET | `/evidence/{id}/` | metadata, `integrity:{state,last_checked,by}`, `holder`, `version`, `can{…}` | scope |
| PATCH | `/evidence/{id}/` | title, description, tags | A,M,I,C |
| GET | `/evidence/{id}/versions/` | | scope |
| GET | `/evidence/{id}/integrity-checks/` | `{checked_on,checked_by,result,computed_hash,stored_hash}` | scope |
| POST | `/evidence/{id}/verify/` | → `{result:"verified"\|"modified",check:{…}}` | A,M,I,C |
| GET | `/evidence/{id}/preview/` · `/download/` | streamed file, audited | scope |
| POST | `/cases/{id}/verify-all/` | → 202 `{task_id,status_url}` | A,M,I,C |
| GET | `/tasks/{task_id}/` | `{state,progress,result}` | owner |
| POST | `/evidence/{id}/acknowledge-alert/` | marks integrity alert acknowledged | A,M |
| GET | `/tags/?q=` | tag suggestions | Any |

## S7 – Custody
| Method | Path | Notes | Perm |
|---|---|---|---|
| GET | `/evidence/{id}/custody/` | timeline events `{id,from,to,status,reason,requested_at,resolved_at}` | scope |
| POST | `/evidence/{id}/custody/request/` | `{receiver,reason,note?}` | holder |
| GET | `/custody/inbox/?direction=incoming\|outgoing` | | Any, scope |
| POST | `/custody/{event_id}/accept/` | | receiver |
| POST | `/custody/{event_id}/reject/` | `{reason}` | receiver |
| POST | `/custody/{event_id}/cancel/` | | requester |
| GET | `/evidence/{id}/label/` | `{evidence_no,case_no,hash_prefix,holder,intake_date,qr_png_base64 or url}`; plus `/label.pdf` | scope |

## S8 – Hearings, tasks, calendar
| Method | Path | Notes | Perm |
|---|---|---|---|
| GET | `/calendar/events/?start=&end=&types=&case=` | FullCalendar-ready events `{id,title,start,end,type,case,overdue}` | scope |
| GET/POST | `/hearings/` | filter `case`, `from`, `to` | read scope · write A,M,I |
| GET/PATCH | `/hearings/{id}/` | incl. `reminders[]` | |
| PATCH | `/hearings/{id}/reschedule/` | `{start}` (drag) | A,M,I |
| POST | `/hearings/{id}/outcome/` | `{outcome,notes,next_hearing_date?}` → `{created_next_suggestion}` | A,M,I |
| GET/POST | `/tasks/` | filter `mine,overdue,case,status` | read scope · write A,M,I |
| PATCH/DELETE | `/tasks/{id}/` | status toggle, edit | A,M,I (assignee may toggle) |

## S9 – Notifications and preferences
| Method | Path | Notes |
|---|---|---|
| GET | `/notifications/?type=&unread=&page=` | list |
| POST | `/notifications/{id}/read/` · `/notifications/read-all/` | |
| GET/PATCH | `/me/preferences/` | channels, reminder timing, phone |
| POST | `/me/preferences/test-notification/` | creates a test in-app notice |

## S10 – Reports and search
| Method | Path | Notes | Perm |
|---|---|---|---|
| GET | `/reports/cases/{id}/{kind}/` | `kind` ∈ `summary,evidence-register,custody-history,hearing-schedule,integrity` → PDF (or 202 task) | scope |
| GET | `/reports/recent/` | `{user,kind,case,at}` from audit | A,M |
| GET | `/search/?q=&group=&page=` | full results, grouped with counts, highlight snippets, `matched_by_hash` flag | scope |

## S11 – Admin and account
| Method | Path | Notes | Perm |
|---|---|---|---|
| GET | `/admin/approvals/` · POST `/admin/approvals/{id}/approve/` `{role}` · POST `…/reject/` `{reason}` | | A |
| GET | `/admin/users/?role=&status=&search=` · PATCH `/admin/users/{id}/` `{role?,is_active?}` · POST `…/unlock/` · POST `…/reset-otp/` | | A |
| GET | `/admin/audit/?user=&action=&case=&from=&to=&search=` · GET `/admin/audit/export.csv` | M sees own cases | A,M |
| POST | `/admin/audit/verify-chain/` | `{ok,entries_checked,first_broken?}` | A |
| GET | `/admin/failed-logins/` · POST `…/{id}/unlock/` · GET `…/stats/` | | A |
| GET | `/admin/security/` | read-mostly settings and health | A |
| POST | `/admin/security/integrity-sweep/` | → 202 task | A |
| GET/PATCH | `/me/` | profile (name, phone) | Any |
| POST | `/auth/password/change/` | `{current,new,new2}` | Any |
| POST/DELETE | `/auth/totp/` | enable → `{qr,secret}` then confirm `{code}`; disable | Any |
| GET | `/me/activity/` | my last 10 audit entries | Any |

## S12 – Hardening and cutover
No new endpoints. Adds: CSP/throttle verification, schema freeze check, SPA catch-all, removal of legacy routes.

## Shared shapes (summary)
`UserRef {id,name,role,initials}` · `CaseRef {id,case_no,title}` · `Pill {value,label}` · `EvidenceCard {id,evidence_no,title,case:CaseRef,file_type,size,tags[],sha256_short,integrity:{state,checked_at},holder:UserRef,version,thumbnail_url?}` · `Notification {id,type,message,link,is_read,created_at}`.

## Requests to backend
Frontend (Agent B) adds requests here. Agent A handles them in its next batch and marks them done with the commit.
- (none yet)
