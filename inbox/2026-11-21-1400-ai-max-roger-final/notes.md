# AI Max ON by Default - Daily Video - Queue Notes

Topic: Google Ads Editor 2.14, AI Max ON by default for new Search campaigns (Nov 12, 2026 update).
Status: QUEUED for Sat 2026-11-21, 14:00 Dhaka. Mofassel approved this video for posting, despite a small mistake.

RESTORED 2026-11-21: this folder was rebuilt from the source files below after a runtime restart wiped the temporary backup. Video, thumbnail, both captions and post.json are the same as the approved version. No status.json exists yet, so the 14:00 slot is still untouched.

## Files in this folder
- media.mp4 - the FINAL video (51.4 sec, 1080x1920, Roger voiceover). Use this one. Do NOT use the old SFX/clone-voice versions.
- thumbnail.png - the thumbnail Mofassel gave (from the 9 Designs - Video chat).
- caption.txt - IG + Facebook Page caption (auto destinations share one caption).
- caption-linkedin.txt - LinkedIn caption. The agent uses this caption for LinkedIn when the file is present.
- post.json - date, slot, destinations.

## Source files (VM)
- Video FINAL: ~/workspace/daily-video-ai-max/ai-max-roger-final.mp4
- Thumbnail: ~/workspace/user/media_library/image/thumbnail.png
- Captions file: ~/workspace/daily-video-ai-max/captions.md

## Destinations
- facebook_page + instagram + linkedin_personal (English video).
- Personal Facebook NOT included: per his split, Personal Facebook is Bangla only.

## WARNINGS - check before posting
1. INVENTED MOCKUP DETAILS: Claude flagged that the UI mockup details in the video (plumber business, town names, dollar amounts) are invented, not real.
2. INSTAGRAM NEEDS A PUBLIC URL: the agent cannot post to Instagram without a public video URL in media_url.txt (Graph API rule). No media_url.txt in this folder yet. Without it, Instagram reports blocked and the post STOPS there (FB Page posts first, then it stops, LinkedIn never reached). Do not approve the post until the URL question is settled.
3. LINKEDIN IS NOW AUTO (changed 2026-11-21): the agent now auto-posts LinkedIn through the official LinkedIn API when LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN are in secrets. Without them, LinkedIn stays manual_ready and he posts it himself with caption-linkedin.txt.
