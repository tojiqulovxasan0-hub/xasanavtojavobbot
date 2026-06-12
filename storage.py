import json, os, threading
from datetime import datetime

# Fayl manzili — bu faylning yonida
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
_lock     = threading.Lock()

_default = {
    "broadcast_targets": [], "target_users": [],
    "blacklist": [], "allowed_users": [],
    "auto_reply_on": True,
    "auto_reply_text": "Salom! Hozir band, tez orada javob beraman 🙏",
    "welcome_on": False, "welcome_text": "Guruhga xush kelibsiz, {name}! 👋",
    "goodbye_on": False, "goodbye_text": "{name} guruhdan chiqdi. 👋",
    "scheduled_messages": [], "notes": {}, "filters": {}, "tags": {},
    "stats": {"sent": 0, "failed": 0, "auto_replies": 0, "filter_hits": 0},
    "auto_replied_users": [], "broadcast_log": [],
    "dm_limit_count": 0, "dm_limit_date": "",
    # Multi-user: har bir foydalanuvchi o'z ma'lumotlari
    "user_sessions": {},
}

def _load() -> dict:
    with _lock:
        if not os.path.exists(DATA_FILE):
            _raw_save(_default.copy())
            return _default.copy()
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in _default.items():
            data.setdefault(k, v)
        return data

def _raw_save(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _save(data: dict):
    with _lock:
        _raw_save(data)

# --- Broadcast ---
def get_broadcast_targets() -> list: return _load()["broadcast_targets"]
def add_broadcast_target(t) -> bool:
    data=_load()
    try: t=int(t)
    except: pass
    if t in data["broadcast_targets"]: return False
    data["broadcast_targets"].append(t); _save(data); return True
def remove_broadcast_target(t) -> bool:
    data=_load()
    try: t=int(t)
    except: pass
    if t not in data["broadcast_targets"]: return False
    data["broadcast_targets"].remove(t); _save(data); return True
def clear_broadcast_targets():
    data=_load(); data["broadcast_targets"]=[]; _save(data)

# --- Target users ---
def get_target_users() -> list: return _load()["target_users"]
def add_target_user(u) -> bool:
    data=_load()
    try: u=int(u)
    except: pass
    if u in data["target_users"]: return False
    data["target_users"].append(u); _save(data); return True
def remove_target_user(u) -> bool:
    data=_load()
    try: u=int(u)
    except: pass
    if u not in data["target_users"]: return False
    data["target_users"].remove(u); _save(data); return True
def clear_target_users():
    data=_load(); data["target_users"]=[]; _save(data)

# --- Blacklist ---
def get_blacklist() -> list: return _load()["blacklist"]
def add_to_blacklist(u) -> bool:
    data=_load()
    try: u=int(u)
    except: pass
    if u in data["blacklist"]: return False
    data["blacklist"].append(u); _save(data); return True
def remove_from_blacklist(u) -> bool:
    data=_load()
    try: u=int(u)
    except: pass
    if u not in data["blacklist"]: return False
    data["blacklist"].remove(u); _save(data); return True
def is_blacklisted(u) -> bool:
    try: u=int(u)
    except: pass
    return u in _load()["blacklist"]

# --- Allowed users ---
def get_allowed_users() -> list: return _load()["allowed_users"]
def add_allowed_user(u) -> bool:
    data=_load()
    try: u=int(u)
    except: pass
    if u in data["allowed_users"]: return False
    data["allowed_users"].append(u); _save(data); return True
def remove_allowed_user(u) -> bool:
    data=_load()
    try: u=int(u)
    except: pass
    if u not in data["allowed_users"]: return False
    data["allowed_users"].remove(u); _save(data); return True

# --- AR log ---
def get_auto_replied_users() -> list: return _load()["auto_replied_users"]
def add_auto_replied_user(uid: int, name: str, username: str):
    data=_load()
    for item in data["auto_replied_users"]:
        if item["id"]==uid:
            item["count"]=item.get("count",1)+1
            item["last_seen"]=datetime.now().strftime("%Y-%m-%d %H:%M")
            _save(data); return
    data["auto_replied_users"].append({
        "id":uid,"name":name,"username":username,"count":1,
        "first_seen":datetime.now().strftime("%Y-%m-%d %H:%M"),
        "last_seen":datetime.now().strftime("%Y-%m-%d %H:%M"),
    }); _save(data)
def clear_auto_replied_users():
    data=_load(); data["auto_replied_users"]=[]; _save(data)

# --- Auto-reply ---
def get_auto_reply() -> bool: return _load()["auto_reply_on"]
def set_auto_reply(v: bool):
    data=_load(); data["auto_reply_on"]=v; _save(data)
def get_auto_reply_text() -> str: return _load()["auto_reply_text"]
def set_auto_reply_text(t: str):
    data=_load(); data["auto_reply_text"]=t; _save(data)

# --- Welcome/Goodbye ---
def get_welcome() -> dict:
    d=_load(); return {"on":d["welcome_on"],"text":d["welcome_text"]}
def set_welcome(on=None,text=None):
    data=_load()
    if on is not None: data["welcome_on"]=on
    if text is not None: data["welcome_text"]=text
    _save(data)
def get_goodbye() -> dict:
    d=_load(); return {"on":d["goodbye_on"],"text":d["goodbye_text"]}
def set_goodbye(on=None,text=None):
    data=_load()
    if on is not None: data["goodbye_on"]=on
    if text is not None: data["goodbye_text"]=text
    _save(data)

# --- Notes ---
def get_notes() -> dict: return _load()["notes"]
def add_note(name:str,text:str):
    data=_load(); data["notes"][name]=text; _save(data)
def get_note(name:str): return _load()["notes"].get(name)
def delete_note(name:str) -> bool:
    data=_load()
    if name not in data["notes"]: return False
    del data["notes"][name]; _save(data); return True

# --- Filters ---
def get_filters() -> dict: return _load()["filters"]
def add_filter(kw:str,reply:str):
    data=_load(); data["filters"][kw.lower()]=reply; _save(data)
def get_filter(kw:str): return _load()["filters"].get(kw.lower())
def delete_filter(kw:str) -> bool:
    data=_load()
    if kw.lower() not in data["filters"]: return False
    del data["filters"][kw.lower()]; _save(data); return True

# --- Tags ---
def get_tags() -> dict: return _load()["tags"]
def set_tag(uid:int,tag:str):
    data=_load(); data["tags"][str(uid)]=tag; _save(data)
def get_tag(uid:int) -> str: return _load()["tags"].get(str(uid),"")
def remove_tag(uid:int):
    data=_load(); data["tags"].pop(str(uid),None); _save(data)

# --- Stats ---
def get_stats() -> dict: return _load()["stats"]
def inc_stat(key:str,n:int=1):
    data=_load(); data["stats"][key]=data["stats"].get(key,0)+n; _save(data)
def reset_stats():
    data=_load()
    data["stats"]={"sent":0,"failed":0,"auto_replies":0,"filter_hits":0}; _save(data)

# --- Scheduled ---
def get_scheduled() -> list: return _load()["scheduled_messages"]
def add_scheduled(item:dict):
    data=_load(); data["scheduled_messages"].append(item); _save(data)
def remove_scheduled(idx:int) -> bool:
    data=_load()
    if idx<0 or idx>=len(data["scheduled_messages"]): return False
    data["scheduled_messages"].pop(idx); _save(data); return True
def clear_scheduled():
    data=_load(); data["scheduled_messages"]=[]; _save(data)

# --- DM limit ---
def check_dm_limit(limit:int) -> tuple:
    data=_load(); today=datetime.now().strftime("%Y-%m-%d")
    if data["dm_limit_date"]!=today:
        data["dm_limit_count"]=0; data["dm_limit_date"]=today; _save(data)
    rem=limit-data["dm_limit_count"]
    return rem>0, max(rem,0)
def inc_dm_count(n:int=1):
    data=_load(); today=datetime.now().strftime("%Y-%m-%d")
    if data["dm_limit_date"]!=today:
        data["dm_limit_count"]=0; data["dm_limit_date"]=today
    data["dm_limit_count"]+=n; _save(data)

# --- Broadcast log ---
def add_broadcast_log(entry:dict):
    data=_load(); data["broadcast_log"].insert(0,entry)
    data["broadcast_log"]=data["broadcast_log"][:20]; _save(data)
def get_broadcast_log() -> list: return _load()["broadcast_log"]

# ─────────────────────────────────────────────────────────────
# MULTI-USER SESSIONS
# Har bir foydalanuvchi o'z alohida data'siga ega
# ─────────────────────────────────────────────────────────────
def _uid(uid:int) -> str: return str(uid)

def user_exists(uid:int) -> bool:
    return _uid(uid) in _load()["user_sessions"]

def create_user(uid:int, name:str, username:str=""):
    data=_load()
    if _uid(uid) not in data["user_sessions"]:
        data["user_sessions"][_uid(uid)]={
            "id":uid,"name":name,"username":username,
            "joined":datetime.now().strftime("%Y-%m-%d %H:%M"),
            "target_users":[],"broadcast_targets":[],
            "notes":{},"filters":{},"tags":{},
            "auto_reply_on":False,
            "auto_reply_text":"Salom! Hozir band 🙏",
            "stats":{"sent":0,"failed":0},
            "dm_limit_count":0,"dm_limit_date":"",
            "blacklist":[],
        }
        _save(data)
    return data["user_sessions"][_uid(uid)]

def get_user(uid:int) -> dict | None:
    return _load()["user_sessions"].get(_uid(uid))

def get_all_users() -> list:
    return list(_load()["user_sessions"].values())

def update_user(uid:int, **kwargs):
    data=_load()
    key=_uid(uid)
    if key not in data["user_sessions"]: return
    data["user_sessions"][key].update(kwargs)
    _save(data)

def delete_user(uid:int) -> bool:
    data=_load()
    key=_uid(uid)
    if key not in data["user_sessions"]: return False
    del data["user_sessions"][key]; _save(data); return True

# User-specific helpers
def user_add_target(uid:int, u) -> bool:
    data=_load(); key=_uid(uid)
    if key not in data["user_sessions"]: return False
    try: u=int(u)
    except: pass
    if u in data["user_sessions"][key]["target_users"]: return False
    data["user_sessions"][key]["target_users"].append(u); _save(data); return True

def user_remove_target(uid:int, u) -> bool:
    data=_load(); key=_uid(uid)
    if key not in data["user_sessions"]: return False
    try: u=int(u)
    except: pass
    if u not in data["user_sessions"][key]["target_users"]: return False
    data["user_sessions"][key]["target_users"].remove(u); _save(data); return True

def user_get_targets(uid:int) -> list:
    u=get_user(uid); return u["target_users"] if u else []

def user_add_group(uid:int, t) -> bool:
    data=_load(); key=_uid(uid)
    if key not in data["user_sessions"]: return False
    try: t=int(t)
    except: pass
    if t in data["user_sessions"][key]["broadcast_targets"]: return False
    data["user_sessions"][key]["broadcast_targets"].append(t); _save(data); return True

def user_remove_group(uid:int, t) -> bool:
    data=_load(); key=_uid(uid)
    try: t=int(t)
    except: pass
    if key not in data["user_sessions"]: return False
    if t not in data["user_sessions"][key]["broadcast_targets"]: return False
    data["user_sessions"][key]["broadcast_targets"].remove(t); _save(data); return True

def user_get_groups(uid:int) -> list:
    u=get_user(uid); return u["broadcast_targets"] if u else []

def user_inc_stat(uid:int, key:str, n:int=1):
    data=_load(); k=_uid(uid)
    if k not in data["user_sessions"]: return
    data["user_sessions"][k]["stats"][key]=data["user_sessions"][k]["stats"].get(key,0)+n
    _save(data)

def user_check_dm_limit(uid:int, limit:int) -> tuple:
    u=get_user(uid)
    if not u: return False, 0
    today=datetime.now().strftime("%Y-%m-%d")
    if u.get("dm_limit_date")!=today:
        update_user(uid, dm_limit_count=0, dm_limit_date=today)
        u=get_user(uid)
    rem=limit-u.get("dm_limit_count",0)
    return rem>0, max(rem,0)

def user_inc_dm(uid:int, n:int=1):
    data=_load(); k=_uid(uid)
    if k not in data["user_sessions"]: return
    today=datetime.now().strftime("%Y-%m-%d")
    if data["user_sessions"][k].get("dm_limit_date")!=today:
        data["user_sessions"][k]["dm_limit_count"]=0
        data["user_sessions"][k]["dm_limit_date"]=today
    data["user_sessions"][k]["dm_limit_count"]=data["user_sessions"][k].get("dm_limit_count",0)+n
    _save(data)

def user_is_blacklisted(uid:int, target) -> bool:
    u=get_user(uid)
    if not u: return False
    try: target=int(target)
    except: pass
    return target in u.get("blacklist",[])
