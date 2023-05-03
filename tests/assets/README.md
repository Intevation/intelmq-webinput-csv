# Test assets

- `webinput-session.conf`: Refers to `webinput-session.sqlite` for the session
- `webinput-session.sqlite`: Contains a user `test` with password `test`.
  Created with:
  ```bash
  sqlite3 tests/assets/webinput-session.sqlite < config/backend/session.sql
  WEBINPUT_CSV_CONFIG=config/backend/webinput_csv.conf WEBINPUT_CSV_SESSION_CONFIG=tests/assets/webinput-session.conf ./webinput-adduser --user test --password test
  ```
