import urllib.request
import urllib.parse
import urllib.error
import json
import re
import xml.etree.ElementTree as ET
import datetime
from .database import get_settings, set_setting, log_activity

TWO_INDEX_API_BASE = "https://2index.ninja/api/v1"

class TwoIndexService:
    @staticmethod
    def get_api_key():
        st = get_settings()
        return st.get("TWO_INDEX_API_KEY", "").strip()

    @staticmethod
    def _api_call(endpoint: str, api_key: str, method: str = "GET", payload: dict = None):
        if not api_key:
            return {"success": False, "error": "Chưa nhập API Token 2Index.ninja"}

        url = f"{TWO_INDEX_API_BASE}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Accept": "application/json",
            "User-Agent": "PBN-Dashboard-2Index/2.0"
        }
        
        data_bytes = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                res_body = resp.read().decode("utf-8")
                try:
                    return json.loads(res_body)
                except Exception:
                    return {"success": True, "raw": res_body}
        except urllib.error.HTTPError as e:
            try:
                err_json = json.loads(e.read().decode("utf-8"))
                err_msg = err_json.get("error") or err_json.get("message")
                if not err_msg and err_json.get("errors"):
                    err_msg = str(err_json.get("errors"))
                return {"success": False, "error": err_msg or f"HTTP {e.code}", "status_code": e.code, "raw": err_json}
            except Exception:
                return {"success": False, "error": f"HTTP {e.code}: {e.reason}", "status_code": e.code}
        except Exception as e:
            return {"success": False, "error": f"Lỗi kết nối tới 2Index.ninja: {str(e)}"}

    @classmethod
    def get_account_info(cls, api_key: str = None):
        key = api_key or cls.get_api_key()
        if not key:
            return {"success": False, "error": "Chưa cấu hình API Key 2Index.ninja"}
        
        res = cls._api_call("account", key, method="GET")
        if res.get("success") and res.get("account"):
            return {
                "success": True,
                "account": res["account"]
            }
        err = res.get("error") or "Không thể lấy thông tin tài khoản 2Index.ninja"
        return {"success": False, "error": err, "raw": res}

    @classmethod
    def add_links_simple(cls, links: list, project_name: str = "PBN Dashboard", google: int = 1, bing: int = 1, yandex: int = 0, api_key: str = None):
        key = api_key or cls.get_api_key()
        if not key:
            return {"success": False, "error": "Chưa cấu hình API Key 2Index.ninja"}

        if not links:
            return {"success": False, "error": "Danh sách link trống"}

        # Normalize and filter links
        clean_links = []
        for l in links:
            l_str = str(l).strip()
            if l_str and (l_str.startswith("http://") or l_str.startswith("https://")):
                clean_links.append(l_str)

        # Deduplicate preserving order
        seen = set()
        dedup_links = []
        for l in clean_links:
            if l not in seen:
                seen.add(l)
                dedup_links.append(l)

        if not dedup_links:
            return {"success": False, "error": "Không có link hợp lệ để gửi index"}

        payload = {
            "project_name": project_name or "PBN Dashboard",
            "links": dedup_links,
            "google": 1 if google else 0,
            "bing": 1 if bing else 0,
            "yandex": 1 if yandex else 0
        }

        res = cls._api_call("link/add_simple", key, method="POST", payload=payload)
        return res

    @classmethod
    def discover_and_extract_sitemap(cls, domain: str, max_urls: int = 250):
        """
        Discovers and extracts URLs from WordPress sitemap (sitemap_index.xml, sitemap.xml, or wp-sitemap.xml).
        """
        domain = re.sub(r"^https?://", "", domain).strip().rstrip("/")
        sitemap_candidates = [
            f"https://{domain}/sitemap_index.xml",
            f"https://{domain}/wp-sitemap.xml",
            f"https://{domain}/sitemap.xml"
        ]

        found_sitemap_url = None
        extracted_urls = [f"https://{domain}/"] # Always include homepage

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/xml,text/xml,*/*"
        }

        def fetch_xml(url):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as r:
                    content = r.read().decode("utf-8", errors="ignore")
                    return content
            except Exception:
                return None

        for s_url in sitemap_candidates:
            xml_text = fetch_xml(s_url)
            if xml_text and ("<urlset" in xml_text or "<sitemapindex" in xml_text):
                found_sitemap_url = s_url
                # Parse XML
                try:
                    # Clean XML namespaces for easier regex / xpath
                    locs = re.findall(r"<loc>\s*(https?://[^<\s]+)\s*</loc>", xml_text, re.IGNORECASE)
                    
                    if "<sitemapindex" in xml_text:
                        # Sub-sitemaps found (e.g. post-sitemap.xml, page-sitemap.xml)
                        # Fetch post / page sub-sitemaps
                        for sub_sitemap in locs:
                            if any(k in sub_sitemap for k in ["post", "page", "category", "tag"]) or len(locs) <= 4:
                                sub_xml = fetch_xml(sub_sitemap)
                                if sub_xml:
                                    sub_locs = re.findall(r"<loc>\s*(https?://[^<\s]+)\s*</loc>", sub_xml, re.IGNORECASE)
                                    extracted_urls.extend(sub_locs)
                                    if len(extracted_urls) >= max_urls:
                                        break
                    else:
                        extracted_urls.extend(locs)
                except Exception:
                    pass
                break

        # Deduplicate
        seen = set()
        final_urls = []
        for u in extracted_urls:
            u_clean = u.strip()
            if u_clean not in seen and not u_clean.endswith(".xml"):
                seen.add(u_clean)
                final_urls.append(u_clean)

        return {
            "domain": domain,
            "sitemap_url": found_sitemap_url or f"https://{domain}/sitemap_index.xml",
            "has_sitemap": bool(found_sitemap_url),
            "urls": final_urls[:max_urls],
            "total_urls": len(final_urls[:max_urls])
        }

    @classmethod
    def submit_indexing_job(cls, domains: list, mode: str = "homepage", custom_urls: list = None, google: int = 1, bing: int = 1, yandex: int = 0):
        """
        Submits indexing job to 2Index.ninja:
        - mode 'homepage': sends https://<domain>/ for all domains
        - mode 'sitemap': crawls sitemap for each domain and submits all post/page URLs
        - mode 'custom_urls': sends custom_urls directly
        """
        api_key = cls.get_api_key()
        if not api_key:
            return {"success": False, "error": "Chưa cấu hình API Key 2Index.ninja. Vui lòng nhập API Key trước khi gửi index."}

        urls_to_submit = []
        domain_breakdown = {}

        if mode == "custom_urls":
            urls_to_submit = [u.strip() for u in (custom_urls or []) if u.strip().startswith("http")]
            if not urls_to_submit:
                return {"success": False, "error": "Vui lòng nhập ít nhất 1 đường link (URL) hợp lệ"}
        elif mode == "sitemap":
            for d in domains:
                d_clean = re.sub(r"^https?://", "", d).strip().rstrip("/")
                info = cls.discover_and_extract_sitemap(d_clean)
                site_urls = info.get("urls", [f"https://{d_clean}/"])
                domain_breakdown[d_clean] = {
                    "sitemap": info.get("sitemap_url"),
                    "count": len(site_urls)
                }
                urls_to_submit.extend(site_urls)
        else: # default: homepage
            for d in domains:
                d_clean = re.sub(r"^https?://", "", d).strip().rstrip("/")
                hp = f"https://{d_clean}/"
                urls_to_submit.append(hp)
                domain_breakdown[d_clean] = {"count": 1}

        # Deduplicate
        urls_to_submit = list(dict.fromkeys(urls_to_submit))

        if not urls_to_submit:
            return {"success": False, "error": "Không tìm thấy URL nào để gửi index"}

        # Call 2Index API
        project_name = f"PBN Matrix - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        res = cls.add_links_simple(
            links=urls_to_submit,
            project_name=project_name,
            google=google,
            bing=bing,
            yandex=yandex,
            api_key=api_key
        )

        # Log activity
        if res.get("success"):
            engines = []
            if google: engines.append("Google")
            if bing: engines.append("Bing")
            if yandex: engines.append("Yandex")
            engine_str = ", ".join(engines) or "Google"

            log_activity(
                action="INDEX_SUBMIT_2INDEX",
                target=f"{len(domains)} sites ({len(urls_to_submit)} URLs)",
                detail=f"Đã gửi {len(urls_to_submit)} URL ({mode}) sang 2Index.ninja ({engine_str}). Kết quả: {res.get('message', 'Thành công')}"
            )

        # Fetch updated account info to return remaining balance
        acc_info = cls.get_account_info(api_key)
        
        return {
            "success": res.get("success", False),
            "message": res.get("message") or (res.get("error") if not res.get("success") else "Đã gửi index thành công!"),
            "total_submitted": len(urls_to_submit),
            "mode": mode,
            "domains_count": len(domains),
            "domain_breakdown": domain_breakdown,
            "sample_urls": urls_to_submit[:10],
            "api_response": res,
            "account": acc_info.get("account") if acc_info.get("success") else None
        }
