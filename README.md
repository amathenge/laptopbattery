Laptop Battery Script

The following scripts checks my laptop battery in Debian 11 and calculates the battery drain.

* [ ] cron job will populate a sqlite database with battery levels every 20 minutes.
* [ ] Script will check every hour and send a report via text message.

---

V 1.1 - 14NOV2022

Updated documentation

Updated time difference to give the number of minutes lost from the last time the battery was checked (the cron job is checking every 20 minutes)
