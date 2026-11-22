import json
import urllib.request
import urllib.parse
from typing import Optional, List, Dict, Any

from .database import get_db, get_all_servers, get_settings, set_setting

CF_API_BASE = "https://api.cloudflare.com/client/v4"

def get_cf_accounts() -> List[dict]:
    """Retrieve all configured Cloudflare API accounts from database settings"""
    settings = get_settings()
    raw = settings.get("cf_accounts", "[]")
    try:
        return json.loads(raw)
    except Exception:
        return []

def save_cf_accounts(accounts: List[dict]):
    """Save Cloudflare API accounts list to settings"""
    set_setting("cf_accounts", json.dumps(accounts))

def make_cf_request(endpoint: str, token: Optional[str] = None, email: Optional[str] = None, key: Optional[str] = None, method: str = "GET", data: Optional[dict] = None) -> dict:
    """Execute authenticated HTTP request to Cloudflare v4 API"""
    url = f"{CF_API_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PBN-Dashboard-CF-Client/2.0"
    }

    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"
    elif email and key:
        headers["X-Auth-Email"] = email.strip()
        headers["X-Auth-Key"] = key.strip()
    else:
        return {"success": False, "errors": [{"message": "No Cloudflare credentials provided"}]}

    payload = json.dumps(data).encode("utf-8") if data else None

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"success": False, "errors": [{"message": f"HTTP {e.code}: {e.reason}"}]}
    except Exception as e:
        return {"success": False, "errors": [{"message": str(e)}]}

def test_cf_credential(token: Optional[str] = None, email: Optional[str] = None, key: Optional[str] = None) -> dict:
    """Verify validity of a Cloudflare API token or Key"""
    if token:
        res = make_cf_request("user/tokens/verify", token=token)
        if res.get("success"):
            # Also fetch count of active zones
            zones_res = make_cf_request("zones?per_page=50", token=token)
            zone_count = len(zones_res.get("result", []))
            return {
                "success": True,
                "message": "Cloudflare API Token hợp lệ",
                "status": res.get("result", {}).get("status"),
                "zone_count": zone_count
            }
        else:
            return {"success": False, "error": res.get("errors", [{}])[0].get("message", "Token không hợp lệ")}
    elif email and key:
        zones_res = make_cf_request("zones?per_page=50", email=email, key=key)
        if zones_res.get("success"):
            return {
                "success": True,
                "message": "Cloudflare Global Key hợp lệ",
                "zone_count": len(zones_res.get("result", []))
            }
        else:
            return {"success": False, "error": zones_res.get("errors", [{}])[0].get("message", "Email/Key không hợp lệ")}
    return {"success": False, "error": "Chưa nhập thông tin API"}

def resolve_domain_via_cf(domain: str) -> dict:
    """
    Looks up a domain across all configured Cloudflare accounts.
    Finds the Zone and queries DNS A records to get the true origin Server IP.
    Matches with the servers table in local database.
    """
    clean_d = domain.lower().strip()
    if "://" in clean_d:
        clean_d = clean_d.split("://")[1]
    clean_d = clean_d.split("/")[0].split(":")[0].strip()
    if clean_d.startswith("www."):
        clean_d = clean_d[4:]

    accounts = get_cf_accounts()
    if not accounts:
        return {"found": False, "reason": "Chưa cấu hình Cloudflare API"}

    servers = {s["host"]: s for s in get_all_servers()}
    # Also index by id
    servers_by_id = {s["id"]: s for s in get_all_servers()}

    # Try matching root domain (e.g. sub.domain.com -> domain.com)
    parts = clean_d.split(".")
    candidate_zones = [clean_d]
    if len(parts) > 2:
        candidate_zones.append(".".join(parts[-2:]))

    for acc in accounts:
        token = acc.get("token")
        email = acc.get("email")
        key = acc.get("key")

        for zname in candidate_zones:
            # 1. Find Zone
            q = urllib.parse.urlencode({"name": zname, "status": "active"})
            z_res = make_cf_request(f"zones?{q}", token=token, email=email, key=key)
            zones = z_res.get("result", [])

            if zones:
                zone = zones[0]
                zone_id = zone["id"]

                # 2. Get DNS A records for this domain
                q_dns = urllib.parse.urlencode({"type": "A"})
                dns_res = make_cf_request(f"zones/{zone_id}/dns_records?{q_dns}", token=token, email=email, key=key)
                records = dns_res.get("result", [])

                for r in records:
                    r_name = r.get("name", "").lower()
                    if r_name == clean_d or r_name == f"www.{clean_d}":
                        origin_ip = r.get("content")
                        proxied = r.get("proxied", False)

                        # Match origin_ip with our servers table
                        matched_server = servers.get(origin_ip)
                        return {
                            "found": True,
                            "domain": clean_d,
                            "zone_name": zone.get("name"),
                            "account_name": acc.get("name", "Cloudflare"),
                            "origin_ip": origin_ip,
                            "proxied": proxied,
                            "matched_server": matched_server,
                            "server_id": matched_server["id"] if matched_server else None,
                            "server_name": matched_server["name"] if matched_server else "Chưa đăng ký trong Servers",
                            "server_host": matched_server["host"] if matched_server else origin_ip,
                            "message": f"Tìm thấy trên Cloudflare ({acc.get('name')}) ➜ Trỏ về IP: {origin_ip}" + (f" ({matched_server['name']})" if matched_server else "")
                        }

    return {"found": False, "domain": clean_d, "reason": "Không tìm thấy domain trong các tài khoản Cloudflare"}
