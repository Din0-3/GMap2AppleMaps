#!/usr/bin/env python3
"""
Build the GMap2AppleMaps iOS Shortcut 「使用AppleMaps導航 (GPS)」 (.shortcut, unsigned).

Usage:
    python3 build_shortcut.py GMap2AppleMaps_unsigned.shortcut
    shortcuts sign --mode anyone -i GMap2AppleMaps_unsigned.shortcut -o "使用AppleMaps導航 (GPS).shortcut"   # macOS

Flow:
  1. Take the share-sheet input as text (URL-decoded).
  2. If it already contains coordinates (desktop place link, @lat,lng, or plain "lat, lng"), use them.
  3. Otherwise pull the link out with a regex, expand it, and fetch the page with a desktop UA.
     Find the place's ftid (0x...:0x...) and ask Google Maps' internal place endpoint for coordinates.
  4. Open Apple Maps driving directions to those coordinates.
  5. Fallbacks: Apple Maps search by the q= text, or copy debug info to the clipboard.
"""
import plistlib
import sys
import uuid

OBJ = "￼"  # placeholder char for variables inside text fields
A = []          # action list

# ---------- helpers ----------
def U():
    return str(uuid.uuid4()).upper()

def out(uid, name):
    return {"Type": "ActionOutput", "OutputUUID": uid, "OutputName": name}

def var(name):
    return {"Type": "Variable", "VariableName": name}

SHORTCUT_INPUT = {"Type": "ExtensionInput"}

def att(v):
    return {"Value": v, "WFSerializationType": "WFTextTokenAttachment"}

def tstr(parts):
    """Text field mixing literal strings and variables."""
    s, rng = "", {}
    for p in parts:
        if isinstance(p, str):
            s += p
        else:
            rng["{%d, 1}" % (len(s.encode("utf-16-le")) // 2)] = p
            s += OBJ
    return {"Value": {"string": s, "attachmentsByRange": rng},
            "WFSerializationType": "WFTextTokenString"}

def act(ident, params):
    A.append({"WFWorkflowActionIdentifier": "is.workflow.actions." + ident,
              "WFWorkflowActionParameters": params})

HAS_ANY_VALUE, NO_VALUE = 100, 101

def if_(g, cond, v):
    act("conditional", {"GroupingIdentifier": g, "WFControlFlowMode": 0, "WFCondition": cond,
                        "WFInput": {"Type": "Variable", "Variable": att(v)}})

def else_(g):
    act("conditional", {"GroupingIdentifier": g, "WFControlFlowMode": 1})

def end_(g):
    act("conditional", {"GroupingIdentifier": g, "WFControlFlowMode": 2, "UUID": U()})

def setv(name, v):
    act("setvariable", {"WFVariableName": name, "WFInput": att(v)})

def match(pattern, parts):
    u = U()
    act("text.match", {"UUID": u, "WFMatchTextPattern": pattern,
                       "WFMatchTextCaseSensitive": False, "text": tstr(parts)})
    return out(u, "Matches")

def group(m, i):
    u = U()
    act("text.match.getgroup", {"UUID": u, "matches": att(m),
                                "WFGetGroupType": "Group At Index", "WFGroupIndex": i})
    return out(u, "Group")

def item(lst, which):
    u = U()
    act("getitemfromlist", {"UUID": u, "WFItemSpecifier": which, "WFInput": att(lst)})
    return out(u, "Item from List")

def text(parts):
    u = U()
    act("gettext", {"UUID": u, "WFTextActionText": tstr(parts)})
    return out(u, "Text")

def urlcode(mode, parts):
    u = U()
    act("urlencode", {"UUID": u, "WFEncodeMode": mode, "WFInput": tstr(parts)})
    return out(u, "URL Encoded Text")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

def fetch(v):
    """Get Contents of URL with a desktop browser User-Agent."""
    u = U()
    act("downloadurl", {
        "UUID": u, "WFURL": tstr([v]), "WFHTTPMethod": "GET", "ShowHeaders": True,
        "WFHTTPHeaders": {"Value": {"WFDictionaryFieldValueItems": [
            {"WFItemType": 0, "WFKey": tstr(["User-Agent"]), "WFValue": tstr([UA])},
            {"WFItemType": 0, "WFKey": tstr(["Accept-Language"]), "WFValue": tstr(["zh-TW,zh;q=0.9"])},
        ]}, "WFSerializationType": "WFDictionaryFieldValue"}})
    return out(u, "Contents of URL")

# ---------- regex ----------
# !3d<lat>!4d<lng> (place pin), @<lat>,<lng> (viewport), =<lat>,<lng> (query), or plain "lat, lng"
P_URL = r"(?:!3d|@|=|^\s*)(-?\d{1,3}\.\d+)(?:!4d|,\s*|%2C)(-?\d{1,3}\.\d+)"
# Google feature id, e.g. 0x3442a9cae035c7a5:0xa8f8f572cc8924c (also escaped forms)
P_FTID = r"(0x[0-9a-fA-F]{6,})(?::|%3A|%253A|\\u003[aA])(0x[0-9a-fA-F]{6,})"
# coordinates inside the /maps/preview/place response
P_API = r"\[null,null,(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)\]"
P_LINK = r"https?://[^\s()<>\"]+"

# ---------- 1. input ----------
setv("Src", urlcode("Decode", [SHORTCUT_INPUT]))
setv("Coords", match(P_URL, [var("Src")]))

# ---------- 2. resolve link ----------
g1 = U(); if_(g1, NO_VALUE, var("Coords"))
links = match(P_LINK, [var("Src")])
g2 = U(); if_(g2, HAS_ANY_VALUE, links)
setv("Link", item(links, "First Item"))
e = U(); act("url.expand", {"UUID": e, "URL": tstr([var("Link")])})
setv("Exp", urlcode("Decode", [out(e, "Expanded URL")]))
setv("Coords", match(P_URL, [var("Exp")]))
g3 = U(); if_(g3, NO_VALUE, var("Coords"))
setv("Html", fetch(var("Link")))
setv("FT", match(P_FTID, [var("Exp"), "\n", var("Html")]))
g4 = U(); if_(g4, HAS_ANY_VALUE, var("FT"))
ft = item(var("FT"), "First Item")
api = text(["https://www.google.com/maps/preview/place?authuser=0&hl=zh-TW&gl=tw&pb=!1m1!1s",
            group(ft, 1), ":", group(ft, 2)])
setv("Coords", match(P_API, [fetch(api)]))
end_(g4)
end_(g3)
end_(g2)
end_(g1)

# ---------- 3. fallbacks ----------
g5 = U(); if_(g5, NO_VALUE, var("Coords"))
qm = match(r"[?&]q=([^&]+)", [var("Exp")])
g6 = U(); if_(g6, HAS_ANY_VALUE, qm)
act("openurl", {"WFInput": att(text(["maps://?q=", urlcode("Encode", [group(qm, 1)])])),
                "Show-WFInput": True})
else_(g6)
head = match(r"^[\s\S]{0,1500}", [var("Html")])
dbg = text(["SRC: ", var("Src"), "\nLINK: ", var("Link"), "\nEXP: ", var("Exp"),
            "\n---HTML---\n", head])
act("setclipboard", {"WFInput": att(dbg)})
act("alert", {"WFAlertActionTitle": "找不到座標（除錯資訊已複製）",
              "WFAlertActionMessage": "請把剪貼簿內容貼到 GitHub issue",
              "WFAlertActionCancelButtonShown": False})
end_(g6)
act("exit", {})
end_(g5)

# ---------- 4. open Apple Maps ----------
last = item(var("Coords"), "Last Item")  # !3d!4d comes after @ in Google URLs
nav = text(["maps://?daddr=", group(last, 1), ",", group(last, 2), "&dirflg=d"])
act("openurl", {"WFInput": att(nav), "Show-WFInput": True})

workflow = {
    "WFWorkflowClientVersion": "2607.0.2",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4292093695, "WFWorkflowIconGlyphNumber": 59511},
    "WFWorkflowImportQuestions": [],
    "WFWorkflowTypes": ["ActionExtension"],  # show in Share Sheet
    "WFWorkflowInputContentItemClasses": ["WFURLContentItem", "WFStringContentItem"],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowHasShortcutInputVariables": True,
    "WFWorkflowNoInputBehavior": {"Name": "WFWorkflowNoInputBehaviorGetClipboard", "Parameters": {}},
    "WFQuickActionSurfaces": [],
    "WFWorkflowActions": A,
}

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "GMap2AppleMaps_unsigned.shortcut"
    with open(path, "wb") as f:
        plistlib.dump(workflow, f, fmt=plistlib.FMT_BINARY)
    print(f"wrote {path} ({len(A)} actions)")
