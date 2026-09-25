# Protocol observations

Observed without authentication on 2026-09-25:

- Base origin: `https://nowfit.memberarea.club`
- Occupancy: `/CheckinCounter/GetClubsCheckinCounterPage`
- Login page and form action: `/Account/Login`
- Login method: `POST`, URL-encoded form
- Visible controls: `Email`, `Password`, `RememberMe`
- Hidden anti-forgery field: discovered dynamically and relayed without logging

The implementation does not hard-code the anti-forgery value and rejects multiple password forms,
non-POST forms, unexpected actions, HTTP actions and cross-origin actions.

Not yet live-verified: a successful member login, the authenticated account and history markup,
the provider's stable account identifier, cookie rotation/lifetime, and session-expiry response.
Synthetic fixtures exercise the intended parser contracts but are not proof of the live provider
contract.
