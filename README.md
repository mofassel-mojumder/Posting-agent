# Posting Agent v1

Alada posting agent. Muse er sathe tomar account connect kora nei. Eta tomar nijer agent, tomar PC te cholbe.

A separate posting agent. It does not connect your accounts to Muse. It is your own agent, it runs on your PC, or on GitHub Actions (free) so the PC can stay off. See "GitHub e publish koro" below.

## Eta ki kore / What it does

- Tumi picture ba video ar caption dibe, agent protidin 2 PM ar 8 PM Asia/Dhaka te post korbe.
- You give a picture or video and a caption, the agent posts it every day at 2 PM and 8 PM Asia/Dhaka.
- 4 ta jayga / 4 destinations:
  1. Facebook Page Mofassel Mojumder - AUTO, Meta Graph API (official)
  2. Instagram @mofassel.mojumder - AUTO, Meta Graph API (official)
  3. Personal Facebook profile - MANUAL, dashboard theke nije post koro
  4. LinkedIn personal profile - MANUAL, dashboard theke nije post koro
- Din e sorboccho 2 ta post, proti slot e 1 ta. Max 2 posts per day, 1 per slot.
- Proti destination er log alada kore thake, logs/audit.log file e. Every destination is logged separately.

## Eta ki kore NA / What it does NOT do

- Content banay na. No content creation.
- Karo message er reply dey na. No auto-reply.
- Bulk DM kore na, karo profile scrape kore na. No bulk DM, no scraping.
- LinkedIn personal profile e nije post kore na, karon ekhane suspension risk sobcheye beshi. It never posts to your LinkedIn personal profile automatically.
- Personal Facebook profile e nije post kore na, karon er kono official API nei. It never posts to your personal Facebook profile automatically.
- Password kothao rakhe na, chay o na. It never stores or asks for a password.
- Kono post fail korle nije theke abar try kore na. It never retries a failed post automatically.

## Keno LinkedIn ar Personal Facebook manual?

- LinkedIn personal profile e automation korle account suspend hote pare, onekei eta dekheche. Tai v1 e LinkedIn sudhu draft-ready thake.
- Personal Facebook profile e post korar kono official API nei. Tai v1 e etao manual.
- Jodi kokhono LinkedIn Company Page thake, tahole official API diye oi Page e post kora jabe. Personal profile e na.

## Chalano / How to run on your Windows PC

1. Python 3.10 ba tar upore install koro. Install Python 3.10 or newer.
2. Ei folder ta tomar PC te copy koro. Copy this folder to your PC.
3. Terminal e ei folder e jao:
   ```
   cd posting-agent
   ```
   Windows e `python` na cholle `py` likho. Tarpor ekbar eta chalao (Windows e somoy er jonno tzdata lage):
   ```
   py -m pip install -r requirements.txt
   ```
4. Token file banao (ekhono token na thakle ei step pore koro):
   ```
   copy .env.example .env
   ```
   Tarpor .env file ta Notepad e khule khali jaygagulo puron koro. Token chara agent DRY RUN mode e cholbe, asol post jabe na.
5. Dashboard chalao:
   ```
   python -m posting_agent dashboard
   ```
   Tarpor browser e kholo: http://localhost:8765
6. Scheduler chalao (alada terminal e):
   ```
   python -m posting_agent
   ```
   Eta proti minute e check korbe, slot er somoy hole post korbe.
7. Bondho korte: terminal e Ctrl+C chap dio, ba dashboard er Stop button chap dio. To stop: press Ctrl+C, or the Stop button on the dashboard.

## Dashboard theke post dao / Add a post from the dashboard (sohoj upay)

1. Dashboard kholo: http://localhost:8765
2. Uporer "Add new post" box e chobi ba video upload koro, caption likho, tarikh ar somoy (2 PM ba 8 PM) bachho, jaygagulo tick thakbe, tarpor Upload chap dio.
3. Hoye gele Queue te post ta dekhte pabe. Folder banate hobe na, agent nije inbox e sajiye rakhbe.
4. Jodi eki date ar somoy er post age theke thake, agent notun folder e -2, -3 diye rakhbe, purono post muche jabe na.

Add a post from the dashboard: open http://localhost:8765, upload a picture or video, type the caption, pick the date and slot (2 PM or 8 PM), keep the destinations checked, press Upload. No folder work needed.

## GitHub e publish koro (PC khula rakhte hobe na) / Publish on GitHub (no PC needed)

GitHub Actions free te chole, taka lage na. PC bondho thakleo somoy hole GitHub er computer agent chalabe. GitHub er somoy UTC te dite hoy. Dhaka UTC+6, tai:
- 08:00 UTC = 14:00 Dhaka (dupur 2 ta)
- 14:00 UTC = 20:00 Dhaka (rat 8 ta)

GitHub Actions runs free, no money needed. The PC can stay off. GitHub runs the agent at the slot times. Times above are UTC and Dhaka.

1. GitHub e notun ekta PRIVATE repo banao, nam dao `posting-agent`.
   WARNING: Portfolio er PUBLIC repo `mofassel-mojumder.github.io` ekhane babohar koro na. Agent er token thake, tai eta alada PRIVATE repo hote hobe. `.env` kokhono push koro na.
   Create a NEW PRIVATE repo named `posting-agent` on GitHub. NEVER use the public portfolio repo. NEVER push `.env`.
2. Ei folder ta oi repo te push koro. Tomar PC er terminal e, `posting-agent` folder er vitore:
   ```
   git init
   git add .
   git commit -m "Posting Agent v1"
   git branch -M main
   git remote add origin https://github.com/mofassel-mojumder/posting-agent.git
   git push -u origin main
   ```
   Jodi remote age theke thake, tahole `git remote add` er bodle `git remote set-url origin https://github.com/mofassel-mojumder/posting-agent.git` likho.
   Push this folder to that new private repo with the commands above.
3. Secret gulo dao. GitHub e repo ta khule Settings > Secrets and variables > Actions > New repository secret e jao. Ei 3 ta secret banao:
   - `META_PAGE_ACCESS_TOKEN` - tomar Meta Page token
   - `META_PAGE_ID` - tomar Page ID
   - `META_INSTAGRAM_USER_ID` - tomar Instagram user ID
   Chaile `DRY_RUN` secret o banate paro, value `false` dile asol post jabe. Token na thakle agent nije theke dry-run e cholbe, kono asol post jabe na, ar workflow fail korbe na.
   Add the 3 secrets above in repo Settings > Secrets and variables > Actions. Without a token the run stays in dry-run mode and does not fail.
4. Post dao GitHub web theke. GitHub e repo ta khule inbox/ folder e jao, Add file > Upload files e click koro. Notun folder er nam dao, example `2026-11-20-1400`, tar vitore rakho: caption.txt, media.jpg ba media.mp4, ar post.json. post.json er vitore likho:
   ```
   {"date": "2026-11-20", "slot": "14:00", "destinations": ["facebook_page", "instagram", "facebook_personal", "linkedin_personal"]}
   ```
   Instagram er jonno media er public URL lagbe. Thakle oi folder e media_url.txt file e link ta rakho. Na thakle Instagram blocked dekhabe, ar agent thambe.
   Add a post from the GitHub website: upload a new folder under inbox/ with caption.txt, a media file, and post.json as above. Or add the post on the PC dashboard first, then push it to GitHub.
5. Check koro. Dupur 2 ta ba rat 8 tar por GitHub e repo ta khule Actions tab e jao. Run ta sobuj hole thik ache. Audit log ta artifact hisebe download kora jabe. Personal Facebook ar LinkedIn e agent nije post kore na, oi 2 ta manual_ready thakbe, tumi nije post korbe.
   After 2 PM or 8 PM Dhaka, check the Actions tab. A green run means it worked. Download the audit log artifact to see what happened.

## Post kibhabe dibe (purono upay, ekhono cholbe) / How to add a post (old way, still works)

1. inbox/ folder er vitore ekta notun folder banao. Example: inbox/2026-11-19-2000/
2. Tar vitore 3 ta jinish rakho:
   - caption.txt - tomar caption, jemon likhecho temon
   - media.jpg ba media.mp4 - tomar picture ba video
   - post.json - niche example ta copy koro:
   ```
   {"date": "2026-11-19", "slot": "20:00", "destinations": ["facebook_page", "instagram", "facebook_personal", "linkedin_personal"]}
   ```
   Date ar slot bodle dio. Slot sudhu "14:00" ba "20:00" hobe.
3. Instagram er jonno media er public URL lagbe. Thakle oi folder e media_url.txt file e link ta rakho. Na thakle Instagram blocked dekhabe, ar agent thambe, eta iccha korei kora.
4. Dashboard e giye dekho post ta queue te ache kina. Dashboard shows the queue and the status log.

## Token kibhabe dibe / How to put tokens in .env

- .env file e sudhu ei 3 ta jinish lagbe:
  ```
  DRY_RUN=false
  META_PAGE_ACCESS_TOKEN=tomar token
  META_PAGE_ID=tomar Page ID
  META_INSTAGRAM_USER_ID=tomar Instagram user ID
  ```
- Token pabe Meta Business Suite / Meta for Developers theke, tomar nijer login diye. Agent kokhono tomar Facebook password chay na.
- .env file ta kauke dio na, ar kothao upload koro na. Linux ba Mac e `chmod 600 .env` dio.
- DRY_RUN=false sudhu tokhoni koro jokhon tumi asol post er jonno ready. Tar age DRY_RUN=true rekhe test koro.

## Safety limits / Nirapotta

- Max 2 posts per day, 1 per slot.
- Destination er majhe 60 theke 120 second gap thake, live mode e.
- Prothom kono destination e vul hole agent oi post ta okhanei thamay, porer destination e jay na, ar nije theke abar try kore na. Vul ta thik kore status.json file ta delete korle tobei abar try kora jabe.
- Dry-run asol post kore na, sudhu log e lekhe "dry_run".

## Test kora hoyeche / Tested

VM e dry-run test cholche, `python3 test_dry_run.py` diye:
- 2 ta slot (14:00 ar 20:00) thik moto chena geche.
- 20:00 er post 14:05 e due hoy na, 20:05 e due hoy.
- Facebook Page dry_run hisebe log hoyeche.
- Instagram public URL chara blocked hoyeche, ar scheduler okhanei thamche.
- Public URL dile 4 ta destination e alada alada log hoyeche, manual 2 ta manual_ready hoyeche.
- Ditiyo bar chalale kono duplicate post hoy ni.
- Kono asol post jay ni, kono token file e nei.

## File gulo / Files

- config.yaml - slot, destination, safety limit
- .env.example - token er khali form, asol .env tumi banabe
- posting_agent/ - agent er code
- posting_agent/dashboard.html - dashboard page
- inbox/sample-2026-11-19-2000/ - sample post, dry-run er jonno
- logs/audit.log - sob attempt er log
- test_dry_run.py - dry-run test
