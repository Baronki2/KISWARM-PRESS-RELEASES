#!/usr/bin/env python3
"""
KISWARM Mail Extractor — kiswarmkirouter@gmail.com
Extracts all messages from m.heyd@sahgreen.de (company address) since a given date,
saves every attachment into the evidence archive with SHA256 hashing,
and produces an index of all counterstrike actions found.

Usage:
    python3 kiswarm-mail-extract.py [--since YYYY-MM-DD] [--out DIR]
"""
import argparse
import email
import hashlib
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timezone
from email.header import decode_header

CREDS = "/home/sah/.config/gmail-mesh/kiswarmkirouter/credentials.json"
SOURCE_ADDRESS = "m.heyd@sahgreen.de"


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def to_imap_date(s):
    """Convert YYYY-MM-DD (or DD-Mon-YYYY) into the only form Gmail's IMAP
    SEARCH accepts: DD-Mon-YYYY. Accepting an already-correct date is
    idempotent."""
    s = (s or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return "{:02d}-{}-{:04d}".format(d, _MONTHS[mo - 1], y)
    if re.match(r"^\d{2}-[A-Za-z]{3}-\d{4}$", s):
        return s
    raise ValueError("unsupported --since format: {!r} (use YYYY-MM-DD)".format(s))


def decode_str(s):
    if s is None:
        return ""
    out = []
    for chunk, enc in decode_header(s):
        if isinstance(chunk, bytes):
            out.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(chunk)
    return "".join(out)


def body_text(msg):
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    parts.append(part.get_payload(decode=True).decode("utf-8", errors="replace"))
                except Exception:
                    pass
        if parts:
            return "\n".join(parts)
        for part in msg.walk():
            if part.get_content_maintype() == "text":
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    pass
        return ""
    try:
        return msg.get_payload(decode=True).decode("utf-8", errors="replace")
    except Exception:
        return ""


def sanitize(name):
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return name[:110] or "attachment"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="08-Nov-2026")
    ap.add_argument("--out", default="/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27")
    ap.add_argument("--index", default="/home/sah/.config/sah-vault")
    args = ap.parse_args()

    c = json.load(open(CREDS))
    m = imaplib.IMAP4_SSL(c["imap_host"], c["imap_port"])
    m.login(c["address"], c["app_password"])

    # Search across folders
    folders = ["INBOX"]
    typ, boxlist = m.list()
    for b in boxlist:
        raw = b.decode()
        name = raw.split('"')[-2] if '"' in raw else raw.split()[-1]
        if name.upper() in ("SENT", "[GMAIL]/SENT MAIL", "GESENDETE ELEMENTE"):
            folders.append(name)
            break

    all_msgs = []
    for folder in folders:
        try:
            m.select(f'"{folder}"' if " " in folder else folder)
            # Gmail's IMAP SEARCH does not accept an ISO date. The only accepted form
            # is DD-Mon-YYYY (e.g. 18-Nov-2026). Passing "2026-11-18" yields
            # "BAD [Could not parse command]" and the search silently returns zero
            # messages — which looks exactly like "no new mail" and is not.
            since_imap = to_imap_date(args.since)
            st, nums = m.search(None, "SINCE", since_imap)
            if st == "OK" and nums[0]:
                for num in nums[0].split():
                    st2, data = m.fetch(num, "(RFC822)")
                    if st2 != "OK":
                        continue
                    all_msgs.append((folder, num, email.message_from_bytes(data[0][1])))
        except Exception as e:
            print(f"  folder {folder}: {e}")

    print(f"  scanned folders: {folders}")
    print(f"  messages since {args.since}: {len(all_msgs)}")

    os.makedirs(args.out, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    index = {
        "source_account": c["address"],
        "source_filter": f'from/related to "{SOURCE_ADDRESS}"',
        "since": args.since,
        "scanned_at": ts,
        "messages_scanned": len(all_msgs),
        "matched_messages": [],
        "attachments_extracted": [],
    }

    seen_hashes = {}
    for folder, num, msg in all_msgs:
        frm = decode_str(msg.get("From", ""))
        to = decode_str(msg.get("To", ""))
        cc = decode_str(msg.get("Cc", ""))
        sub = decode_str(msg.get("Subject", ""))
        date = msg.get("Date", "")
        blob = (frm + " " + to + " " + cc + " " + sub).lower()

        # Match: sent FROM the company address, or received by it (forwarded copies)
        is_company = SOURCE_ADDRESS.lower() in blob
        if not is_company:
            continue

        body = body_text(msg)
        entry = {
            "folder": folder,
            "imap_num": num.decode() if hasattr(num, "decode") else str(num),
            "date": date,
            "from": frm,
            "to": to,
            "cc": cc,
            "subject": sub,
            "attachment_count": 0,
            "attachments": [],
        }

        # Extract attachments
        for part in msg.walk():
            fn = part.get_filename()
            if not fn:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            fname = sanitize(decode_str(fn))
            h = hashlib.sha256(payload).hexdigest()
            # dedupe by hash
            if h in seen_hashes:
                fname = seen_hashes[h]
            else:
                dest = os.path.join(args.out, fname)
                base, ext = os.path.splitext(fname)
                n = 1
                while os.path.exists(dest):
                    fname = f"{base}_{n}{ext}"
                    dest = os.path.join(args.out, fname)
                    n += 1
                with open(dest, "wb") as fh:
                    fh.write(payload)
                seen_hashes[h] = fname
                index["attachments_extracted"].append({
                    "filename": fname,
                    "sha256": h,
                    "size": len(payload),
                    "source_subject": sub,
                    "source_date": date,
                    "source_from": frm,
                })
            entry["attachments"].append({"filename": fname, "sha256": h, "size": len(payload)})
            entry["attachment_count"] += 1

        # Save the body as text evidence
        if body.strip():
            safe_sub = sanitize(sub)[:70] or "message"
            bpath = os.path.join(args.out, f"MAIL_{date_to_ord(date)}_{safe_sub}.md")
            with open(bpath, "w") as fh:
                fh.write(f"# {sub}\n\n**Date**: {date}\n**From**: {frm}\n**To**: {to}\n**CC**: {cc}\n\n---\n\n{body}\n")
            entry["body_file"] = os.path.basename(bpath)
            bh = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
            entry["body_sha256"] = bh

        index["matched_messages"].append(entry)

    index["matched_count"] = len(index["matched_messages"])
    index["unique_attachments"] = len({a["sha256"] for a in index["attachments_extracted"]})
    index["total_attachment_bytes"] = sum(a["size"] for a in index["attachments_extracted"])

    # The index filename must follow the run date. It used to be hardcoded to
    # 2026-11-18, so every run OVERWROTE that one file while a second file
    # (…-2026-11-20.json) was written by hand — the old record's hash then no
    # longer matched its file, which looks exactly like a broken evidence
    # chain to anyone checking it.
    _stamp = datetime.now().strftime("%Y-%m-%d")
    idx_path = os.path.join(args.index,
                            "MAIL-EXTRACTION-KISWARM-ROUTER-{0}.json".format(_stamp))
    with open(idx_path, "w") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)

    print(f"\n  matched messages: {index['matched_count']}")
    print(f"  attachments extracted: {len(index['attachments_extracted'])} ({index['unique_attachments']} unique)")
    print(f"  total attachment bytes: {index['total_attachment_bytes']:,}")
    print(f"  index: {idx_path}")

    for a in index["attachments_extracted"]:
        print(f"    {a['filename'][:70]:70s} {a['size']:>10,} B  {a['sha256'][:16]}")

    m.close()
    m.logout()


def date_to_ord(date):
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date).strftime("%Y%m%d")
    except Exception:
        return "XXXXXX"


if __name__ == "__main__":
    main()
