# AI Max ON by Default - Daily Video - Queue Notes

Topic: Google Ads Editor 2.14, AI Max ON by default for new Search campaigns (Nov 12, 2026 update).
Status: QUEUED as a draft proposal for Fri 2026-11-20, 20:00 Dhaka. NOT posted. Goes out only when Mofassel says so in the Posting Agent chat.

## Files in this folder
- media.mp4 - the SFX version of the video (46.6 sec, 1080x1920, 30fps, clone voiceover, soft whoosh + light tick, max -0.9 dB). Use this one.
- thumbnail-claude.png - cover made inside Claude (1080x1920, "Google turns AI Max ON. By default.").
- caption.txt - IG + Facebook Page caption (auto destinations share one caption).
- caption-linkedin.txt - LinkedIn caption, for his MANUAL LinkedIn post (LinkedIn is manual-only in v1).
- post.json - date, slot, destinations.

## Source files (VM)
- Video SFX: ~/workspace/daily-video-ai-max/ai-max-default-on-sfx.mp4
- Video no-SFX (do NOT use): ~/workspace/daily-video-ai-max/ai-max-default-on.mp4
- Voiceover: ~/workspace/voice-clone-test/daily-video-ai-max-voice.mp3
- Script: ~/workspace/voice-clone-test/daily-video-ai-max-script.md
- Captions file: ~/workspace/daily-video-ai-max/captions.md
- Do NOT use the 3 PIL thumbnails in ~/workspace/daily-video-ai-max/ (thumb-ig-fb-1080x1920.jpg, thumb-linkedin-1200x627.jpg, thumb-fb-1200x630.jpg). Per his Nov 20 instruction, thumbnails are made inside Claude only; the assistant-made ones are not to be used.

## Destinations
- facebook_page + instagram + linkedin_personal (English video).
- Personal Facebook NOT included: per his split, Personal Facebook is Bangla only.

## WARNINGS - check before posting
1. INVENTED MOCKUP DETAILS: Claude flagged that the UI mockup details in the video (plumber business, town names, dollar amounts) are invented, not real. Flag to Mofassel before posting.
2. INSTAGRAM NEEDS A PUBLIC URL: the agent cannot post to Instagram without a public video URL in media_url.txt (Graph API rule). No media_url.txt in this folder yet. Without it, Instagram reports blocked and the post STOPS there (FB Page posts first, then it stops, LinkedIn never reached). Do not approve the post until the URL question is settled.
3. NO TOKENS YET: the agent on his PC has no Meta token in .env, so it runs in dry-run mode. Nothing can post for real until he supplies the Page token, Page ID and Instagram ID.
4. LinkedIn is MANUAL in v1: the agent never auto-posts LinkedIn. He posts it himself with caption-linkedin.txt.
