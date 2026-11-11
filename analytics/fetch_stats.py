"""Pull GA4 numbers for justinbclose.com and write an encrypted stats file.

Runs in GitHub Actions (see .github/workflows/stats.yml). Needs three secrets:
GA4_PROPERTY_ID, GA4_SA_KEY (service-account JSON), DASH_KEY (dashboard passphrase).
The output is AES-GCM encrypted, so the public repo never shows visitor data.
Run with --sample to write made-up data for testing the dashboard.
"""
import base64, datetime as dt, json, os, random, sys
from collections import defaultdict

OUT = os.environ.get("STATS_OUT", "stats.enc.json")
RANGES = {"7": 7, "30": 30, "90": 90}

ISP_WORDS = ["comcast", "xfinity", "charter", "spectrum", "cox ", "cox communications", "at&t", "att services", "verizon",
             "t-mobile", "tmobile", "frontier", "centurylink", "lumen", "google fiber", "starlink", "space exploration",
             "akamai", "cloudflare", "fastly", "apple inc", "icloud", "zscaler", "amazon", "microsoft", "google llc",
             "digitalocean", "ovh", "hetzner", "linode", "rcn", "wow", "mediacom", "optimum", "altice", "windstream",
             "sprint", "cellco", "telus", "rogers", "bell canada", "shaw", "vodafone", "orange", "telefonica",
             "hughes", "viasat", "sonic telecom", "astound", "wave", "ziply", "consolidated", "brightspeed", "metronet",
             "cable", "wireless", "broadband", "telecom", "communications", "mobile", "internet", "isp", "fiber", "datacenter",
             "hosting", "vpn", "private relay"]

def is_isp(org):
    o = (org or "").lower()
    return any(w in o for w in ISP_WORDS)

def channel(src, med, camp):
    s, m = (src or "").lower(), (med or "").lower()
    if m == "job_app" or s == "application": return "Job applications"
    if s == "resume": return "Resume"
    if s == "email" and m == "signature": return "Email signature"
    if "linkedin" in s or "lnkd" in s: return "LinkedIn"
    if "canva" in s: return "Old Canva link"
    if s in ("google", "bing", "duckduckgo", "yahoo", "ecosia") and m == "organic": return "Search"
    if s == "(direct)": return "Direct"
    if "instagram" in s or s in ("ig", "l.instagram.com"): return "Instagram"
    if "mail" in s or m == "email": return "Email"
    return "Other"

# ---------- GA4 ----------
def ga_client():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.oauth2 import service_account
    info = json.loads(os.environ["GA4_SA_KEY"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
    return BetaAnalyticsDataClient(credentials=creds)

def run(client, prop, dims, mets, days, limit=2000, filt=None):
    from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric, DateRange
    req = RunReportRequest(property=f"properties/{prop}", dimensions=[Dimension(name=d) for d in dims],
                           metrics=[Metric(name=m) for m in mets],
                           date_ranges=[DateRange(start_date=f"{days-1}daysAgo", end_date="today")], limit=limit)
    if filt is not None: req.dimension_filter = filt
    out = []
    for r in client.run_report(req).rows:
        row = {d: v.value for d, v in zip(dims, r.dimension_values)}
        for m, v in zip(mets, r.metric_values):
            row[m] = float(v.value) if "." in v.value else int(v.value)
        out.append(row)
    return out

def event_filter(name):
    from google.analytics.data_v1beta.types import FilterExpression, Filter
    return FilterExpression(filter=Filter(field_name="eventName", string_filter=Filter.StringFilter(value=name)))

def coords():
    try:
        import geonamescache
        gc = geonamescache.GeonamesCache(min_city_population=5000)
        best = {}
        for c in gc.get_cities().values():
            k = (c["name"].lower(), c["countrycode"])
            if k not in best or c["population"] > best[k][2]: best[k] = (c["latitude"], c["longitude"], c["population"])
        return best
    except Exception as e:
        print("no geonamescache:", e); return {}

def pull():
    prop = os.environ["GA4_PROPERTY_ID"].strip()
    c = ga_client()
    geo = coords()
    U = ["activeUsers", "sessions"]
    ranges = {}
    for key, days in RANGES.items():
        tot = run(c, prop, [], ["activeUsers", "newUsers", "sessions", "screenPageViews", "engagedSessions", "userEngagementDuration", "averageSessionDuration"], days)
        t = tot[0] if tot else {}
        nvr = {r["newVsReturning"]: r["activeUsers"] for r in run(c, prop, ["newVsReturning"], ["activeUsers"], days)}
        cities = run(c, prop, ["city", "region", "country", "countryId"], U, days, 300)
        for r in cities:
            g = geo.get((r["city"].lower(), r["countryId"]))
            if g: r["lat"], r["lon"] = round(g[0], 3), round(g[1], 3)
        countries = run(c, prop, ["country", "countryId"], U, days, 250)
        regions = run(c, prop, ["region", "country"], U, days, 300)
        src = run(c, prop, ["sessionSource", "sessionMedium", "sessionCampaignName"], U, days, 500)
        ch = defaultdict(lambda: {"activeUsers": 0, "sessions": 0})
        for r in src:
            k = channel(r["sessionSource"], r["sessionMedium"], r["sessionCampaignName"])
            r["channel"] = k; ch[k]["activeUsers"] += r["activeUsers"]; ch[k]["sessions"] += r["sessions"]
        dev = run(c, prop, ["deviceCategory"], U, days)
        br = run(c, prop, ["browser"], U, days, 50)
        os_ = run(c, prop, ["operatingSystem"], U, days, 50)
        evs = run(c, prop, ["eventName"], ["eventCount", "totalUsers"], days, 500)
        try:  # needs the "Visitor org" custom dimension; skip quietly until GA4 has it
            orgs = run(c, prop, ["customEvent:visitor_org"], ["totalUsers", "eventCount"], days, 300, event_filter("visitor_org"))
        except Exception as e:
            print("visitor_org not available yet:", str(e)[:200]); orgs = []
        orgs = [{"org": r["customEvent:visitor_org"], "users": r["totalUsers"], "isp": is_isp(r["customEvent:visitor_org"])}
                for r in orgs if r["customEvent:visitor_org"] not in ("(not set)", "")]
        ranges[key] = {
            "totals": t, "newVsReturning": nvr, "cities": cities, "countries": countries, "regions": regions,
            "sources": src, "channels": [{"channel": k, **v} for k, v in sorted(ch.items(), key=lambda x: -x[1]["activeUsers"])],
            "devices": dev, "browsers": br, "os": os_, "events": {r["eventName"]: {"count": r["eventCount"], "users": r["totalUsers"]} for r in evs},
            "orgs": orgs,
        }
    daily = run(c, prop, ["date", "newVsReturning"], ["activeUsers", "sessions", "screenPageViews"], 90, 1000)
    apps = run(c, prop, ["date", "sessionCampaignName", "sessionMedium"], U, 90, 2000)
    apps = [r for r in apps if r["sessionMedium"] == "job_app"]
    recent = run(c, prop, ["dateHour", "city", "region", "countryId", "sessionSource", "sessionMedium", "sessionCampaignName", "deviceCategory"], ["sessions", "userEngagementDuration"], 4, 200)
    return ranges, daily, apps, recent

# ---------- sample data (for testing) ----------
def sample():
    random.seed(7)
    today = dt.date.today()
    cities = [("San Diego","California","United States","US",32.716,-117.165,30),("La Jolla","California","United States","US",32.847,-117.274,12),
              ("Denver","Colorado","United States","US",39.739,-104.985,9),("Broomfield","Colorado","United States","US",39.920,-105.087,6),
              ("Salt Lake City","Utah","United States","US",40.761,-111.891,8),("Park City","Utah","United States","US",40.646,-111.498,5),
              ("Los Angeles","California","United States","US",34.052,-118.244,7),("Bozeman","Montana","United States","US",45.680,-111.039,3),
              ("New York","New York","United States","US",40.713,-74.006,4),("Seattle","Washington","United States","US",47.606,-122.332,2),
              ("Breckenridge","Colorado","United States","US",39.482,-106.038,3),("Vancouver","British Columbia","Canada","CA",49.283,-123.121,1),("London","England","United Kingdom","GB",51.507,-0.128,1)]
    srcs = [("linkedin","social","featured",28),("(direct)","(none)","(direct)",22),("google","organic","(organic)",9),("canva","redirect","old-portfolio",5),
            ("resume","pdf","resume",6),("email","signature","email-signature",4),("application","job_app","vail-resorts",4),("application","job_app","alterra-ikon",3),
            ("application","job_app","ucsd-extended-studies",2),("application","job_app","big-sky",1),("lnkd.in","referral","(referral)",3)]
    ranges = {}
    for key, days in RANGES.items():
        f = days / 30
        sc = lambda n: max(1, round(n * f * random.uniform(.8, 1.2))) if n * f >= .5 else 0
        cs = [{"city":a,"region":b,"country":c_,"countryId":d,"lat":la,"lon":lo,"activeUsers":sc(n),"sessions":sc(n*1.3)} for a,b,c_,d,la,lo,n in cities]
        cs = [x for x in cs if x["activeUsers"]]
        users = sum(x["activeUsers"] for x in cs)
        sr = [{"sessionSource":a,"sessionMedium":b,"sessionCampaignName":cc,"activeUsers":sc(n),"sessions":sc(n*1.3)} for a,b,cc,n in srcs]
        sr = [x for x in sr if x["activeUsers"]]
        ch = defaultdict(lambda: {"activeUsers":0,"sessions":0})
        for r in sr:
            k = channel(r["sessionSource"], r["sessionMedium"], r["sessionCampaignName"]); r["channel"]=k
            ch[k]["activeUsers"]+=r["activeUsers"]; ch[k]["sessions"]+=r["sessions"]
        cn = defaultdict(lambda: {"activeUsers":0,"sessions":0}); rg = defaultdict(lambda: {"activeUsers":0,"sessions":0})
        for x in cs:
            cn[(x["country"],x["countryId"])]["activeUsers"]+=x["activeUsers"]; cn[(x["country"],x["countryId"])]["sessions"]+=x["sessions"]
            rg[(x["region"],x["country"])]["activeUsers"]+=x["activeUsers"]; rg[(x["region"],x["country"])]["sessions"]+=x["sessions"]
        ev = {"page_view":(users*1.4,users),"user_engagement":(users*1.2,users),"scroll_25":(users*.8,users*.8),"scroll_50":(users*.62,users*.62),
              "scroll_75":(users*.44,users*.44),"scroll_100":(users*.29,users*.29),"work_email":(users*.5,users*.42),"work_social":(users*.33,users*.3),
              "work_print":(users*.18,users*.17),"work_web":(users*.2,users*.18),"work_brand":(users*.12,users*.11),"click_book_call":(users*.07,users*.06),
              "click_email":(users*.05,users*.05),"copy_email":(users*.03,users*.03),"click_linkedin":(users*.09,users*.08),"lightbox_open":(users*.6,users*.3),
              "reels_open":(users*.21,users*.2),"contact_form_submit":(users*.02,users*.02),"view_work":(users*.7,users*.7),"view_photos":(users*.45,users*.45),"view_contact":(users*.32,users*.32)}
        orgs = [("Comcast Cable Communications, LLC",9),("T-Mobile USA, Inc.",8),("Vail Resorts Inc",2),("University of California, San Diego",2),("Charter Communications Inc",5),("Alterra Mountain Company",1),("Akamai Technologies, Inc.",4)]
        ranges[key] = {
            "totals":{"activeUsers":users,"newUsers":round(users*.78),"sessions":round(users*1.3),"screenPageViews":round(users*1.45),"engagedSessions":round(users*.9),
                      "userEngagementDuration":round(users*96),"averageSessionDuration":104.0},
            "newVsReturning":{"new":round(users*.78),"returning":users-round(users*.78)},
            "cities":cs,"countries":[{"country":k[0],"countryId":k[1],**v} for k,v in cn.items()],"regions":[{"region":k[0],"country":k[1],**v} for k,v in rg.items()],
            "sources":sr,"channels":[{"channel":k,**v} for k,v in sorted(ch.items(), key=lambda x:-x[1]["activeUsers"])],
            "devices":[{"deviceCategory":"mobile","activeUsers":round(users*.58),"sessions":0},{"deviceCategory":"desktop","activeUsers":round(users*.39),"sessions":0},{"deviceCategory":"tablet","activeUsers":max(1,round(users*.03)),"sessions":0}],
            "browsers":[{"browser":b,"activeUsers":round(users*p),"sessions":0} for b,p in [("Safari",.46),("Chrome",.38),("Edge",.08),("Firefox",.04),("Samsung Internet",.02)]],
            "os":[{"operatingSystem":b,"activeUsers":round(users*p),"sessions":0} for b,p in [("iOS",.47),("Macintosh",.22),("Windows",.19),("Android",.11)]],
            "events":{k:{"count":round(a),"users":round(b)} for k,(a,b) in ev.items()},
            "orgs":[{"org":o,"users":sc(n),"isp":is_isp(o)} for o,n in orgs if sc(n)],
        }
    daily = []
    for i in range(90):
        d = today - dt.timedelta(days=89-i); base = 2 + (i/90)*5 + (6 if i in (70,71,84) else 0)
        n = max(0, round(random.gauss(base, 1.6))); r = max(0, round(random.gauss(base*.25, .8)))
        for k, v in (("new", n), ("returning", r)):
            if v: daily.append({"date":d.strftime("%Y%m%d"),"newVsReturning":k,"activeUsers":v,"sessions":round(v*1.25),"screenPageViews":round(v*1.4)})
    apps = []
    for camp, ds in (("vail-resorts",[2,2,5,11]),("alterra-ikon",[1,6,6]),("ucsd-extended-studies",[3,20]),("big-sky",[40])):
        for back in ds:
            apps.append({"date":(today-dt.timedelta(days=back)).strftime("%Y%m%d"),"sessionCampaignName":camp,"sessionMedium":"job_app","activeUsers":1,"sessions":1})
    recent = []
    for h, city, reg, cid, s, m, cp, dv in [(1,"Broomfield","Colorado","US","application","job_app","vail-resorts","desktop"),(3,"San Diego","California","US","linkedin","social","featured","mobile"),
                                            (5,"Denver","Colorado","US","(direct)","(none)","(direct)","mobile"),(9,"Salt Lake City","Utah","US","resume","pdf","resume","desktop"),
                                            (20,"La Jolla","California","US","google","organic","(organic)","mobile"),(27,"Park City","Utah","US","canva","redirect","old-portfolio","mobile")]:
        t = dt.datetime.now() - dt.timedelta(hours=h)
        recent.append({"dateHour":t.strftime("%Y%m%d%H"),"city":city,"region":reg,"countryId":cid,"sessionSource":s,"sessionMedium":m,"sessionCampaignName":cp,"deviceCategory":dv,"sessions":1,"userEngagementDuration":random.randint(20,300)})
    return ranges, daily, apps, recent

# ---------- encrypt ----------
def encrypt(obj, passphrase):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    salt, iv, it = os.urandom(16), os.urandom(12), 250000
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=it).derive(passphrase.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(obj, separators=(",", ":")).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "alg": "AES-GCM/PBKDF2-SHA256", "iter": it, "salt": b(salt), "iv": b(iv), "data": b(ct),
            "generated_at": obj["generated_at"]}

if __name__ == "__main__":
    is_sample = "--sample" in sys.argv
    ranges, daily, apps, recent = sample() if is_sample else pull()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    stats = {"generated_at": now, "sample": is_sample, "site": "justinbclose.com", "ranges": ranges, "daily": daily, "applications": apps, "recent": recent}
    key = os.environ.get("DASH_KEY") or ("sample" if is_sample else None)
    if not key: sys.exit("DASH_KEY secret is missing")
    with open(OUT, "w") as f: json.dump(encrypt(stats, key), f)
    if "--plain" in sys.argv:
        with open(OUT.replace(".enc", ""), "w") as f: json.dump(stats, f, indent=1)
    print("wrote", OUT, "at", now)
