<directive>
**[Module: Optimized Worklog Maintenance & Context Restoration]**

**1. Mandate, Purpose, & Session Initialization:**
In addition to your other primary directives and operational responsibilities, you MUST maintain a highly compact and machine-parsable project worklog. This log is to be stored in the file `.Q/worklog.md` (relative to the project root).

**Critically, at the commencement of any new work session, or when re-engaging with this project after any period of inactivity or context reset, your absolute first operational step MUST be to read and fully parse the entire content of the `.Q/worklog.md` file.** This is to ensure you are completely updated on the latest recorded state, decisions, pending actions, and critical context before proceeding with any new tasks or instructions.

The primary purpose of this log and your interaction with it is to facilitate your internal context management, enabling efficient task resumption by yourself or another LLM instance. The log is optimized for your parsing speed and data density; human readability is not a primary design concern. Consistent and accurate maintenance and utilization of this log are mandatory for operational continuity and effective long-term project engagement. Failure to adhere to this protocol will impede operational effectiveness.

**2. Update Triggers (When to Append to Log):**
You are to append a new, timestamped log entry to `.Q/worklog.md`:
    * **Post-Action:** Immediately after every significant coding action (e.g., code generation, modification, refactoring, bug fixing, critical configuration changes).
    * **Pre-Complex Task:** Before generating extensive code blocks or outlining detailed multi-step plans, log your current understanding and intended high-level approach.
    * **On Key Decisions:** When significant architectural, algorithmic, or library choices are finalized.
    * **On Roadblock/Query Identification:** When new challenges, critical issues, or open questions impacting progress are identified.
    * **At Interaction Boundaries:** Before anticipated long pauses, at the end of a defined work session, or when an interaction cycle concludes.

**3. Log Entry Structure (Ultra-Compact, Key-Based Format):**
Each new log entry MUST begin on a new line, be clearly separated from any previous entry by a horizontal rule (`---`), and strictly follow this key-value pair format. Each key must be on a new line, followed immediately by a colon (`:`), and then its highly condensed value. Adherence to these exact keys is crucial for your parsing efficiency:

    * `TS:` (Timestamp - ISO 8601 Compact: `YYYY-MM-DDTHH:MM:SSZ`)
    * `PRJ_ID:` (Optional Project Identifier - a brief, consistent ID if you are managing multiple distinct projects concurrently; omit if single project context)
    * `OBJ:` (Current high-level objective or task group - use keywords for maximum brevity, e.g., "AuthN_module_dev")
    * `LAST_ACT:` (Last significant completed action or milestone - extremely concise, e.g., "Impl: `user_login()` EP;Status:Pass_tests")
    * `FOCUS_TASK:` (Current specific, granular task being worked on - e.g., "Dev:pwd_reset_token_gen")
    * `MOD_FILES:` (Files actively modified or viewed for the current task - list essential paths, one per sub-line prefixed with `-`, e.g., `- /src/auth/tokens.py`)
    * `MOD_ENTITIES:` (Key Functions/Classes/Modules directly involved or changed - list names, one per sub-line prefixed with `-`, e.g., `- gen_secure_token()`)
    * `LOGIC_SUM:` (Brief keywords summarizing the core logic or approach for `FOCUS_TASK` - e.g., "CSRNG_uuid_v4_timed_db_store")
    * `DEC_CHG:` (Key Decisions made or significant Changes implemented since the last log entry - list concisely, one per sub-line prefixed with `-`, e.g., "- AlgoSwitch:SHA512_to_Argon2id;R:enhanced_sec")
    * `ISS_BLK_Q:` (Observed Issues, Roadblocks, or critical Open Questions needing resolution - list, one per sub-line prefixed with `-`, e.g., "- ERR:DB_conn_pool_timeout;Needs_cfg_rev")
    * `NEXT_ACT:` (Pending Actions and Immediate Next Steps - critical for resumption. List, one per sub-line prefixed with `-`. Use P1, P2, P3 to denote High, Medium, Low priority respectively, e.g., "- P1:Write_unit_tests_for_`gen_secure_token`")
    * `CTX_BRANCH:` (Current version control branch, if applicable - e.g., `ft/reset-pass-v2`)
    * `CTX_STATE:` (Critical contextual state variables or parameters not easily found in code but essential for resuming the current specific task - e.g., "TestUser: `dev_user_003`", "ActiveSessionToken: `abc...xyz`_preview")
    * `CTX_REFS:` (Critical new external URLs, documentation links, or references consulted/used - e.g., "CryptoLib_docs: [URL_to_specific_page]")
    * `CTX_ENV:` (Relevant environment specifics if they changed or are uniquely critical for the current task - e.g., "PyVer:3.11.5", "LibVer: `cryptography==42.0.5`")

**4. Content & Style Imperatives for Log Entries:**
    * **Extreme Compactness:** This is the absolute, overriding priority. Aggressively use abbreviations, established codes (like P1/P2/P3), symbols, and keywords. Eliminate all non-essential words, articles, and connecting phrases where meaning can be inferred by an LLM.
    * **Machine Parsability:** Strict adherence to the defined key-based format and consistent use of keys are vital for your own efficient parsing and context retrieval.
    * **Data Density:** Maximize the information conveyed per character. Think in terms of essential data points.
    * **Internal LLM Use Only:** This log is your operational memory extension. Do not add any formatting, verbose explanations, or elaborations intended for human readability.
    * **Essential Information Only:** Log only data that is critical for *your* ability to seamlessly resume the exact thread of work and understanding. Avoid duplicating information that is stable and easily discoverable from the current codebase, unless it is a very recent change or a specific point of active focus/debugging.
    * **No Code Snippets:** Do not include blocks of code. Refer to code entities by their fully qualified names and file paths where necessary.

**5. Initial Log Entry Protocol:**
    If the `.Q/worklog.md` file does not exist, you must create it. The very first entry in a newly created log must also conform to this structure, minimally logging the `TS:` (current timestamp), `OBJ:` (overall project goal or initial main task), and the first `NEXT_ACT:` you intend to perform.


<directive>
**Optimized Worklog Maintenance & Context Restoration**

**1. Mandate, Purpose & Session Start:**
Integrate this worklog protocol with all your duties.
* **Log File:** `.Q/worklog.md` (project root).
* **Session Start:** Your FIRST action in a new session or on project re-engagement MUST be to read and fully parse `.Q/worklog.md` for complete context.
* **Purpose:** Internal LLM context management for efficient task resumption. Optimized for YOUR parsing speed and data density; human readability is NOT a goal.
* **Adherence:** Mandatory for operational continuity.

**2. When to Append New Log Entries:**
Append a new, timestamped entry to `.Q/worklog.md` after:
* Significant coding actions (generation, modification, refactor, fix, critical config changes).
* Defining approach for complex tasks/code generation.
* Making key decisions (architecture, algorithms, libraries).
* Identifying new challenges, critical issues, or key questions.
* Interaction boundaries (before long pauses, end of session).

**3. Log Entry Structure (Ultra-Compact, Key-Based):**
Separate entries with `---`. Each entry uses strict `Key:Value` pairs (highly condensed value), one pair per line. Use ONLY these keys:

* `TS:` Timestamp (YYYY-MM-DDTHH:MM:SSZ)
* `PRJ_ID:` Project ID (optional, brief, if multi-project context)
* `OBJ:` Current objective (keywords, max brevity)
* `LAST_ACT:` Last significant action (extremely concise)
* `FOCUS_TASK:` Current specific task (concise)
* `MOD_FILES:` Modified/viewed files (list paths with `-` prefix if multiple)
* `MOD_ENTITIES:` Involved functions/classes/modules (list names with `-` prefix if multiple)
* `LOGIC_SUM:` Logic summary for `FOCUS_TASK` (keywords)
* `DEC_CHG:` Key decisions/significant changes (list concisely with `-` prefix if multiple)
* `ISS_BLK_Q:` Issues/Roadblocks/Open Questions (list with `-` prefix if multiple)
* `NEXT_ACT:` Pending/Next Actions (list with `-` prefix if multiple; use P1, P2, P3 for High, Medium, Low priority)
* `CTX_BRANCH:` Current Git branch (if applicable)
* `CTX_STATE:` Critical contextual state variables (not easily found in code, essential for resumption)
* `CTX_REFS:` Critical new external URLs or documentation links
* `CTX_ENV:` Relevant environment specifics (if changed or uniquely critical for current task)

**4. Content & Style Imperatives for Log Entries:**
* **Extreme Compactness:** HIGHEST PRIORITY. Aggressively use abbreviations, codes, symbols, keywords. Eliminate all non-essential characters/words.
* **Machine Parsability:** Strict adherence to keys and `Key:Value` format is VITAL for your parsing.
* **Data Density:** Maximize information per character.
* **Internal LLM Use Only:** This log is YOUR operational memory. DO NOT optimize for human readability.
* **Essential Info Only:** Log only data CRITICAL for YOUR seamless resumption. Avoid redundancy with stable, easily discoverable codebase state unless it's a recent change or active focus.
* **No Code Snippets:** Refer to code entities by name/file path.

**5. Initial Log Entry Protocol:**
If `.Q/worklog.md` does not exist, create it. The first entry MUST conform, minimally logging `TS:`, `OBJ:` (overall project goal or initial main task), and the first `NEXT_ACT:`.

</directive>
