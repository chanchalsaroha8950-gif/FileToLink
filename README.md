# FileToLink Telegram Bot (Dual Bot Setup)

Simple aur production-ready Telegram file lock/share bot.

Is project me 2 bots ka use hota hai:
- `BOT_TOKEN` (Primary bot): Admin upload karta hai, share link generate hota hai.
- `BOT_TOKEN1` (Secondary bot): User link open karke file download karta hai.

## Features

- Single command startup: `python main.py`
- Dual bot architecture (primary + secondary)
- Admin-only upload
- Share link generation with copy button
- Non-expiring links support (`NEVER_EXPIRE_LINKS=1`)
- Channel lock before file access (secondary bot)
- Join request support: agar user ne request bhej di hai to access allow ho sakta hai
- Auto delete delivered file message after 15 minutes (secondary bot)
- SQLite + Supabase backend support

## Project Structure

- `main.py`: Dono bots ko ek command me start karta hai
- `bot.py`: Legacy secondary launcher (ab optional)
- `config.py`: Env + `channels.txt` parsing
- `channels.txt`: Required channels config (numbered format)
- `handlers/upload.py`: Upload and link generation
- `handlers/start.py`: `/start` flow + access checks
- `handlers/deliver.py`: File delivery + callback checks
- `handlers/channel.py`: Channel membership + join request handling
- `database/db.py`: SQLite/Supabase data layer

## Requirements

- Python 3.10+
- Telegram bots created via BotFather
- Bot ko required channels me admin/member rights

Install dependencies:

```bash
pip install -r requirements.txt
```

## 1) .env Setup

Create `.env` from `.env.example` and fill values:

```dotenv
BOT_TOKEN=YOUR_PRIMARY_BOT_TOKEN
BOT_TOKEN1=YOUR_SECONDARY_BOT_TOKEN

ADMIN_ID=123456789
LOG_CHANNEL=-1001234567890
STORAGE_CHANNEL_ID=-1001234567890

NEVER_EXPIRE_LINKS=1
FILE_EXPIRY_MINUTES=5
CLEANUP_INTERVAL_MINUTES=1
BROADCAST_CLEANUP_INTERVAL_MINUTES=30

USE_SUPABASE=1
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxx
```

Notes:
- `ADMIN_ID` only uploader hoga.
- `STORAGE_CHANNEL_ID` me primary + secondary bot dono required access ke saath hone chahiye.
- Agar Supabase use nahi karna: `USE_SUPABASE=0`.

## 2) Supabase Database Setup

Agar aap `USE_SUPABASE=1` use karna chahte hain, to bot start karne se **pehle** Supabase me schema create karna hoga.

### Prerequisites

1. [Supabase](https://supabase.com) par free account banayein.
2. Ek naya project create karein.
3. Project settings se **Project URL** (`SUPABASE_URL`) aur **service_role key** (`SUPABASE_SERVICE_ROLE_KEY`) copy karein:
   - Dashboard → ⚙️ Project Settings → API → **Project URL** & **Service Role** secret.

### `supabase.sql` kya hai?

`supabase.sql` (repo root me) ek migration script hai jo bot ke liye required tables create karta hai:

| Table | Purpose |
|-------|---------|
| `users` | Telegram user records |
| `files` | Uploaded file metadata + share tokens |
| `channels` | Required-join channel config |
| `broadcasts` | Broadcast message tracking |

### SQL Run Karo — Option A: Supabase SQL Editor (Recommended)

1. Supabase Dashboard kholein → apna project select karein.
2. Left sidebar me **SQL Editor** par click karein.
3. **New query** click karein.
4. `supabase.sql` file ka poora content copy karein aur editor me paste karein.
5. **Run** (▶) button click karein.

### SQL Run Karo — Option B: `psql` CLI

```bash
psql "postgresql://postgres:<YOUR_DB_PASSWORD>@db.<YOUR_PROJECT_REF>.supabase.co:5432/postgres" \
  -f supabase.sql
```

Connection string aapko Supabase Dashboard → ⚙️ Project Settings → Database → **Connection string** me milegi.

### `.env` me enable karein

```dotenv
USE_SUPABASE=1
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
```

> **Note:** Agar Supabase use nahi karna to `USE_SUPABASE=0` set karein — bot SQLite use karega.

---

## 3) channels.txt Setup (Required Channel Lock)

Channel lock config ab `channels.txt` se hota hai.

Format:

```ini
JOIN_CHANNEL_IDS1=-1001234567890
JOIN_CHANNEL_LINKS1=https://t.me/+InviteLinkOne

JOIN_CHANNEL_IDS2=-1009876543210
JOIN_CHANNEL_LINKS2=https://t.me/+InviteLinkTwo
```

Meaning:
- `JOIN_CHANNEL_IDS<n>`: verify target (best: `-100...` channel id, ya `@username`)
- `JOIN_CHANNEL_LINKS<n>`: user ko join karne ke liye button URL

Important:
- Numbering continuous rakho: `1,2,3...`
- Agar user ne channel join request send ki hai, secondary bot usko process karke access allow kar sakta hai (bot ko proper permissions chahiye)

## 4) Run Bot

Recommended:

```bash
python main.py
```

Stop running bots:

```bash
./stop_bots.sh
```

## 5) How Flow Works

### Admin Upload Flow (Primary Bot)
1. Admin file send karta hai primary bot ko
2. Bot file ko storage channel me copy karta hai
3. Bot DB me metadata save karta hai
4. Bot share link deta hai (BOT_TOKEN1 username ke saath)

### User Download Flow (Secondary Bot)
1. User link open karta hai: `https://t.me/<BOT_TOKEN1_username>?start=<file_id>`
2. Bot required channels check karta hai
3. Joined/requested user ko file deliver hoti hai
4. File message 15 minutes me delete ho jata hai

## 6) Supabase Notes

Agar `USE_SUPABASE=1`:
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` required
- `users` table me uploader user record pehle save hota hai
- `files` table me file metadata save hota hai

## 7) Common Errors & Fixes

### `foreign key constraint files_user_id_fkey`
Cause: `files.user_id` ka user `users` table me missing.
Fix: upload path me user save pehle hona chahiye (already implemented).

### `Message is not modified`
Cause: same text + same markup ke saath message edit attempt.
Fix: callback me duplicate edit avoid kiya gaya hai.

### `getChatMember 400 Bad Request`
Cause: invalid verify target ya bot ke paas access nahi.
Fix:
- `JOIN_CHANNEL_IDS<n>` me valid `-100...` id ya `@username` do
- Bot ko target channels me required rights do

### User joined but access denied
Check:
- `channels.txt` values correct hain?
- Secondary bot channel me present/admin hai?
- Join request mode me bot ko approve rights hai?

## 8) Quick Test Checklist

1. `python main.py` run hota hai bina error
2. Admin file upload karta hai, link milta hai
3. User secondary bot link open karta hai
4. Join buttons show hote hain (agar required)
5. Join/request ke baad `✅ Joined? Try Again` par file milti hai
6. 15 min baad delivered message auto-delete hota hai

## 9) Security Tips

- `.env` aur keys ko git me commit mat karo
- Supabase service role key ko private rakho
- Channel IDs/links sirf trusted admins ke through update karo

---

If needed, next step me admin command add kiya ja sakta hai jisse runtime pe `channels.txt` reload ho jaye bina bot restart ke.
