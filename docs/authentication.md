# Authentication and session handling

The member setup flow submits credentials directly to the NowFit origin. Credentials and response
HTML are never logged or exposed as entity attributes or diagnostics.

By default the password is not persisted. Session cookies are stored per config entry in Home
Assistant's private storage. Cookie export accepts only the exact NowFit domain and drops expired
records during restore. Selecting **store password** enables bounded automatic re-login; at most two
attempts are allowed per rolling 30-minute window and concurrent failures share one attempt.

When no stored password is available, or credentials are rejected, Home Assistant requests native
reauthentication. Changing an email address safely depends on a live-verified stable provider
identity and is therefore not claimed by this release candidate.
