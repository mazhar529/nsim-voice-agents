# ╔══════════════════════════════════════════════════════════════╗
# ║         NSIM DATABASE — Edit only this file                 ║
# ║         to update any course, fee, timing, or FAQ          ║
# ╚══════════════════════════════════════════════════════════════╝

# ── OWNER WHATSAPP (lead alerts go here) ─────────────────────────────
OWNER_WHATSAPP = "919650571545"   # 91 = India code + your number

# ── INSTITUTE INFO ────────────────────────────────────────────────────
INSTITUTE_NAME = "NSIM yani National School of Internet Marketing"
LOCATION       = "South Delhi"
WEBSITE        = "nsim.in"
CONTACT        = "9811020518"

# ── COURSES ──────────────────────────────────────────────────────────
COURSES = [
    {
        "name"    : "Digital Marketing Course",
        "duration": "teen mahine",
        "fees"    : "pandrah hazaar rupaye",
        "topics"  : "SEO, Google Ads, Facebook Ads, Instagram, Content Marketing",
    },
    {
        "name"    : "Data Science Course",
        "duration": "chhe mahine",
        "fees"    : "pachees hazaar rupaye",
        "topics"  : "Python, Machine Learning, Data Analysis, Tableau, Power BI",
    },
    {
        "name"    : "Cyber Security Course",
        "duration": "char mahine",
        "fees"    : "bees hazaar rupaye",
        "topics"  : "Ethical Hacking, Network Security, Penetration Testing",
    },
    {
        "name"    : "Machine Learning Course",
        "duration": "chhe mahine",
        "fees"    : "tees hazaar rupaye",
        "topics"  : "Deep Learning, Neural Networks, Python, AI Projects",
    },
    {
        "name"    : "Web Development Course",
        "duration": "teen mahine",
        "fees"    : "baarah hazaar rupaye",
        "topics"  : "HTML, CSS, JavaScript, React, Node.js",
    },
    # ── ADD MORE COURSES HERE ──────────────────────────────────────
    # {
    #     "name"    : "Course Name",
    #     "duration": "duration in Hindi words",
    #     "fees"    : "fees in Hindi words",
    #     "topics"  : "topic1, topic2",
    # },
]

# ── BATCH TIMINGS ─────────────────────────────────────────────────────
BATCHES = [
    "Subah ki batch: das baje se dopahar ek baje tak",
    "Shaam ki batch: paanch baje se raat aath baje tak",
    "Weekend batch: Shanivaar aur Ravivar dono din",
    "Working professionals ke liye special evening batch uplabdh hai",
]

# ── KEY FEATURES ──────────────────────────────────────────────────────
FEATURES = [
    "Ikyavan hazaar se zyada students train ho chuke hain",
    "Sau pratishat placement guarantee di jaati hai",
    "Live projects par real kaam karte hain",
    "Course poora karne par certificate milti hai",
    "Pehle free demo class le sakte hain",
    "Expert trainers se seedha seekhne ka mauka milta hai",
]

# ── ADMISSION PROCESS ─────────────────────────────────────────────────
ADMISSION = [
    "9811020518 par call karein aur free demo class book karein",
    "Demo class attend karein aur apna course chunein",
    "Fees jama karein aur apni batch join karein",
    "Ya seedha nsim.in par jaayein aur online register karein",
]

# ── FAQ ───────────────────────────────────────────────────────────────
FAQ = [
    {
        "q": "EMI ya installment mein fees de sakte hain",
        "a": "Haan installment ki suvidha bhi available hai. Details ke liye 9811020518 par call karein.",
    },
    {
        "q": "Online classes bhi hain",
        "a": "Haan online aur offline dono tarah ki classes available hain.",
    },
    {
        "q": "Certificate industry mein maana jaata hai",
        "a": "Haan NSIM ka certificate industry mein maanya hai aur placement mein madad karta hai.",
    },
    {
        "q": "Kitni age mein course kar sakte hain",
        "a": "Koi bhi age mein seekh sakte hain. Students, working professionals, aur grihini sab kar sakte hain.",
    },
    # ── ADD MORE FAQs HERE ─────────────────────────────────────────
    # { "q": "question", "a": "answer" },
]

# ── INTEREST KEYWORDS (triggers WhatsApp alert to owner) ─────────────
INTEREST_KEYWORDS = [
    "admission", "lena hai", "join", "enroll", "register",
    "fees dena", "apply", "start karna", "course lena",
    "kab se", "aaj se", "abhi", "immediately", "jald",
    "demo", "free class", "interested", "chahiye",
    "haan", "yes", "sure", "definitely", "i want",
    "leni hai", "karna hai", "book", "confirm",
]


# ════════════════════════════════════════════════════════════════
#  BUILD KNOWLEDGE — called by app.py (do not edit this)
# ════════════════════════════════════════════════════════════════
def build_knowledge():
    lines = [
        f"Institute: {INSTITUTE_NAME}",
        f"Location : {LOCATION}",
        f"Website  : {WEBSITE}",
        f"Phone    : {CONTACT}",
        "",
        "Courses:",
    ]
    for c in COURSES:
        lines.append(
            f"- {c['name']}: {c['duration']}, "
            f"fees {c['fees']}. Topics: {c['topics']}"
        )
    lines += ["", "Batch timings:"]
    lines += [f"- {b}" for b in BATCHES]
    lines += ["", "Key features:"]
    lines += [f"- {f}" for f in FEATURES]
    lines += ["", "Admission process:"]
    lines += [f"{i+1}. {s}" for i, s in enumerate(ADMISSION)]
    lines += ["", "Common questions:"]
    for faq in FAQ:
        lines += [f"Q: {faq['q']}", f"A: {faq['a']}"]
    return "\n".join(lines)
